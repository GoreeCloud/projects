"""GoreeCloud Projects single-user preview API. No implicit multi-user permissions."""
from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from datetime import date, datetime, timezone
import hmac
import os
from pathlib import Path
import re
import sqlite3
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator

Status = Literal["backlog", "todo", "in_progress", "in_review", "done", "canceled"]
Priority = Literal["none", "urgent", "high", "medium", "low"]
KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,7}$")
bearer = HTTPBearer(auto_error=False)
SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, project_key TEXT NOT NULL UNIQUE,
 description TEXT NOT NULL DEFAULT '', archived INTEGER NOT NULL DEFAULT 0,
 next_issue INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cycles (
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 name TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL,
 created_at TEXT NOT NULL, CHECK(end_date >= start_date)
);
CREATE INDEX IF NOT EXISTS cycles_project ON cycles(project_id);
CREATE TABLE IF NOT EXISTS issues (
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 number INTEGER NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL DEFAULT 'backlog',
 priority TEXT NOT NULL DEFAULT 'none', assignee TEXT,
 cycle_id TEXT REFERENCES cycles(id), due_date TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(project_id, number)
);
CREATE INDEX IF NOT EXISTS issues_project_status ON issues(project_id,status);
CREATE INDEX IF NOT EXISTS issues_project_updated ON issues(project_id,updated_at);
CREATE TABLE IF NOT EXISTS comments (
 id TEXT PRIMARY KEY, issue_id TEXT NOT NULL REFERENCES issues(id),
 author TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS comments_issue ON comments(issue_id,created_at);
"""

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def db_path() -> Path:
    return Path(os.getenv("PROJECTS_DB_PATH", "./data/projects.sqlite3")).resolve()

def initialize_db() -> None:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        conn.execute("PRAGMA user_version = 1")
    if os.name == "posix":
        path.chmod(0o600)

@contextmanager
def session():
    conn = sqlite3.connect(db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_one(conn, query, params=()):
    row = conn.execute(query, params).fetchone()
    if row is None:
        raise HTTPException(404, "Resource not found")
    return dict(row)

def require_token(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    expected = os.getenv("PROJECTS_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(503, "PROJECTS_ADMIN_TOKEN is required")
    if len(expected) < 24:
        raise HTTPException(503, "PROJECTS_ADMIN_TOKEN must have at least 24 characters")
    if credentials is None or not hmac.compare_digest(credentials.credentials, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid access token",
                            headers={"WWW-Authenticate": "Bearer"})
    return True

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class ProjectCreate(Strict):
    name: str = Field(min_length=1, max_length=120)
    key: str = Field(min_length=2, max_length=8)
    description: str = Field(default="", max_length=4000)

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        value = value.upper()
        if not KEY_RE.fullmatch(value):
            raise ValueError("Use 2-8 letters/digits; start with a letter")
        return value

class ProjectPatch(Strict):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    archived: bool | None = None

class IssueCreate(Strict):
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=20000)
    status: Status = "backlog"
    priority: Priority = "none"
    assignee: str | None = Field(default=None, max_length=120)
    cycle_id: str | None = None
    due_date: date | None = None

class IssuePatch(Strict):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=20000)
    status: Status | None = None
    priority: Priority | None = None
    assignee: str | None = Field(default=None, max_length=120)
    cycle_id: str | None = None
    due_date: date | None = None

class CycleCreate(Strict):
    name: str = Field(min_length=1, max_length=120)
    start_date: date
    end_date: date

class CommentCreate(Strict):
    author: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=10000)

def validate_cycle(conn, project_id: str, cycle_id: str | None):
    if cycle_id is not None:
        match = conn.execute("SELECT 1 FROM cycles WHERE id=? AND project_id=?",
                             (cycle_id, project_id)).fetchone()
        if not match:
            raise HTTPException(422, "Cycle must belong to the issue project")

def format_issue(conn, row):
    issue = dict(row)
    key = conn.execute("SELECT project_key FROM projects WHERE id=?",
                       (issue["project_id"],)).fetchone()
    issue["identifier"] = f"{key['project_key']}-{issue['number']}"
    return issue

@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_db()
    yield

app = FastAPI(title="GoreeCloud Projects API", version="0.1.0", lifespan=lifespan)
origins = [x.strip() for x in os.getenv("PROJECTS_CORS_ORIGINS", "").split(",") if x.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                       allow_methods=["GET", "POST", "PATCH"], allow_headers=["Authorization", "Content-Type"])

@app.get("/healthz")
def health():
    return {"status": "ok", "service": "goreecloud-projects", "version": "0.1.0"}

@app.get("/api/v1/projects", dependencies=[Depends(require_token)])
def list_projects(include_archived: bool = False):
    with session() as conn:
        sql = "SELECT * FROM projects" + ("" if include_archived else " WHERE archived=0") + " ORDER BY name COLLATE NOCASE"
        return [dict(r) for r in conn.execute(sql)]

@app.post("/api/v1/projects", status_code=201, dependencies=[Depends(require_token)])
def create_project(payload: ProjectCreate):
    id_, ts = str(uuid4()), now()
    with session() as conn:
        try:
            conn.execute("INSERT INTO projects (id,name,project_key,description,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                         (id_, payload.name, payload.key, payload.description, ts, ts))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Project key is already in use")
        return get_one(conn, "SELECT * FROM projects WHERE id=?", (id_,))

@app.get("/api/v1/projects/{project_id}", dependencies=[Depends(require_token)])
def get_project(project_id: str):
    with session() as conn:
        return get_one(conn, "SELECT * FROM projects WHERE id=?", (project_id,))

@app.patch("/api/v1/projects/{project_id}", dependencies=[Depends(require_token)])
def update_project(project_id: str, payload: ProjectPatch):
    fields = payload.model_dump(exclude_unset=True)
    with session() as conn:
        get_one(conn, "SELECT * FROM projects WHERE id=?", (project_id,))
        if fields:
            clean = {k: int(v) if k == "archived" else v for k, v in fields.items()}
            if any(v is None for v in clean.values()):
                raise HTTPException(422, "Null is not a valid project update")
            clean["updated_at"] = now()
            sql = ", ".join(f"{k}=?" for k in clean)
            conn.execute(f"UPDATE projects SET {sql} WHERE id=?", (*clean.values(), project_id))
        return get_one(conn, "SELECT * FROM projects WHERE id=?", (project_id,))

@app.get("/api/v1/projects/{project_id}/cycles", dependencies=[Depends(require_token)])
def list_cycles(project_id: str):
    with session() as conn:
        get_one(conn, "SELECT id FROM projects WHERE id=?", (project_id,))
        return [dict(r) for r in conn.execute("SELECT * FROM cycles WHERE project_id=? ORDER BY start_date DESC", (project_id,))]

@app.post("/api/v1/projects/{project_id}/cycles", status_code=201, dependencies=[Depends(require_token)])
def create_cycle(project_id: str, payload: CycleCreate):
    if payload.end_date < payload.start_date:
        raise HTTPException(422, "Cycle end_date must be after start_date")
    id_ = str(uuid4())
    with session() as conn:
        get_one(conn, "SELECT id FROM projects WHERE id=? AND archived=0", (project_id,))
        conn.execute("INSERT INTO cycles VALUES (?,?,?,?,?,?)",
                     (id_, project_id, payload.name, str(payload.start_date), str(payload.end_date), now()))
        return get_one(conn, "SELECT * FROM cycles WHERE id=?", (id_,))

@app.get("/api/v1/projects/{project_id}/issues", dependencies=[Depends(require_token)])
def list_issues(project_id: str, state: Status | None = None,
                search: Annotated[str | None, Query(max_length=120)] = None,
                limit: Annotated[int, Query(ge=1, le=200)] = 100,
                offset: Annotated[int, Query(ge=0)] = 0):
    with session() as conn:
        get_one(conn, "SELECT id FROM projects WHERE id=?", (project_id,))
        sql = "SELECT * FROM issues WHERE project_id=?"
        params: list = [project_id]
        if state:
            sql += " AND status=?"
            params.append(state)
        if search:
            sql += " AND (title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\')"
            term = "%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            params.extend([term, term])
        sql += " ORDER BY updated_at DESC, number DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        return [format_issue(conn, r) for r in conn.execute(sql, params).fetchall()]

@app.post("/api/v1/projects/{project_id}/issues", status_code=201, dependencies=[Depends(require_token)])
def create_issue(project_id: str, payload: IssueCreate):
    id_, ts = str(uuid4()), now()
    with session() as conn:
        conn.execute("BEGIN IMMEDIATE")
        project = get_one(conn, "SELECT * FROM projects WHERE id=? AND archived=0", (project_id,))
        validate_cycle(conn, project_id, payload.cycle_id)
        number = project["next_issue"]
        conn.execute("UPDATE projects SET next_issue=? WHERE id=?", (number + 1, project_id))
        conn.execute("""INSERT INTO issues
        (id,project_id,number,title,description,status,priority,assignee,cycle_id,due_date,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (id_, project_id, number, payload.title, payload.description, payload.status, payload.priority,
         payload.assignee, payload.cycle_id, str(payload.due_date) if payload.due_date else None, ts, ts))
        return format_issue(conn, get_one(conn, "SELECT * FROM issues WHERE id=?", (id_,)))

@app.get("/api/v1/issues/{issue_id}", dependencies=[Depends(require_token)])
def get_issue(issue_id: str):
    with session() as conn:
        return format_issue(conn, get_one(conn, "SELECT * FROM issues WHERE id=?", (issue_id,)))

@app.patch("/api/v1/issues/{issue_id}", dependencies=[Depends(require_token)])
def update_issue(issue_id: str, payload: IssuePatch):
    fields = payload.model_dump(exclude_unset=True)
    with session() as conn:
        current = get_one(conn, "SELECT * FROM issues WHERE id=?", (issue_id,))
        if fields:
            if "cycle_id" in fields:
                validate_cycle(conn, current["project_id"], fields["cycle_id"])
            for key in ("title", "description", "status", "priority"):
                if key in fields and fields[key] is None:
                    raise HTTPException(422, f"{key} cannot be null")
            if "due_date" in fields:
                fields["due_date"] = str(fields["due_date"]) if fields["due_date"] else None
            fields["updated_at"] = now()
            sql = ", ".join(f"{k}=?" for k in fields)
            conn.execute(f"UPDATE issues SET {sql} WHERE id=?", (*fields.values(), issue_id))
        return format_issue(conn, get_one(conn, "SELECT * FROM issues WHERE id=?", (issue_id,)))

@app.get("/api/v1/issues/{issue_id}/comments", dependencies=[Depends(require_token)])
def list_comments(issue_id: str):
    with session() as conn:
        get_one(conn, "SELECT id FROM issues WHERE id=?", (issue_id,))
        return [dict(r) for r in conn.execute("SELECT * FROM comments WHERE issue_id=? ORDER BY created_at,id", (issue_id,))]

@app.post("/api/v1/issues/{issue_id}/comments", status_code=201, dependencies=[Depends(require_token)])
def add_comment(issue_id: str, payload: CommentCreate):
    id_ = str(uuid4())
    with session() as conn:
        get_one(conn, "SELECT id FROM issues WHERE id=?", (issue_id,))
        conn.execute("INSERT INTO comments VALUES (?,?,?,?,?)",
                     (id_, issue_id, payload.author, payload.body, now()))
        return get_one(conn, "SELECT * FROM comments WHERE id=?", (id_,))

@app.get("/api/v1/projects/{project_id}/stats", dependencies=[Depends(require_token)])
def project_stats(project_id: str):
    with session() as conn:
        get_one(conn, "SELECT id FROM projects WHERE id=?", (project_id,))
        counts = {r["status"]: r["n"] for r in conn.execute(
            "SELECT status,COUNT(*) AS n FROM issues WHERE project_id=? GROUP BY status",
            (project_id,))}
        return {"total": sum(counts.values()), "by_status": counts}
