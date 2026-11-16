import pytest

from app import MAX_TITLE_LENGTH


def add_task(client, title):
    return client.post("/add", data={"title": title}, follow_redirects=True)


def test_index_shows_empty_message(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"No tasks yet." in response.data


def test_add_task_redirects_to_index(client):
    response = client.post("/add", data={"title": "Buy milk"})
    assert response.status_code == 302


def test_add_task_appears_in_list(client):
    response = add_task(client, "Buy milk")
    assert b"Buy milk" in response.data
    assert b"No tasks yet." not in response.data


@pytest.mark.parametrize("title", ["", "   "])
def test_add_blank_title_is_ignored(client, title):
    response = add_task(client, title)
    assert b"No tasks yet." in response.data


def test_add_title_at_maximum_length_is_accepted(client):
    response = add_task(client, "x" * MAX_TITLE_LENGTH)
    assert b"x" * MAX_TITLE_LENGTH in response.data


def test_add_title_over_maximum_length_is_ignored(client):
    response = add_task(client, "x" * (MAX_TITLE_LENGTH + 1))
    assert b"No tasks yet." in response.data


def test_complete_task_marks_it_completed(client):
    add_task(client, "Buy milk")
    response = client.post("/1/complete", follow_redirects=True)
    assert b'class="task completed"' in response.data
    assert b'class="complete-task"' not in response.data


def test_delete_task_removes_it(client):
    add_task(client, "Buy milk")
    response = client.post("/1/delete", follow_redirects=True)
    assert b"Buy milk" not in response.data
    assert b"No tasks yet." in response.data


@pytest.mark.parametrize("path", ["/999/complete", "/999/delete"])
def test_unknown_task_id_redirects_without_error(client, path):
    response = client.post(path)
    assert response.status_code == 302