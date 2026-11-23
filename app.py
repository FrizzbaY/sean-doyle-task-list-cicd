import os
import sqlite3
import time

from flask import Flask, Response, g, redirect, render_template, request, url_for
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

MAX_TITLE_LENGTH = 200

# Module level, so every call of create_app shares the same counters
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Number of HTTP requests handled",
    ["method", "endpoint", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Time taken to handle an HTTP request",
    ["method", "endpoint"],
)

TASKS_ADDED = Counter("tasks_added_total", "Number of tasks added")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0
);
"""


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "DATABASE_PATH", os.path.join(app.instance_path, "tasks.db")
        ),
    )
    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(exception=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().executescript(SCHEMA)

    @app.before_request
    def start_timer():
        g.request_start = time.perf_counter()

    @app.after_request
    def record_metrics(response):
        if request.path == "/metrics":
            return response
        # Route pattern, not the real path, so /1/complete and /2/complete share one label
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        HTTP_REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        HTTP_REQUEST_DURATION.labels(request.method, endpoint).observe(
            time.perf_counter() - g.request_start
        )
        return response

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)

    @app.get("/")
    def index():
        tasks = get_db().execute(
            "SELECT id, title, completed FROM tasks ORDER BY id"
        ).fetchall()
        return render_template("index.html", tasks=tasks)

    @app.post("/add")
    def add_task():
        title = request.form.get("title", "").strip()
        if title and len(title) <= MAX_TITLE_LENGTH:
            db = get_db()
            with db:
                db.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
            TASKS_ADDED.inc()
        return redirect(url_for("index"))

    @app.post("/<int:task_id>/complete")
    def complete_task(task_id):
        db = get_db()
        with db:
            db.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        return redirect(url_for("index"))

    @app.post("/<int:task_id>/delete")
    def delete_task(task_id):
        db = get_db()
        with db:
            db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return redirect(url_for("index"))

    return app
