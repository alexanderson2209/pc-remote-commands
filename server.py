import subprocess
from fastapi import FastAPI, HTTPException, Request
import yaml
import os
import threading
import sys
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
from plyer import notification

app = FastAPI()


def get_base_path():
    if getattr(sys, "frozen", False):
        # running as .exe
        return os.path.dirname(sys.executable)
    else:
        # running as script
        return os.path.dirname(os.path.abspath(__file__))


# Load config initially
def load_config():
    base_path = get_base_path()
    config_path = os.path.join(base_path, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()
auth_key = config["server"]["auth_key"]
allowed_commands = config["commands"]


@app.post("/run/{command_name}")
async def run_command(command_name: str, request: Request):
    global config, allowed_commands, auth_key  # allow updating these

    # Check auth key in headers
    client_key = request.headers.get("X-Auth-Key")
    if client_key != auth_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Try first from memory
    cmd_config = allowed_commands.get(command_name)

    if not cmd_config:
        # Reload config and try again
        config = load_config()
        allowed_commands = config["commands"]
        auth_key = config["server"]["auth_key"]  # update in case auth_key changed too
        cmd_config = allowed_commands.get(command_name)

    if not cmd_config:
        raise HTTPException(
            status_code=404, detail="Command not found even after reloading config."
        )

    cmd = cmd_config["command"]

    try:
        # Run the command
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


@app.get("/")
def root():
    return {"message": "Command server is running."}


def create_image():
    image = Image.new("RGB", (64, 64), color="white")
    d = ImageDraw.Draw(image)
    d.rectangle([16, 16, 48, 48], fill="black")
    return image


icon = None  # placeholder
server_thread = None


def open_config_folder():
    print("Opening config folder...")
    os.startfile(get_base_path())


def stop_app(icon_obj, item):
    print("Exiting app...")
    icon_obj.stop()
    os._exit(0)  # force exit whole app, including FastAPI


def run_tray():
    global icon
    menu = Menu(
        MenuItem("Open Config Folder", lambda icon, item: open_config_folder()),
        MenuItem("Exit App", stop_app),
    )
    icon = Icon("MyServer", create_image(), "My Server", menu)
    icon.run()


# === Run FastAPI in background ===
def run_server():
    import uvicorn

    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        log_level="critical",  # set log level to critical
        # Disable access logging. block console output
        access_log=False,
        log_config=None,
    )


def notify_startup():
    notification.notify(
        title="PC Remote",
        message="Server Started!",
        app_name="PC Remote",
        timeout=5,
    )


if __name__ == "__main__":
    try:
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        notify_startup()
        run_tray()  # this blocks until user exits tray
    except Exception as e:
        with open("server_error.log", "a", encoding="utf-8") as f:
            f.write(str(e) + "\n")
        raise

sys.stdout = open(
    os.path.join(get_base_path(), "logs.txt"), "a", encoding="utf-8"
)  # divert stdout to logs.txt file
sys.stderr = open(os.path.join(get_base_path(), "errors.txt"), "a", encoding="utf-8")
