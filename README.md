# Project Zomboid Build 42 Unstable Server

A high-performance, Dockerized environment for running a **Project Zomboid Build 42 Unstable** dedicated server. Optimized for **Host Networking** and **ZGC** performance.

---

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/OmTanakorn/project-zomboid-server.git
   cd project-zomboid-server
   ```

2. **Prepare Directories** (Ensure correct permissions)
   ```bash
   mkdir -p pz-data pz-config
   sudo chown -R 1000:1000 .
   ```

3. **Start the Server**
   ```bash
   docker compose up -d
   ```
   *The server will download SteamCMD and Project Zomboid (~5 GB) on first run.*

4. **Monitor Logs**
   ```bash
   docker compose logs -f pz-b42-server
   ```

---

## 🎮 Server Configuration (Build 42)

เซิร์ฟเวอร์นี้ถูกตั้งค่าให้รัน **Build 42 Unstable** โดยใช้โครงสร้างไฟล์ดังนี้:

### 1. ไฟล์และโฟลเดอร์หลัก
- **`pz-config/`**: ข้อมูลการตั้งค่าเซิร์ฟเวอร์ (Sandbox, Mods, Save files)
- **`pz-data/`**: ข้อมูลตัวเกมที่ดาวน์โหลดมาจาก Steam
- **`docker-compose.yml`**: การตั้งค่า Docker (Memory: 12GB, App ID: 380870)

### 2. การตั้งค่าที่สำคัญ
- **Network**: `host` mode (ใช้ Port พื้นฐานของเกม 16261, 16262 โดยตรง)
- **JVM Optimization**: ตั้งค่า RAM 12GB พร้อมระบบ **ZGC** เพื่อลดอาการกระตุก
- **Backups**: ระบบสำรองข้อมูลอัตโนมัติทุกๆ **4 ชั่วโมง** เก็บไว้สูงสุด 5 ชุด

### 3. การจัดการเซิร์ฟเวอร์เชิงลึก
รายละเอียดวิธีเพิ่ม Mod, ปรับแต้มตัวละครฟรี, หรือแก้ไขตัวคูณ XP:
👉 **[SERVER_GUIDE.md](./SERVER_GUIDE.md)**
👉 **[GEMINI.md](./GEMINI.md)** (AI File Map)

---

## 🛠️ Essential Commands

| คำสั่ง | วัตถุประสงค์ |
|--------|--------------|
| `docker compose restart pzserver` | รีสตาร์ทเพื่อโหลด Config ใหม่ |
| `docker compose pull` | อัปเดตไฟล์ SteamCMD (ถ้ามี) |
| `docker compose down` | ปิดเซิร์ฟเวอร์ |

---

## ⚠️ Build 42 Unstable Disclaimer
เวอร์ชันนี้ยังอยู่ในช่วงพัฒนา (Unstable) ไฟล์เซฟและม็อดอาจเกิดข้อผิดพลาดได้ง่าย ระบบสำรองข้อมูล (Internal Backup) ถูกเปิดใช้งานไว้แล้วที่ `pz-config/backups/` เพื่อความปลอดภัยครับ
