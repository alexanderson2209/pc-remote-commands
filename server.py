import subprocess
from fastapi import FastAPI, HTTPException, Request
import yaml
import os
import sys

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


if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host=config["server"]["host"], port=config["server"]["port"])
    except Exception as e:
        with open("server_error.log", "a", encoding="utf-8") as f:
            f.write(str(e) + "\n")
        raise
