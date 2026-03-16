# 🎮 Project Zomboid Server Management Guide (Build 42)

คู่มือการจัดการและแก้ไขไฟล์คอนฟิกสำหรับเซิร์ฟเวอร์ Project Zomboid Build 42 Unstable

---

## 📂 ตำแหน่งไฟล์คอนฟิก (Directory Map)

### 1. การตั้งค่าเซิร์ฟเวอร์หลัก (Server Settings)
ไฟล์เหล่านี้อยู่ที่: `pz-config/Server/`
- **`b42coop.ini`**:
    - แก้ไขรายชื่อ Mod (`Mods=`)
    - แก้ไข Workshop ID (`WorkshopItems=`)
    - รหัสผ่าน Admin (`Password=`)
    - ระบบ Backup (`BackupsPeriod=`, `BackupsCount=`)
- **`b42coop_SandboxVars.lua`**:
    - แก้ไขกฎการเล่น (Sandbox Rules)
    - แต้มตัวละครฟรี (`CharacterFreePoints`)
    - ตัวคูณประสบการณ์ (`MultiplierConfig`)
    - ความเร็วของวันและความโหดของซอมบี้

### 2. การตั้งค่าม็อด (Workshop & Mod Settings)
- **การตั้งค่าผ่าน Sandbox (แนะนำ)**: อยู่ใน `b42coop_SandboxVars.lua` มองหาชื่อ Mod (เช่น `ProximityInventory = { ... }`)
- **ไฟล์ Mod โดยตรง (Advanced)**: `pz-data/steamapps/workshop/content/108600/`
    - ค้นหาตาม **Workshop ID** (เช่น `2866258937`)
    - ไฟล์ Lua จะอยู่ใน: `.../[Workshop_ID]/mods/[Mod_Name]/media/lua/`

---

## 🛠️ วิธีการแก้ไขที่พบบ่อย

### การเพิ่ม/ลบ Mod
1. เปิดไฟล์ `pz-config/Server/b42coop.ini`
2. เพิ่ม Mod ID ในบรรทัด `Mods=` (คั่นด้วย `;`)
3. เพิ่ม Workshop ID ในบรรทัด `WorkshopItems=` (คั่นด้วย `;`)
4. **Restart Server** เพื่อให้เริ่มดาวน์โหลด

### การปรับแต้มตัวละครใหม่
1. เปิดไฟล์ `pz-config/Server/b42coop_SandboxVars.lua`
2. แก้ไขค่า `CharacterFreePoints = [จำนวนแต้ม],`
3. **Restart Server**

---

## 🔄 คำสั่งควบคุมเซิร์ฟเวอร์ (Docker)

| คำสั่ง | วัตถุประสงค์ |
|--------|--------------|
| `docker compose up -d` | เริ่มเซิร์ฟเวอร์แบบเบื้องหลัง |
| `docker compose restart pzserver` | รีสตาร์ทเซิร์ฟเวอร์ (ต้องทำหลังแก้ Config) |
| `docker compose logs -f pzserver` | ดู Log การทำงานแบบ Real-time |
| `docker compose down` | ปิดเซิร์ฟเวอร์ |

---

## ⚠️ ข้อควรระวัง
- **Build 42 Unstable**: มีการเปลี่ยนแปลงบ่อยครั้ง ก่อนแก้ไขควร Backup เสมอ
- **Surgical Edits**: การลบ Mod กลางเซฟอาจทำให้ไอเทมหายหรือภาพตัวละครผิดปกติ
- **Case Sensitivity**: ใน Linux ชื่อไฟล์และตัวแปรต้องพิมพ์ตัวเล็ก/ใหญ่ให้ถูกต้องเสมอ
