// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
mod sidecar;

use tauri::Manager;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn rpc(method: String, params: serde_json::Value) -> Result<serde_json::Value, String> {
    sidecar::call(&method, params).await.map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let resource_dir = app.path().resource_dir().ok();
            // Dev mode: sidecar lives at <repo>/sidecar relative to CARGO_MANIFEST_DIR.
            let dev_sidecar_cwd = {
                let mut p = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"));
                p.pop(); // strip "src-tauri"
                p.push("sidecar"); // join "sidecar"
                p
            };
            let _ = resource_dir;

            let cwd = dev_sidecar_cwd.to_string_lossy().into_owned();
            eprintln!("[purgeless] spawning sidecar with cwd={cwd}");
            tauri::async_runtime::spawn(async move {
                if let Err(e) = sidecar::init(&cwd).await {
                    eprintln!("sidecar init failed: {e}");
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet, rpc])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
