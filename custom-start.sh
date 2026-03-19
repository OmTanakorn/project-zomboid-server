#!/bin/bash
set -e # หยุดสคริปต์ทันทีหากมีคำสั่งล้มเหลว

PZ_JSON="/home/steam/pzserver/ProjectZomboid64.json"

echo "--- Starting SteamCMD Update ---"
# แยกขั้นตอนเพื่อให้ SteamCMD จัดการสถานะได้ดีขึ้น
/home/steam/steamcmd/steamcmd.sh +force_install_dir /home/steam/pzserver +login anonymous +app_update 380870 -beta unstable validate +quit || echo "SteamCMD update had some issues, continuing anyway..."

# จัดการแก้ไข ProjectZomboid64.json
if [ -f "$PZ_JSON" ]; then
    echo "Patching ProjectZomboid64.json for performance..."
    sed -i 's/-Xmx[0-9]*g/-Xmx12g/g' "$PZ_JSON"
    sed -i 's/UseZGC/UseG1GC/g' "$PZ_JSON"
    echo "Current vmArgs in ProjectZomboid64.json:"
    grep -E "Xmx|UseG1GC" "$PZ_JSON"
else
    echo "Warning: $PZ_JSON not found! Attempting to start server anyway..."
fi

# JVM Tuning
export JSIG=""
cd /home/steam/pzserver

echo "--- Starting Project Zomboid Server ---"
exec bash ./start-server.sh \
    -servername b42coop \
    -adminpassword CHANGEME_PASSWORD \
    -Xms12G \
    -Xmx12G \
    -XX:+UseG1GC \
    -XX:MaxGCPauseMillis=50 \
    -XX:+UnlockExperimentalVMOptions \
    -XX:G1NewSizePercent=20 \
    -XX:G1ReservePercent=20 \
    -XX:G1HeapRegionSize=32M \
    -XX:+ParallelRefProcEnabled \
    -XX:ParallelGCThreads=8
