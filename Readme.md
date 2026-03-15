# Nanite

A Notion-style personal knowledge base with semantic search. Markdown-first, folder/subpage hierarchy, and vector-powered search — all self-hosted.

---

## What we decided

### Core features
- Markdown note editor
- Folder + subpage hierarchy (Notion-style)
- Semantic search via embeddings (triggers on Ctrl+S only)
- User accounts with email verification
- Soft delete (recycle bin) for notes and accounts

### Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 14 + Tailwind + Bun | familiar, fast |
| Backend | FastAPI + fastapi-users | Python, async, auth built-in |
| Database | PostgreSQL + pgvector | one DB for data + vectors |
| Cache/Queue | Redis | JWT blacklist + ARQ job queue + Redlock |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | local, no API cost |
| Migrations | Alembic | SQLAlchemy-native |

---

## Architecture

```
Next.js Frontend
      ↓
FastAPI (main API + auth)
      ↓
Postgres + pgvector ←──── Embedding Workers (ARQ)
      ↑                          ↑
      └────────── Redis ──────────┘
           (blacklist + queue + locks)
```

### Redis — 3 responsibilities
- `blacklist:{jti}` — JWT blacklisting on logout (TTL = token expiry)
- `arq:queue` — ARQ job queue for embedding tasks
- `lock:note:{id}` — Redlock per note_id, prevents race conditions across workers

### Embedding flow (Ctrl+S)
1. User hits Ctrl+S
2. FastAPI validates JWT → checks Redis blacklist
3. FastAPI saves note to Postgres, increments `version`
4. FastAPI pushes embed job to Redis queue
5. Worker acquires Redlock on `note_id`
6. Worker checks job version == current note version (stale job guard)
7. Worker embeds content → writes vector to Postgres
8. Lock released. Note is now searchable.

### Auth flow
1. Signup → bcrypt hash → store in DB → send verification email → `is_active = false`
2. Email verified → `is_active = true`
3. Login guard (in order):
   - email exists? → 404
   - `is_active = true`? → 403 not verified
   - `deleted_at IS NULL`? → 403 account deleted
   - password matches? → 401
   - all good → issue JWT
4. Logout → write JTI to Redis blacklist with TTL
5. Every request → check Redis blacklist before processing

---

## Database design

### Two tables only

**`users`** — managed by fastapi-users

```sql
users (
  id                UUID PRIMARY KEY,
  email             TEXT UNIQUE NOT NULL,
  hashed_password   TEXT NOT NULL,
  is_active         BOOLEAN DEFAULT false,  -- flips true on email verify
  is_verified       BOOLEAN DEFAULT false,
  is_superuser      BOOLEAN DEFAULT false,
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now(),
  deleted_at        TIMESTAMPTZ             -- null = active, set = soft deleted
)
```

**`nodes`** — folders + notes, single table (single table inheritance)

```sql
nodes (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES users(id) ,
  parent_id     UUID REFERENCES nodes(id) ,  -- null = root
  type          TEXT CHECK (type IN ('note', 'folder')),
  title         TEXT NOT NULL,
  content       TEXT,                     -- null if folder
  embedding     vector(384),              -- null if folder or pending
  embed_status  TEXT DEFAULT 'pending',   -- pending | done | failed
  version       INT DEFAULT 0,            -- increments on every edit
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now(),
  deleted_at    TIMESTAMPTZ               -- null = active, soft delete
)
```

### Why one table for folders + notes?
- Tree traversal (`WITH RECURSIVE`) stays clean with one table
- Move operations are a single `UPDATE nodes SET parent_id = :new` query
- Cycle detection (prevent moving folder into its own descendant) is one recursive query
- Two tables would require UNION on every sidebar fetch and ugly joins on moves

### Key queries

```sql
-- fetch children of a folder
SELECT * FROM nodes
WHERE parent_id = :id AND user_id = :uid AND deleted_at IS NULL
ORDER BY type DESC, title;

-- move node
UPDATE nodes SET parent_id = :new_parent_id
WHERE id = :id AND user_id = :uid;

-- semantic search
SELECT id, title, content,
       1 - (embedding <=> :query_vec) AS similarity
FROM nodes
WHERE user_id = :uid AND type = 'note' AND deleted_at IS NULL
ORDER BY embedding <=> :query_vec
LIMIT 10;
```

### Soft delete pattern
Never `DELETE`. Always:
```sql
UPDATE nodes SET deleted_at = now() WHERE id = :id AND user_id = :uid;
```

Use a Postgres view to never forget the filter:
```sql
CREATE VIEW active_nodes AS
  SELECT * FROM nodes WHERE deleted_at IS NULL;
```

---

## Folder structure

```
Nanite/
├── .gitignore
├── README.md
├── backend/
│   ├── pyproject.toml
│   ├── .env
│   ├── alembic.ini
│   ├── alembic/
│   └── app/
│       ├── main.py
│       ├── core/
│       │   ├── config.py        # settings, env vars (pydantic-settings)
│       │   ├── security.py      # JWT issue, verify, blacklist check
│       │   └── dependencies.py  # get_db, get_current_user
│       ├── features/
│       │   ├── auth/
│       │   │   ├── router.py    # POST /auth/login, /auth/logout, /auth/signup
│       │   │   ├── service.py   # login guard (deleted_at, is_active checks)
│       │   │   └── schemas.py   # LoginRequest, TokenResponse
│       │   ├── nodes/
│       │   │   ├── router.py    # CRUD + move + search routes
│       │   │   ├── service.py   # business logic, cycle detection
│       │   │   ├── schemas.py   # NodeCreate, NodeResponse, NodeMove
│       │   │   └── models.py    # Node SQLAlchemy model
│       │   └── users/
│       │       ├── router.py    # GET /users/me, DELETE /users/me
│       │       ├── service.py   # soft delete, account management
│       │       ├── schemas.py   # UserResponse
│       │       └── models.py    # User SQLAlchemy model
│       └── workers/
│           └── embed.py         # ARQ worker — dequeues jobs, embeds, writes vector
└── frontend/
    ├── package.json
    └── src/
        ├── app/                 # Next.js app router
        ├── components/
        └── lib/
```

### Feature-based structure
Each feature is self-contained. Adding a new feature = new folder under `features/`. Nothing else touched.

- `router.py` — HTTP layer only, thin, calls service
- `service.py` — all business logic
- `schemas.py` — Pydantic serialization/deserialization (request → python, python → response)
- `models.py` — SQLAlchemy table definition

---

## Setup

### Prerequisites
- Python 3.12
- `uv` (Python package manager)
- `bun` (JS package manager)
- PostgreSQL with pgvector extension
- Redis

### Backend
```bash
cd backend
uv sync
cp .env.example .env   # fill in your values
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
bun install
bun dev
```

### Embedding worker
```bash
cd backend
uv run arq app.workers.embed.WorkerSettings
```

---

## Environment variables

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nanite
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## What's next
- [ ] Alembic setup + initial migration (users + nodes tables)
- [ ] SQLAlchemy models (`User`, `Node`)
- [ ] fastapi-users integration with custom login guard
- [ ] JWT blacklist middleware
- [ ] Node CRUD routes
- [ ] ARQ worker setup
- [ ] Embedding service (sentence-transformers)
- [ ] Semantic search endpoint
- [ ] Frontend: auth pages
- [ ] Frontend: sidebar tree
- [ ] Frontend: markdown editor (Ctrl+S save)
- [ ] Frontend: search UI
