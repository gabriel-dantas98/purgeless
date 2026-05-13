//! Manages the python sidecar subprocess and a request/response queue.
use anyhow::{anyhow, Result};
use once_cell::sync::OnceCell;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::Mutex;
use std::time::Instant;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tauri::{AppHandle, Emitter};
use tokio::process::{ChildStdin, Command};
use tokio::sync::oneshot;
use uuid::Uuid;

pub struct Sidecar {
    stdin: tokio::sync::Mutex<ChildStdin>,
    pending: Mutex<HashMap<String, oneshot::Sender<Value>>>,
    app: AppHandle,
}

static SIDECAR: OnceCell<Sidecar> = OnceCell::new();

pub fn instance() -> &'static Sidecar {
    SIDECAR.get().expect("sidecar not initialized")
}

/// Spawn the Python sidecar.
///
/// `cwd` is the path to the sidecar directory (e.g. `<repo>/sidecar`).
/// We launch via `uv run python -m purgeless_sidecar.server` so the venv resolves automatically.
pub async fn init(cwd: &str, app: AppHandle) -> Result<()> {
    let mut child = Command::new("uv")
        .arg("run")
        .arg("python")
        .arg("-u") // unbuffered stdout
        .arg("-m")
        .arg("purgeless_sidecar.server")
        .current_dir(cwd)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::inherit())
        .kill_on_drop(true)
        .spawn()?;
    let stdin = child.stdin.take().ok_or_else(|| anyhow!("no stdin"))?;
    let stdout = child.stdout.take().ok_or_else(|| anyhow!("no stdout"))?;

    let sidecar = Sidecar {
        stdin: tokio::sync::Mutex::new(stdin),
        pending: Mutex::new(HashMap::new()),
        app: app.clone(),
    };
    SIDECAR
        .set(sidecar)
        .map_err(|_| anyhow!("sidecar already initialized"))?;

    // Detach the child so it isn't dropped (we don't need to await its exit here).
    // kill_on_drop ensures cleanup when the Tauri process exits.
    std::mem::forget(child);

    // Reader task — read responses line by line, dispatch to pending oneshots.
    tokio::spawn(async move {
        let mut reader = BufReader::new(stdout).lines();
        while let Ok(Some(line)) = reader.next_line().await {
            let msg = match serde_json::from_str::<Value>(&line) {
                Ok(m) => m,
                Err(e) => {
                    eprintln!("[sidecar] non-JSON line: {line:?} ({e})");
                    continue;
                }
            };
            // Notification: has "method", no "id"
            if msg.get("method").is_some() && msg.get("id").is_none() {
                let method = msg
                    .get("method")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string();
                let params = msg.get("params").cloned().unwrap_or(Value::Null);
                let _ = instance().app.emit(&format!("sidecar:{}", method), params);
                continue;
            }
            // Response: has "id"
            if let Some(id) = msg.get("id").and_then(|v| v.as_str()).map(String::from) {
                let tx_opt = instance().pending.lock().unwrap().remove(&id);
                if let Some(tx) = tx_opt {
                    let _ = tx.send(msg);
                }
            }
        }
        eprintln!("[sidecar] stdout closed");
    });

    Ok(())
}

pub async fn call(method: &str, params: Value) -> Result<Value> {
    let started = Instant::now();
    let sidecar = SIDECAR
        .get()
        .ok_or_else(|| anyhow!("sidecar not initialized"))?;
    let id = Uuid::new_v4().to_string();
    eprintln!("[purgeless] rpc.start id={id} method={method}");
    let req = json!({ "jsonrpc": "2.0", "id": id, "method": method, "params": params });
    let line = format!("{}\n", serde_json::to_string(&req)?);

    let (tx, rx) = oneshot::channel();
    sidecar.pending.lock().unwrap().insert(id.clone(), tx);

    {
        let write_result = async {
            let mut stdin = sidecar.stdin.lock().await;
            stdin.write_all(line.as_bytes()).await?;
            stdin.flush().await
        }
        .await;

        if let Err(err) = write_result {
            sidecar.pending.lock().unwrap().remove(&id);
            eprintln!(
                "[purgeless] rpc.write_error id={id} method={method} elapsed_ms={} error={err}",
                started.elapsed().as_millis()
            );
            return Err(err.into());
        }
    }

    let resp = rx.await?;
    if let Some(err) = resp.get("error") {
        let formatted = format_rpc_error(method, err);
        eprintln!(
            "[purgeless] rpc.error id={id} method={method} elapsed_ms={} error={formatted}",
            started.elapsed().as_millis()
        );
        return Err(anyhow!(formatted));
    }
    eprintln!(
        "[purgeless] rpc.ok id={id} method={method} elapsed_ms={}",
        started.elapsed().as_millis()
    );
    resp.get("result").cloned().ok_or_else(|| anyhow!("no result"))
}

fn format_rpc_error(method: &str, err: &Value) -> String {
    let code = err.get("code").and_then(Value::as_i64).unwrap_or(-32000);
    let message = err
        .get("message")
        .and_then(Value::as_str)
        .unwrap_or("unknown sidecar error");
    let data = err.get("data");
    let exception_type = data
        .and_then(|data| data.get("exception_type"))
        .and_then(Value::as_str);
    let elapsed_ms = data
        .and_then(|data| data.get("elapsed_ms"))
        .and_then(Value::as_i64);

    let mut formatted = format!("sidecar {method} failed [{code}]: {message}");
    if let Some(exception_type) = exception_type {
        formatted.push_str(&format!(" ({exception_type})"));
    }
    if let Some(elapsed_ms) = elapsed_ms {
        formatted.push_str(&format!(" after {elapsed_ms}ms"));
    }
    formatted
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn call_before_init_returns_error() {
        let err = call("ping", json!({})).await.unwrap_err();

        assert!(err.to_string().contains("sidecar not initialized"));
    }

    #[test]
    fn format_rpc_error_includes_context() {
        let err = json!({
            "code": -32000,
            "message": "load_mesh failed: KeyError: 'path'",
            "data": {
                "exception_type": "KeyError",
                "elapsed_ms": 12
            }
        });

        let formatted = format_rpc_error("load_mesh", &err);

        assert!(formatted.contains("sidecar load_mesh failed [-32000]"));
        assert!(formatted.contains("KeyError"));
        assert!(formatted.contains("12ms"));
    }
}
