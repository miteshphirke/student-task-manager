"""
app.py
------
Main Flask application for the Student Task Management System.

Routes:
  GET  /                 -> list all tasks
  GET  /add               -> show "add task" form
  POST /add               -> create a task
  GET  /edit/<id>         -> show "edit task" form
  POST /edit/<id>         -> update a task
  POST /delete/<id>       -> delete a task
  GET  /health            -> simple health check (used by Docker/Ansible/monitoring)
  GET  /metrics           -> Prometheus metrics endpoint
"""

import time
from flask import Flask, render_template, request, redirect, url_for
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

import models

app = Flask(__name__)

# ---- Prometheus metrics -----------------------------------------------
REQUEST_COUNT = Counter(
    "flask_app_request_count", "Total number of requests", ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "flask_app_request_latency_seconds", "Request latency in seconds", ["endpoint"]
)


@app.before_request
def start_timer():
    request._start_time = time.time()


@app.after_request
def record_metrics(response):
    if request.endpoint != "metrics":  # don't measure the metrics endpoint itself
        latency = time.time() - getattr(request, "_start_time", time.time())
        REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
        REQUEST_COUNT.labels(
            method=request.method, endpoint=request.path, http_status=response.status_code
        ).inc()
    return response


# ---- Routes -------------------------------------------------------------

@app.route("/")
def index():
    tasks = models.get_all_tasks()
    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        models.add_task(
            student_name=request.form["student_name"],
            title=request.form["title"],
            description=request.form.get("description", ""),
            due_date=request.form.get("due_date", ""),
            status=request.form.get("status", "Pending"),
        )
        return redirect(url_for("index"))
    return render_template("add_task.html")


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    task = models.get_task(task_id)
    if task is None:
        return redirect(url_for("index"))

    if request.method == "POST":
        models.update_task(
            task_id=task_id,
            student_name=request.form["student_name"],
            title=request.form["title"],
            description=request.form.get("description", ""),
            due_date=request.form.get("due_date", ""),
            status=request.form.get("status", "Pending"),
        )
        return redirect(url_for("index"))
    return render_template("edit_task.html", task=task)


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    models.delete_task(task_id)
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# ---- Entrypoint -----------------------------------------------------------
models.init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
