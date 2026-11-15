import os
import sqlite3

from flask import Flask, g, redirect, render_template, request, url_for

MAX_TITLE_LENGTH = 200

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
