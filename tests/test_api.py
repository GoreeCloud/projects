import os
from fastapi.testclient import TestClient
import pytest
from apps.api.main import app

TOKEN = "testing-only-token-longer-than-24"

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PROJECTS_DB_PATH", str(tmp_path / "projects.sqlite3"))
    monkeypatch.setenv("PROJECTS_ADMIN_TOKEN", TOKEN)
    with TestClient(app) as test:
        yield test

@pytest.fixture()
def headers():
    return {"Authorization": f"Bearer {TOKEN}"}

def test_requires_authentication(client, headers):
    assert client.get("/healthz").status_code == 200
    assert client.get("/api/v1/projects").status_code == 401
    assert client.get("/api/v1/projects", headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.get("/api/v1/projects", headers=headers).json() == []

def test_project_and_issue_lifecycle(client, headers):
    project = client.post("/api/v1/projects", headers=headers, json={"name": "Notebook", "key": "nb"}).json()
    assert project["project_key"] == "NB"
    assert client.post("/api/v1/projects", headers=headers,
                       json={"name": "Duplicate", "key": "NB"}).status_code == 409
    pid = project["id"]
    cycle = client.post(f"/api/v1/projects/{pid}/cycles", headers=headers,
                        json={"name": "Sprint 1", "start_date": "2026-11-20", "end_date": "2026-12-01"})
    assert cycle.status_code == 201
    issue = client.post(f"/api/v1/projects/{pid}/issues", headers=headers,
                        json={"title": "Support offline editing", "priority": "high",
                              "cycle_id": cycle.json()["id"]})
    assert issue.status_code == 201
    value = issue.json()
    assert value["identifier"] == "NB-1"
    assert value["status"] == "backlog"
    patch = client.patch(f"/api/v1/issues/{value['id']}", headers=headers,
                         json={"status": "in_progress", "due_date": "2026-12-01"})
    assert patch.status_code == 200 and patch.json()["status"] == "in_progress"
    assert client.get(f"/api/v1/projects/{pid}/issues", headers=headers, params={"state":"in_progress"}).json()[0]["identifier"] == "NB-1"
    assert client.get(f"/api/v1/projects/{pid}/stats", headers=headers).json() == {
        "total": 1, "by_status": {"in_progress": 1}}
    comment = client.post(f"/api/v1/issues/{value['id']}/comments",
                          headers=headers, json={"author": "GoreeCloud", "body": "Starting."})
    assert comment.status_code == 201
    assert len(client.get(f"/api/v1/issues/{value['id']}/comments", headers=headers).json()) == 1

def test_rejects_cross_project_cycles_and_invalid_updates(client, headers):
    a = client.post("/api/v1/projects", headers=headers, json={"name":"A","key":"AA"}).json()
    b = client.post("/api/v1/projects", headers=headers, json={"name":"B","key":"BB"}).json()
    cy = client.post(f"/api/v1/projects/{a['id']}/cycles", headers=headers,
                     json={"name":"Cycle","start_date":"2026-11-20","end_date":"2026-11-21"}).json()
    res = client.post(f"/api/v1/projects/{b['id']}/issues", headers=headers,
                      json={"title":"Invalid","cycle_id":cy["id"]})
    assert res.status_code == 422
    item = client.post(f"/api/v1/projects/{b['id']}/issues", headers=headers, json={"title":"Valid"}).json()
    assert item["number"] == 1
    assert client.patch(f"/api/v1/issues/{item['id']}", headers=headers, json={"status":"unknown"}).status_code == 422
    assert client.patch(f"/api/v1/issues/{item['id']}", headers=headers, json={"title":None}).status_code == 422
    assert client.post("/api/v1/projects", headers=headers, json={"name":"Invalid","key":"--"}).status_code == 422

def test_archiving_and_search(client, headers):
    project = client.post("/api/v1/projects", headers=headers, json={"name":"Search", "key":"SEA"}).json()
    pid = project["id"]
    for title in ["alpha release", "beta release", "100% done"]:
        client.post(f"/api/v1/projects/{pid}/issues", headers=headers, json={"title":title})
    assert len(client.get(f"/api/v1/projects/{pid}/issues", headers=headers, params={"search":"release"}).json()) == 2
    assert len(client.get(f"/api/v1/projects/{pid}/issues", headers=headers, params={"search":"%"}).json()) == 1
    assert client.get(f"/api/v1/projects/{pid}/issues", headers=headers, params={"limit":201}).status_code == 422
    assert client.patch(f"/api/v1/projects/{pid}", headers=headers, json={"archived":True}).status_code == 200
    assert client.get("/api/v1/projects", headers=headers).json() == []
    assert client.post(f"/api/v1/projects/{pid}/issues", headers=headers, json={"title":"No"}).status_code == 404
