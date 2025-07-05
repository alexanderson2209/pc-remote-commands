import os
import sys
import yaml
import threading
import subprocess
from fastapi import FastAPI, HTTPException, Request
import uvicorn
from pystray import Icon, MenuItem, Menu
from PIL import Image
from plyer import notification
from tv_remote import TVController

app = FastAPI()

# Global vars initialized later
config = None
auth_key = None
allowed_commands = None
tv = None


def is_running_as_exe():
    """Detect if running from PyInstaller bundled executable"""
    return getattr(sys, "frozen", False)


def get_base_path():
    """Return base directory (current script or executable location)"""
    return os.path.dirname(
        sys.executable if is_running_as_exe() else os.path.abspath(__file__)
    )


def get_icon_folder():
    """Folder containing static assets like tray icons"""
    return (
        os.path.join(sys._MEIPASS, "static")
        if is_running_as_exe()
        else os.path.join(get_base_path(), "static")
    )


def load_server_config():
    """Load YAML config from disk"""
    config_path = os.path.join(get_base_path(), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def initialize():
    """Initialize global state from config"""
    global config, auth_key, allowed_commands, tv
    config = load_server_config()
    auth_key = config["server"]["auth_key"]
    allowed_commands = config["commands"]

    tv = TVController(
        config["server"]["tv_ip"],
        config["server"]["pc_tv_profile"],
        config["server"]["pc_desk_profile"],
        config["server"]["pc_tv_input_label"],
    )


@app.get("/")
def root():
    return {"message": "Command server is running."}


@app.post("/run/{command_name}")
async def run_command(command_name: str, request: Request):
    """Endpoint to execute allowed commands"""
    global config, auth_key, allowed_commands

    # Validate auth key
    client_key = request.headers.get("X-Auth-Key")
    if client_key != auth_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Find command config
    cmd_config = allowed_commands.get(command_name)

    # If missing, reload config and retry
    if not cmd_config:
        initialize()
        cmd_config = allowed_commands.get(command_name)
        if not cmd_config:
            raise HTTPException(
                status_code=404, detail="Command not found even after reloading config."
            )

    # Handle special TV commands
    if command_name == "switch_pc_to_tv":
        tv.switch_pc_to_tv()
        return {"status": "success", "message": "Switched PC to TV"}
    elif command_name == "switch_pc_back":
        tv.switch_pc_back()
        return {"status": "success", "message": "Switched PC back"}
    else:
        return run_shell_command(cmd_config["command"], command_name)


def run_shell_command(cmd: str, command_name: str):
    """Run shell command and capture output"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        return {
            "status": "success",
            "message": f"Executed {command_name}",
            "output": result.stdout.strip(),
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"Command failed: {e.stderr.strip()}"
        ) from e


# === System tray integration ===
def open_config_folder():
    """Open config folder in file explorer"""
    os.startfile(get_base_path())


def stop_app(icon_obj, _):
    """Stop tray icon and exit entire app"""
    icon_obj.stop()
    os._exit(0)  # immediate exit


def run_tray():
    """Start system tray icon"""
    menu = Menu(
        MenuItem("Open Config Folder", lambda icon, _: open_config_folder()),
        MenuItem("Exit App", stop_app),
    )
    icon = Icon(
        "PC Remote",
        Image.open(os.path.join(get_icon_folder(), "icon.ico")),
        "PC Remote",
        menu,
    )
    icon.run()


# === FastAPI server in background ===
def run_server():
    """Start FastAPI server with Uvicorn"""
    if is_running_as_exe():
        # Redirect logs to file when packaged
        sys.stdout = open(
            os.path.join(get_base_path(), "logs.txt"), "a", encoding="utf-8"
        )
        sys.stderr = open(
            os.path.join(get_base_path(), "errors.txt"), "a", encoding="utf-8"
        )

    uvicorn.run(app, host=config["server"]["host"], port=config["server"]["port"])


def notify_startup():
    """Show system notification on startup"""
    notification.notify(
        title="PC Remote",
        message="Server Started!",
        app_name="PC Remote",
        timeout=5,
    )


if __name__ == "__main__":
    try:
        initialize()
        threading.Thread(target=run_server, daemon=True).start()
        notify_startup()
        run_tray()
    except Exception as e:
        with open("server_error.log", "a", encoding="utf-8") as f:
            f.write(f"{e}\n")
        raise
