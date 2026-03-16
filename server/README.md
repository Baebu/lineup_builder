# Lineup Builder — Server

A **FastAPI + Discord.py** backend that keeps the Discord bot online 24/7 while exposing REST endpoints for the desktop and web clients to manage lineups, DJs, bookings, and VRChat integration. Deployed on [Railway](https://railway.app).

## Overview

The server acts as the central coordination point for:
- **Discord bot** — Always-on bot that responds to commands, posts lineups, schedules events
- **REST API** — Authentication, DJ profiles, bookings, event scheduling, cloud sync
- **VRChat integration** — Group verification, bio-based linking
- **MongoDB storage** — Persistent DJ profiles, bookings, user data, club settings
- **Image hosting** — Upload/serve DJ avatars and banners

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.110+ | Fast, async REST API |
| **Bot** | discord.py 2.3+ | Discord bot client & interactions |
| **Database** | MongoDB + motor 3.3+ | Async document storage |
| **Auth** | APIKeyHeader + OAuth2 | API key for client auth, Discord OAuth for user login |
| **Server** | uvicorn 0.29+ | ASGI application server |
| **Upload** | FastAPI UploadFile | Multipart image upload to disk/S3 |
| **HTTP** | httpx 0.27+ | Async HTTP client for VRChat API |

## Directory Structure

```
server/
├── .env                           # Local environment variables (gitignored)
├── .env.example                   # Template for .env
├── requirements.txt               # Root-level Python deps (if used)
├── docker-compose.yml             # Local MongoDB for development
├── Procfile                       # Railway process definition
├── dev_server.py                  # Auto-reload dev runner script
├── vrc_state.json                 # Persistent VRChat rate-limit state
│
└── src/
    ├── main.py                    # Entry point (calls uvicorn)
    ├── server.py                  # FastAPI app, Discord bot, lifespan, background loops
    ├── config.py                  # Environment variables, logging setup
    ├── db.py                       # MongoDB collections, auto-increment IDs, indexes
    ├── mongo.py                    # MongoDB connection (motor)
    │
    ├── models/
    │   ├── schemas.py             # Pydantic request/response models (30+ classes)
    │   └── __init__.py
    │
    ├── routes/                    # API endpoint handlers (8 route modules)
    │   ├── discord.py             # POST embed, schedule, list channels (API KEY REQUIRED)
    │   ├── discord_oauth.py       # GET login-url, POST callback (PUBLIC)
    │   ├── dj.py                  # DJ CRUD: register, login, profile (PUBLIC + AUTH)
    │   ├── images.py              # Image upload/serve (PUBLIC)
    │   ├── bookings.py            # Create/respond to booking requests (PUBLIC + AUTH)
    │   ├── user_data.py           # Cloud save for library, events, settings (PUBLIC + AUTH)
    │   ├── club.py                # Club metadata & VRChat linking (PUBLIC + AUTH)
    │   ├── vrchat.py              # VRChat bio verification, group linking (PUBLIC)
    │   └── __init__.py
    │
    ├── services/
    │   ├── discord_bot.py         # Bot instance, embed builder, send helpers
    │   ├── vrchat_api.py          # VRChat API client, rate-limit caching
    │   └── __init__.py
    │
    ├── .venv/                     # Python virtual environment (local dev)
    ├── __init__.py
    ├── __pycache__/
    ├── requirements.txt           # Dependencies (copy of root)
    ├── pyproject.toml             # Tool configs (Ruff, pytest)
    ├── Procfile                   # Railway prod definition
    ├── railway.toml               # Railway build settings
    └── nixpacks.toml              # Alternative Nix-based build config
```

## API Endpoints

### Public Endpoints (No Authentication Required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/bot/status` | Bot connection status, list of guilds |
| `GET` | `/api/discord/login-url` | Generate Discord OAuth2 authorization URL |
| `GET` | `/api/discord/callback` | Discord OAuth2 redirect handler |
| `POST` | `/dj/register` | Register a new DJ account |
| `POST` | `/dj/login` | Login with DJ name & password |
| `POST` | `/images/upload` | Upload DJ avatar/banner |
| `GET` | `/images/{filename}` | Serve uploaded image |
| `POST` | `/booking` | Create a booking request |
| `POST` | `/booking/{id}/respond` | Accept/decline a booking |
| `GET` | `/bookings/{dj_id}` | List bookings for a DJ |
| `GET` | `/user/{discord_id}/data/{key}` | Fetch user's library/events/settings |
| `PUT` | `/user/{discord_id}/data/{key}` | Save user's library/events/settings |
| `GET` | `/user/{discord_id}/club` | Get club metadata (Discord link, VRChat info) |
| `POST` | `/vrchat/verify-bio` | Search VRChat user, verify code in bio |
| `POST` | `/vrchat/group/{id}/verify` | Verify VRChat group ownership |

### Authenticated Endpoints (API_KEY Required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/guilds` | List all bot guilds |
| `GET` | `/channels/{guild_id}` | List text channels in a guild |
| `POST` | `/post` | Post a lineup embed to a channel immediately |
| `POST` | `/schedule` | Schedule a lineup embed for future posting |
| `GET` | `/schedule` | List all scheduled posts |
| `PUT` | `/schedule/{id}` | Update a scheduled post |
| `DELETE` | `/schedule/{id}` | Cancel a scheduled post |
| `POST` | `/schedule/{id}/resend` | Resend a previously posted lineup |
| `GET` | `/sent` | List recently sent posts |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | — | Discord bot token from [Developer Portal](https://discord.com/developers/applications) |
| `API_KEY` | Yes | — | Shared secret between client and server (min 16 chars recommended) |
| `DISCORD_CLIENT_ID` | No | — | Discord OAuth client ID (required for user login) |
| `DISCORD_CLIENT_SECRET` | No | — | Discord OAuth client secret |
| `DISCORD_REDIRECT_URI` | No | `http://localhost:3000/api/discord/callback` | OAuth redirect URL (must match Developer Portal) |
| `MONGO_URI` | No | `mongodb://localhost:27017/lineup_builder` | MongoDB connection string (prod: Atlas URI) |
| `VRCHAT_USERNAME` | No | — | VRChat username (required for VRChat API access) |
| `VRCHAT_PASSWORD` | No | — | VRChat password |
| `VRCHAT_TOTP_SECRET` | No | — | VRChat 2FA TOTP secret (if 2FA enabled on account) |
| `IMAGES_DIR` | No | `server/uploads` | Directory where uploaded images are stored |
| `PORT` | Auto | `8000` | Listen port (set by Railway automatically) |

## Local Development

### Prerequisites

- Python 3.11+
- MongoDB running locally (or via Docker)
- Discord bot token from [Developer Portal](https://discord.com/developers/applications)

### Setup

```bash
# 1. Create virtual environment
cd server/src
python -m venv .venv
.venv\Scripts\activate              # Windows PowerShell
# or: source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file from template
cd ..
cp .env.example .env

# 4. Edit .env with your credentials
# You must set:
#   - DISCORD_BOT_TOKEN=your_token
#   - API_KEY=your_secret_key
#   - MONGO_URI (if not using default localhost)

# 5. (Optional) Start MongoDB via Docker
docker-compose up -d

# 6. Run the server with auto-reload
python dev_server.py
# or from src/: uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

The server will start on `http://127.0.0.1:8000`.

### Using Docker Compose

```bash
# Start MongoDB in background
docker-compose up -d

# Run server (in another terminal)
python dev_server.py

# Stop MongoDB when done
docker-compose down
```

## Database Schema

### Collections

#### `dj_profiles`
DJ account records with contact info and metadata.

```javascript
{
  _id: ObjectId,
  id: <int>,                      // auto-increment ID
  name: <string>,                 // unique DJ name (case-insensitive indexed)
  password: <hash>,               // bcrypt hash
  discord_id: <string>,           // optional link to Discord user
  display_name: <string>,         // shown in lineups (may differ from name)
  bio: <string>,                  // DJ bio
  genres: [<string>, ...],        // genre tags
  links: {                         // social links (URLs)
    "TIMELINE": "...",
    "VRCPOP": "...",
    "TWITCH": "...",
    ...
  },
  logo: <string>,                 // image filename or URL
  avatar: <string>,               // profile image filename
  availability: [<string>, ...],  // time availability (ISO format)
  created_at: <timestamp>,        // ISO 8601
  updated_at: <timestamp>,
}
```

#### `bookings`
Booking requests between clubs and DJs.

```javascript
{
  _id: ObjectId,
  id: <int>,                  // auto-increment ID
  dj_id: <int>,              // reference to dj_profiles.id
  group_name: <string>,      // club/group name
  event_title: <string>,     // lineup/event name
  event_date: <string>,      // "YYYY-MM-DD"
  start_time: <string>,      // "HH:MM"
  duration: <int>,           // minutes
  message: <string>,         // custom message from club
  discord_channel_id: <string>,  // for notifications
  status: <string>,          // "pending", "accepted", "declined"
  created_at: <timestamp>,
  updated_at: <timestamp>,
}
```

#### `user_data`
Cloud-saved app state per Discord user (library, events, settings).

```javascript
{
  _id: ObjectId,
  discord_id: <string>,      // Discord user ID
  key: <string>,             // "library", "events", or "settings"
  value: <object>,           // JSON blob
  updated_at: <timestamp>,
}
```

#### `clubs`
Club metadata and VRChat linking info.

```javascript
{
  _id: ObjectId,
  discord_id: <string>,      // Discord user ID (club owner)
  discord_link: <string>,    // Discord guild/channel link
  vrchat_group_id: <string>, // VRChat group ID
  vrchat_group_name: <string>,
  vrchat_short_code: <string>, // "shortcode.discriminator"
  vrchat_owner_id: <string>,
  vrchat_member_count: <int>,
  vrchat_icon_url: <string>,
  vrchat_banner_url: <string>,
  updated_at: <timestamp>,
}
```

#### `counters`
Auto-increment sequence counters (one doc per collection).

```javascript
{
  _id: <string>,  // collection name (e.g., "dj_profiles")
  seq: <int>,     // current sequence value
}
```

## Architecture & Data Flow

### Request Lifecycle

```
Client (desktop/web)
  ↓
FastAPI route handler (routes/*.py)
  ↓
Authorization check (API key or OAuth)
  ↓
Pydantic validation (models/schemas.py)
  ↓
Business logic (services/*, db.py)
  ↓
MongoDB operation (motor async driver)
  ↓
Response (JSON)
```

### Background Loops (in server.py)

Running asynchronously in the background:

1. **Scheduler Loop** (every 5 sec) — Check for due scheduled posts, fire them to Discord
2. **VRChat Keepalive Loop** (every 30 min) — Ping VRChat API to keep session alive
3. **Bot Event Handler** — Discord bot waiting for commands, responding to mentions

### Discord Bot Integration

The Discord bot is a `discord.Client` (not `commands.Bot`). It:
- Responds to slash commands (via message content for now)
- Posts embeds with computed slot times
- Handles scheduled posts via in-memory dict + periodic check

## Authentication & Security

### API Key (Desktop → Server)

Desktop app includes `API_KEY` header in all POST/PUT requests:

```python
headers = {"Authorization": f"Bearer {API_KEY}"}
```

Server verifies via `Depends(api_key_header)` on protected routes.

### Discord OAuth (Web Client Login)

1. User clicks "Sign In with Discord"
2. Web redirects to `/api/discord/login-url` → gets authorization URL
3. User logs into Discord → redirected to `/api/discord/callback`
4. Server exchanges code for access token, fetches user profile
5. User's Discord ID stored in browser (localStorage)
6. Cloud data keyed by Discord ID (e.g., `/user/{discord_id}/data/library`)

### VRChat Group Verification

1. User gets a verification code from web app
2. User adds code to their VRChat bio
3. User submits VRChat username via web
4. Server searches VRChat API for user, checks bio for code
5. If match, server links club to user's VRChat groups

## Performance & Rate-Limiting

### MongoDB Indexes

Created on startup (see `db.py:init_db()`):
- `dj_profiles`: name (unique, case-insensitive)
- `bookings`: dj_id, status, created_at
- `user_data`: discord_id, key
- `clubs`: discord_id

### VRChat API Rate-Limit

VRChat enforces strict rate limits. Server caches rate-limit state to disk (`vrc_state.json`) to survive restarts:

```python
_vrc_last_call: float = 0.0  # Timestamp of last request
VRC_LOGIN_COOLDOWN = 60      # Seconds between login attempts
```

Queries wait appropriately between requests.

### Discord Bot Ratelimits

Discord.py handles rate-limiting transparently. See [discord.py docs](https://discordpy.readthedocs.io/).

## Building & Deployment

### Production Build (Railway)

Railway auto-detects `Procfile` and runs:

```bash
uvicorn src.backend.server.server:app --host 0.0.0.0 --port $PORT
```

**Pre-deployment checklist:**
- [ ] Set all environment variables in Railway dashboard
- [ ] MongoDB Atlas cluster created and reachable
- [ ] Discord bot token and OAuth credentials set
- [ ] DISCORD_REDIRECT_URI matches app URL (e.g., `https://yourdomain.com/api/discord/callback`)

### Docker Build (Alternative)

```bash
docker build -t lineup-server .
docker run -p 8000:8000 \
  -e DISCORD_BOT_TOKEN="..." \
  -e API_KEY="..." \
  -e MONGO_URI="..." \
  lineup-server
```

## Code Organization

### routes/ — Request handlers

Each file is a logical feature:
- `discord.py` — Embed posting, scheduling, channel listing
- `dj.py` — DJ CRUD, authentication
- `images.py` — Image upload and serving
- `bookings.py` — Booking request lifecycle
- `user_data.py` — Cloud sync for app state
- `club.py` — Club metadata, VRChat linking
- `vrchat.py` — VRChat API integration
- `discord_oauth.py` — Discord user authentication

### services/ — External integrations

- `discord_bot.py` — Discord bot instance, embed builder, helpers
- `vrchat_api.py` — VRChat HTTP client, session management, caching

### models/ — Type definitions

- `schemas.py` — 30+ Pydantic models for request/response validation

### Utilities

- `config.py` — Environment variables, logging
- `db.py` — MongoDB collection helpers, auto-increment
- `mongo.py` — Motor connection, initialization
- `server.py` — FastAPI app, lifespan, background tasks

## Development Guidelines

### Code Style

- **Type hints** — Required on function signatures
- **Docstrings** — Module and function-level (""""...""")
- **Async/await** — All I/O is async (MongoDB, HTTP, Discord)
- **Validation** — Use Pydantic models for all input

### Testing

No test suite currently. For future tests:
- Mock MongoDB with `mongomock`
- Mock Discord client
- Test rate-limit caching
- Test OAuth flow

### Adding a New Route

1. Create a new file in `routes/` with an `APIRouter`
2. Define Pydantic models in `models/schemas.py`
3. Import router in `server.py` and `app.include_router()`
4. Add endpoints with appropriate dependencies

Example:

```python
# routes/myfeature.py
from fastapi import APIRouter, Depends
from models.schemas import MyRequest
from dependencies import api_key_header

router = APIRouter()

@router.post("/myendpoint", dependencies=[Depends(api_key_header)])
async def my_handler(req: MyRequest):
    return {"status": "ok"}
```

## Troubleshooting

### Issue: Discord bot won't connect
**Cause:** Invalid `DISCORD_BOT_TOKEN`  
**Solution:** Verify token in [Developer Portal](https://discord.com/developers/applications). Regenerate if needed.

### Issue: MongoDB connection refused
**Cause:** MongoDB not running locally  
**Solution:** Start MongoDB: `docker-compose up -d` or `mongod` command.

### Issue: VRChat API returns 401
**Cause:** Account credentials wrong or 2FA not configured  
**Solution:** Verify `VRCHAT_USERNAME`, `VRCHAT_PASSWORD`, `VRCHAT_TOTP_SECRET` in `.env`. Use 2FA-enabled account.

### Issue: OAuth callback URL mismatch
**Cause:** `DISCORD_REDIRECT_URI` doesn't match Developer Portal setting  
**Solution:** Update both to same URL (e.g., `https://yourapp.com/api/discord/callback`).

### Issue: Scheduled posts not firing
**Cause:** Server not running, or bot not ready  
**Solution:** Check logs. Ensure bot has sent at least one message (sets `bot_ready` flag).

### Issue: Images not uploading
**Cause:** `IMAGES_DIR` doesn't exist or not writable  
**Solution:** Create directory: `mkdir -p server/uploads`. Check permissions.

## Related Documentation

- **Desktop app** — See [desktop/README.md](../desktop/README.md)
- **Web client** — See [web/README.md](../web/README.md)
- **Discord.py docs** — https://discordpy.readthedocs.io/
- **FastAPI docs** — https://fastapi.tiangolo.com/
- **MongoDB docs** — https://docs.mongodb.com/

## License

See [LICENSE](../LICENSE) at project root.

---

**Last Updated:** 2026-03-16  
**Version:** 1.0.0

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