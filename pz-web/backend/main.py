import os
import re
import glob
import docker
import asyncio
import aiofiles
import time
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from pydantic import BaseModel

app = FastAPI(title="Project Zomboid Server Dashboard API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from Environment Variables (set in docker-compose)
PZ_CONFIG_PATH = os.getenv("PZ_CONFIG_PATH", "/home/steam/Zomboid")
PZ_DATA_PATH = os.getenv("PZ_DATA_PATH", "/home/steam/pzserver")
SERVER_NAME = os.getenv("SERVER_NAME", "b42coop")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "pz-b42-server")

# --- Pydantic Models ---
class ModItem(BaseModel):
    id: str
    workshopId: str

# --- Helper Functions ---

def get_docker_client():
    try:
        return docker.from_env()
    except Exception as e:
        print(f"Docker Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Docker is not available.")

def get_pz_container():
    client = get_docker_client()
    try:
        return client.containers.get(CONTAINER_NAME)
    except docker.errors.NotFound:
        containers = client.containers.list(filters={"name": "pz-b42-server"})
        if containers:
            return containers[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Container '{CONTAINER_NAME}' not found.")

def get_latest_log_file(pattern: str) -> Optional[str]:
    log_root = os.path.join(PZ_CONFIG_PATH, "Logs")
    if not os.path.exists(log_root):
        return None
    log_dirs = sorted(glob.glob(os.path.join(log_root, "logs_*")), reverse=True)
    for log_dir in log_dirs:
        files = sorted(glob.glob(os.path.join(log_dir, f"*{pattern}*")), reverse=True)
        if files:
            return files[0]
    root_logs = sorted(glob.glob(os.path.join(log_root, f"*{pattern}*")), reverse=True)
    if root_logs:
        return root_logs[0]
    return None

def parse_ini_file_to_dict(file_path: str) -> Dict[str, str]:
    results = {}
    if not os.path.exists(file_path):
        return results
    try:
        with open(file_path, "r", errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        results[parts[0].strip()] = parts[1].strip()
    except Exception:
        pass
    return results

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
                player_states = {} 
                for line in lines:
                    connect_match = re.search(r'"(.+)" fully connected', line)
                    if connect_match:
                        player_states[connect_match.group(1)] = True
                    disconnect_match = re.search(r'"(.+)" disconnected player', line)
                    if disconnect_match:
                        player_states[disconnect_match.group(1)] = False
                online_players = [name for name, online in player_states.items() if online]
        except Exception:
            pass
    container_status = "offline"
    try:
        container = get_pz_container()
        container_status = container.status
    except Exception:
        container_status = "not_found"
    mods_value = ini_data.get("Mods", "")
    mods_count = len([m for m in mods_value.split(";") if m.strip()]) if mods_value else 0
    return {
        "serverName": ini_data.get("PublicName", "Project Zomboid Server"),
        "maxPlayers": ini_data.get("MaxPlayers", "32"),
        "onlinePlayers": len(online_players),
        "playerList": online_players,
        "status": container_status,
        "version": "Build 42 Unstable",
        "modsCount": mods_count
    }

@app.get("/api/monitoring")
async def get_monitoring():
    try:
        container = get_pz_container()
        stats = container.stats(stream=False)
        
        # CPU Calculation
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        cpu_percent = 0.0
        if system_delta > 0.0:
            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [1])) * 100.0

        # Memory Calculation
        mem_usage = stats['memory_stats']['usage'] / (1024 * 1024) 
        mem_limit = stats['memory_stats']['limit'] / (1024 * 1024) 
        mem_percent = (stats['memory_stats']['usage'] / stats['memory_stats']['limit']) * 100.0

        # Estimate TPS (Project Zomboid target is 20 TPS)
        # We simulate it based on CPU load. If CPU is extremely high, TPS might drop.
        # In Build 42, TPS is usually stable unless the main thread is choked.
        tps = 20.0
        if cpu_percent > 90.0:
            tps = max(5.0, 20.0 - ((cpu_percent - 90.0) / 2.0))

        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_usage_mib": round(mem_usage, 2),
            "memory_limit_mib": round(mem_limit, 2),
            "memory_percent": round(mem_percent, 2),
            "tps": round(tps, 1),
            "container_name": CONTAINER_NAME
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring Error: {str(e)}")

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    log_file = get_latest_log_file("DebugLog-server.txt") or get_latest_log_file("DebugLog.txt")
    if not log_file:
        return {"logs": ["No log file found."]}
    try:
        async with aiofiles.open(log_file, mode='r', errors='ignore') as f:
            content = await f.readlines()
            return {"logs": [line.strip() for line in content[-lines:]]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}

@app.post("/api/server/action/{action}")
async def server_action(action: str):
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid action.")
    try:
        container = get_pz_container()
        if action == "stop": container.stop(timeout=30)
        elif action == "restart": container.restart(timeout=30)
        elif action == "start": container.start()
        return {"message": f"Server {action} command issued."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
