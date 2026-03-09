# Lineup Builder — Server

FastAPI + Discord bot backend for the Lineup Builder desktop app. Deployed on [Railway](https://railway.app).

## Structure

```
server/
├── requirements.txt        # Python dependencies
├── README.md
└── src/
    ├── server.py           # FastAPI app + Discord bot
    ├── db.py               # SQLite database layer (aiosqlite)
    ├── requirements.txt    # Copy for Railway deploy context
    ├── Procfile            # Railway process definition
    ├── railway.toml        # Railway build/deploy config
    └── nixpacks.toml       # Nixpacks build config
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Discord bot token |
| `API_KEY` | Yes | Shared secret for desktop app ↔ server auth |
| `VRCHAT_AUTH_COOKIE` | No | VRChat auth cookie for group verification |
| `DB_PATH` | No | SQLite database file path (default: `lineup.db`) |
| `PORT` | Auto | Set automatically by Railway |

## Local Development

```bash
cd server/src
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Set environment variables
$env:DISCORD_BOT_TOKEN = "your-token"
$env:API_KEY = "your-key"

# Run with auto-reload
uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

Or from the project root:

```bash
python dev_server.py
```

## API Endpoints

All endpoints except `/health` require the `X-API-Key` header.

### Health & Status

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (no auth) |
| `GET` | `/bot/status` | Discord bot connection status |

### Discord Channels & Posting

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/channels` | List bot-accessible text channels |
| `POST` | `/post/embed` | Post a rich embed to a channel |
| `POST` | `/post/message` | Post a plain text message to a channel |

### Scheduled Posts

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/schedule` | Schedule a post for a future time |
| `GET` | `/schedule` | List all pending scheduled posts |
| `DELETE` | `/schedule/{post_id}` | Cancel a scheduled post |

### DJ Profiles

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/dj/register` | Register a new DJ profile |
| `POST` | `/dj/login` | Authenticate a DJ |
| `POST` | `/dj/discord-auth` | Link a DJ profile via Discord OAuth |
| `GET` | `/dj/profile/{name}` | Get a DJ's public profile |
| `PUT` | `/dj/profile` | Update a DJ's profile |
| `GET` | `/dj/list` | List all registered DJs |

### Bookings

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/booking` | Create a booking request |
| `GET` | `/bookings/dj/{dj_name}` | List bookings for a DJ |
| `GET` | `/bookings/group/{group_name}` | List bookings by group |
| `PUT` | `/booking/{booking_id}/respond` | Accept or decline a booking |

### User Data (Cloud Sync)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/user/{discord_id}/data/{key}` | Get a stored value |
| `PUT` | `/user/{discord_id}/data/{key}` | Store a value |
| `GET` | `/user/{discord_id}/data` | List all stored keys |

### VRChat

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/vrchat/verify-group` | Verify ownership of a VRChat group |
| `GET` | `/user/{discord_id}/vrchat-group` | Get a user's linked VRChat group |

## Database

SQLite with WAL mode. Three tables:

- **`dj_profiles`** — DJ name, Discord ID, links, logo, availability
- **`bookings`** — Booking requests between groups and DJs
- **`user_data`** — Key-value cloud storage per Discord user

## Deployment

Railway root directory should be set to `server/src/`. The build uses Nixpacks with Python 3.11.