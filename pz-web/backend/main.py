import os
import re
import glob
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
from typing import List, Dict, Optional
import docker
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Project Zomboid Server Dashboard API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use parent directory of this script's location for more robust pathing
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, '..', '..'))

PZ_CONFIG_PATH = os.getenv("PZ_CONFIG_PATH", os.path.join(PROJECT_ROOT, "pz-config"))
PZ_DATA_PATH = os.getenv("PZ_DATA_PATH", os.path.join(PROJECT_ROOT, "pz-data"))
SERVER_NAME = os.getenv("SERVER_NAME", "b42coop")
# Default docker-compose naming convention is project_service_1
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "project-zomboid-server-pzserver-1")

# --- Pydantic Models ---
class ModItem(BaseModel):
    id: str
    workshopId: str

# --- Helper Functions ---

def get_docker_client():
    try:
        return docker.from_env()
    except docker.errors.DockerException:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Docker is not available or not configured correctly.")

def get_pz_container():
    client = get_docker_client()
    try:
        # Using container name from compose is more reliable
        return client.containers.get(CONTAINER_NAME)
    except docker.errors.NotFound:
        # Fallback for different naming schemes
        try:
            containers = client.containers.list(filters={"name": "pzserver"})
            if not containers:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Container '{CONTAINER_NAME}' or any container with name 'pzserver' not found.")
            return containers[0]
        except docker.errors.NotFound:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Container '{CONTAINER_NAME}' or any container with name 'pzserver' not found.")


def get_latest_log_file(pattern: str) -> Optional[str]:
    log_dirs = sorted(glob.glob(os.path.join(PZ_CONFIG_PATH, "Logs", "logs_*")), reverse=True)
    for log_dir in log_dirs:
        files = sorted(glob.glob(os.path.join(log_dir, f"*{pattern}*")), reverse=True)
        if files:
            return files[0]
    root_logs = sorted(glob.glob(os.path.join(PZ_CONFIG_PATH, "Logs", f"*{pattern}*")), reverse=True)
    if root_logs:
        return root_logs[0]
    return None

def parse_ini_file_to_dict(file_path: str) -> Dict[str, str]:
    results = {}
    if not os.path.exists(file_path):
        return results
    with open(file_path, "r", errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                results[key.strip()] = value.strip()
    return results

async def update_ini_file_content(file_path: str, new_content: str):
    async with aiofiles.open(file_path, "w", errors='ignore') as f:
        await f.write(new_content)

async def modify_ini_list(ini_path: str, key: str, item: str, action: str = 'add'):
    async with aiofiles.open(ini_path, "r", errors='ignore') as f:
        lines = await f.readlines()

    new_lines = []
    key_found = False
    for line in lines:
        if line.strip().lower().startswith(f"{key.lower()}="):
            key_found = True
            current_value = line.split("=", 1)[1].strip()
            items = [i.strip() for i in current_value.split(";") if i.strip()]
            
            if action == 'add':
                if item not in items:
                    items.append(item)
            elif action == 'remove':
                if item in items:
                    items.remove(item)

            new_lines.append(f"{key}={';'.join(items)}\n")
        else:
            new_lines.append(line)

    if not key_found and action == 'add':
         new_lines.append(f"\n{key}={item}\n")

    await update_ini_file_content(ini_path, "".join(new_lines))

# --- API Endpoints ---

@app.get("/api/status")
async def get_status():
    ini_path = os.path.join(PZ_CONFIG_PATH, "Server", f"{SERVER_NAME}.ini")
    ini_data = parse_ini_file_to_dict(ini_path)
    
    user_log = get_latest_log_file("user.txt")
    online_players = []
    if user_log:
        try:
            async with aiofiles.open(user_log, mode='r', errors='ignore') as f:
                lines = await f.readlines()
                player_states = {} # username -> bool
                for line in lines:
                    connect_match = re.search(r'"(.+)" fully connected', line)
                    if connect_match:
                        player_states[connect_match.group(1)] = True
                    
                    disconnect_match = re.search(r'"(.+)" disconnected player', line)
                    if disconnect_match:
                        player_states[disconnect_match.group(1)] = False
                
                online_players = [name for name, online in player_states.items() if online]
        except FileNotFoundError:
            pass # It's okay if log file is not found yet

    container_status = "unknown"
    try:
        container = get_pz_container()
        container_status = container.status
    except HTTPException:
        container_status = "not_found" # Docker running, but container is not there
    except Exception:
        container_status = "docker_error" # Docker daemon not running or other issue

    mods_value = ini_data.get("Mods", "")
    mods_count = len(mods_value.split(";")) if mods_value else 0

    return {
        "serverName": ini_data.get("PublicName", "Project Zomboid Server"),
        "maxPlayers": ini_data.get("MaxPlayers", "0"),
        "onlinePlayers": len(online_players),
        "playerList": online_players,
        "status": container_status,
        "version": "Build 42 Unstable",
        "modsCount": mods_count
    }

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    log_file = get_latest_log_file("DebugLog-server.txt")
    if not log_file:
        return {"logs": ["No log file found."]}
    
    try:
        async with aiofiles.open(log_file, mode='r', errors='ignore') as f:
            content = await f.readlines()
            return {"logs": content[-lines:]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}

@app.get("/api/settings")
async def get_settings():
    ini_path = os.path.join(PZ_CONFIG_PATH, "Server", f"{SERVER_NAME}.ini")
    sandbox_path = os.path.join(PZ_CONFIG_PATH, "Server", f"{SERVER_NAME}_SandboxVars.lua")
    
    settings = {"ini": "", "sandbox": ""}
    
    try:
        if os.path.exists(ini_path):
            async with aiofiles.open(ini_path, mode='r') as f:
                settings["ini"] = await f.read()
        if os.path.exists(sandbox_path):
            async with aiofiles.open(sandbox_path, mode='r') as f:
                settings["sandbox"] = await f.read()
    except Exception:
        pass # Ignore read errors for now
            
    return settings

@app.get("/api/mods", response_model=List[ModItem])
async def get_mods():
    ini_path = os.path.join(PZ_CONFIG_PATH, "Server", f"{SERVER_NAME}.ini")
    ini_data = parse_ini_file_to_dict(ini_path)
    
    mods = [m.strip() for m in ini_data.get("Mods", "").split(";") if m.strip()]
    workshop_ids = [w.strip() for w in ini_data.get("WorkshopItems", "").split(";") if w.strip()]
    
    # Pair them up, assuming they are in order. Pad if mismatched.
    max_len = max(len(mods), len(workshop_ids))
    mod_list = []
    for i in range(max_len):
        mod_list.append({
            "id": mods[i] if i < len(mods) else "N/A",
            "workshopId": workshop_ids[i] if i < len(workshop_ids) else "N/A"
        })
    return mod_list

# --- Server Control Endpoints ---
@app.post("/api/server/action/{action}", status_code=status.HTTP_200_OK)
async def server_action(action: str):
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action.")
    
    message = ""
    try:
        if action == "start":
            # Start is a bit different, it might not exist.
            # We can use `docker compose up -d` for this.
            process = await asyncio.create_subprocess_shell(
                f"docker compose up -d {CONTAINER_NAME.split('-')[1]}", # Assumes service name is middle part
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise Exception(stderr.decode())
            message = "Server start command issued successfully."
        else:
            container = get_pz_container()
            if action == "stop":
                container.stop(timeout=60)
                message = "Server stop command issued successfully."
            elif action == "restart":
                container.restart(timeout=60)
                message = "Server restart command issued successfully."

        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to {action} server: {str(e)}")


# --- Mod Management Endpoints ---
@app.post("/api/mods", status_code=status.HTTP_200_OK)
async def add_mod(mod: ModItem):
    ini_path = os.path.join(PZ_CONFIG_PATH, "Server", f"{SERVER_NAME}.ini")
    if not os.path.exists(ini_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=".ini file not found.")

    try:
        await modify_ini_list(ini_path, "WorkshopItems", mod.workshopId, action='add')
        await modify_ini_list(ini_path, "Mods", mod.id, action='add')
        
        # Non-blocking restart
        asyncio.create_task(server_action('restart'))

        return {"message": f"Mod '{mod.id}' added. Server is restarting."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add mod: {str(e)}")


@app.delete("/api/mods", status_code=status.HTTP_200_OK, response_model=Dict[str, str])
async def remove_mod(mod: ModItem):
    ini_path = os.path.join(PZ_CONFIG_PATH, "Server", f"{SERVER_NAME}.ini")
    if not os.path.exists(ini_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=".ini file not found.")

    try:
        await modify_ini_list(ini_path, "WorkshopItems", mod.workshopId, action='remove')
        await modify_ini_list(ini_path, "Mods", mod.id, action='remove')
        
        # Non-blocking restart
        asyncio.create_task(server_action('restart'))

        return {"message": f"Mod '{mod.id}' removed. Server is restarting."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to remove mod: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Make sure to run with reload for development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
