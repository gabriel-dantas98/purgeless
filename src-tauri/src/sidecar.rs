//! Manages the python sidecar subprocess and a request/response queue.
use anyhow::{anyhow, Result};
use once_cell::sync::OnceCell;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::Mutex;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{ChildStdin, Command};
use tokio::sync::oneshot;
use uuid::Uuid;

pub struct Sidecar {
    stdin: tokio::sync::Mutex<ChildStdin>,
    pending: Mutex<HashMap<String, oneshot::Sender<Value>>>,
}

static SIDECAR: OnceCell<Sidecar> = OnceCell::new();

pub fn instance() -> &'static Sidecar {
    SIDECAR.get().expect("sidecar not initialized")
}

/// Spawn the Python sidecar.
///
/// `cwd` is the path to the sidecar directory (e.g. `<repo>/sidecar`).
/// We launch via `uv run python -m purgeless_sidecar.server` so the venv resolves automatically.
pub async fn init(cwd: &str) -> Result<()> {
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
            match serde_json::from_str::<Value>(&line) {
                Ok(msg) => {
                    if let Some(id) = msg.get("id").and_then(|v| v.as_str()).map(String::from)
                    {
                        let tx_opt = instance().pending.lock().unwrap().remove(&id);
                        if let Some(tx) = tx_opt {
                            let _ = tx.send(msg);
                        }
                    }
                }
                Err(e) => eprintln!("[sidecar] non-JSON line: {line:?} ({e})"),
            }
        }
        eprintln!("[sidecar] stdout closed");
    });

    Ok(())
}

pub async fn call(method: &str, params: Value) -> Result<Value> {
    let id = Uuid::new_v4().to_string();
    let req = json!({ "jsonrpc": "2.0", "id": id, "method": method, "params": params });
    let line = format!("{}\n", serde_json::to_string(&req)?);

    let (tx, rx) = oneshot::channel();
    instance().pending.lock().unwrap().insert(id.clone(), tx);

    {
        let mut stdin = instance().stdin.lock().await;
        stdin.write_all(line.as_bytes()).await?;
        stdin.flush().await?;
    }

    let resp = rx.await?;
    if let Some(err) = resp.get("error") {
        return Err(anyhow!("rpc error: {}", err));
    }
    resp.get("result").cloned().ok_or_else(|| anyhow!("no result"))
}
