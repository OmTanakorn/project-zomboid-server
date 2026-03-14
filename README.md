# project-zomboid-server

Project Zomboid dedicated server running in Docker Compose — configured for **Build 42 Unstable** (`b42multiplayer` beta branch).

## Requirements

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/install/) v2+

## Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/OmTanakorn/project-zomboid-server.git
   cd project-zomboid-server
   ```

2. **Create your environment file**

   ```bash
   cp .env.example .env
   ```

   Open `.env` and set a secure `ADMIN_PASSWORD` and optionally a `SERVER_PASSWORD`.

3. **Start the server**

   ```bash
   docker compose up -d
   ```

   The first run will download the Project Zomboid dedicated server files (~5 GB). Monitor progress with:

   ```bash
   docker compose logs -f
   ```

4. **Stop the server**

   ```bash
   docker compose down
   ```

## Configuration

All settings are controlled via the `.env` file (copied from `.env.example`).

| Variable          | Default          | Description                               |
|-------------------|------------------|-------------------------------------------|
| `BETA_BRANCH`     | `b42multiplayer` | Steam beta branch (Build 42 Unstable)     |
| `BETA_PASSWORD`   | *(empty)*        | Beta branch password (if required)        |
| `SERVER_NAME`     | `servertest`     | Server name / save-file identifier        |
| `SERVER_PASSWORD` | *(empty)*        | Password players need to join             |
| `ADMIN_PASSWORD`  | `changeme`       | In-game admin password (**change this!**) |
| `MAX_PLAYERS`     | `16`             | Maximum concurrent players                |
| `MAX_RAM`         | `4096m`          | JVM heap size for the server              |
| `SERVER_PORT`     | `16261`          | Primary UDP game port (host)              |
| `SERVER_PORT_2`   | `16262`          | Secondary UDP game port (host)            |

## Ports

| Port  | Protocol | Purpose                    |
|-------|----------|----------------------------|
| 16261 | UDP      | Primary game / client port |
| 16262 | UDP      | Secondary game port        |

## Data Persistence

Server save files, mods, and configuration are stored in the `pz-data` Docker volume (`/serverdata/serverfiles` inside the container). The volume persists across container restarts and upgrades.

To back up your world:

```bash
docker run --rm \
  -v project-zomboid-server_pz-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/pz-backup.tar.gz -C /data .
```

## Switching to Stable Build 41

To run the stable Build 41 branch instead, edit `.env`:

```dotenv
BETA_BRANCH=
BETA_PASSWORD=
```

Then restart the server:

```bash
docker compose down
docker compose up -d
```

## Updating the Server

Pull the latest game files by recreating the container:

```bash
docker compose pull
docker compose up -d --force-recreate
```
