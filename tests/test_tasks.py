def test_index_shows_empty_message(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"No tasks yet." in response.data