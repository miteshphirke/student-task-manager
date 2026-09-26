"""
test_app.py
-----------
Pytest test-suite for the Student Task Management System.
Run with:  pytest -v   (from inside the app/ directory)

These tests use a temporary SQLite database file so they never touch
your real tasks.db, and Jenkins can run them with zero setup.
"""

import os
import sys
import tempfile
import pytest

# Make sure "app" and "models" (which live in app/) are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import models
import app as flask_app_module

flask_app_module.app.config["TESTING"] = True


@pytest.fixture
def client():
    # Point the app at a fresh temp DB file for every test, without re-importing
    # the app module (re-importing would try to register Prometheus metrics twice).
    db_fd, db_path = tempfile.mkstemp()
    models.DB_PATH = db_path
    models.init_db()

    with flask_app_module.app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200


def test_index_page_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"No tasks yet" in response.data


def test_add_task_get_form(client):
    response = client.get("/add")
    assert response.status_code == 200
    assert b"Add New Task" in response.data


def test_add_task_post_creates_task(client):
    response = client.post(
        "/add",
        data={
            "student_name": "Asha Patel",
            "title": "Finish DevOps assignment",
            "description": "Set up CI/CD pipeline",
            "due_date": "2026-10-01",
            "status": "Pending",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Finish DevOps assignment" in response.data
    assert b"Asha Patel" in response.data


def test_edit_task_updates_status(client):
    client.post(
        "/add",
        data={
            "student_name": "Rohan Mehta",
            "title": "Read chapter 5",
            "description": "",
            "due_date": "2026-11-01",
            "status": "Pending",
        },
    )
    import models
    tasks = models.get_all_tasks()
    task_id = tasks[0]["id"]

    response = client.post(
        f"/edit/{task_id}",
        data={
            "student_name": "Rohan Mehta",
            "title": "Read chapter 5",
            "description": "",
            "due_date": "2026-11-01",
            "status": "Completed",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Completed" in response.data


def test_delete_task_removes_it(client):
    client.post(
        "/add",
        data={
            "student_name": "Neha Gupta",
            "title": "Temporary Task",
            "description": "",
            "due_date": "",
            "status": "Pending",
        },
    )
    import models
    tasks = models.get_all_tasks()
    task_id = tasks[0]["id"]

    response = client.post(f"/delete/{task_id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Temporary Task" not in response.data
