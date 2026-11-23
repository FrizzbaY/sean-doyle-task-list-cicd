from prometheus_client import REGISTRY


def value(name, labels=None):
    # Reads one number from the metrics. Returns 0 if it does not exist yet.
    # The counters are shared by all tests, so each test compares before and after
    return REGISTRY.get_sample_value(name, labels or {}) or 0.0


def test_metrics_endpoint_returns_prometheus_text(client):
    # The /metrics page loads and is in the text format Prometheus reads
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")
    assert b"http_requests_total" in response.data


def test_request_is_counted_with_method_endpoint_and_status(client):
    # One visit to the home page adds 1 to the request count for GET / 200
    labels = {"method": "GET", "endpoint": "/", "status": "200"}
    before = value("http_requests_total", labels)
    client.get("/")
    assert value("http_requests_total", labels) == before + 1


def test_endpoint_label_is_the_route_pattern(client):
    # Task 1 and task 2 are counted under one label, not one label per task id
    labels = {
        "method": "POST",
        "endpoint": "/<int:task_id>/complete",
        "status": "302",
    }
    before = value("http_requests_total", labels)
    client.post("/1/complete")
    client.post("/2/complete")
    assert value("http_requests_total", labels) == before + 2


def test_unknown_path_uses_the_unmatched_label(client):
    # A page that does not exist is counted under the fixed label "unmatched"
    labels = {"method": "GET", "endpoint": "unmatched", "status": "404"}
    before = value("http_requests_total", labels)
    client.get("/no-such-page")
    assert value("http_requests_total", labels) == before + 1


def test_metrics_endpoint_is_not_counted(client):
    # Visits to /metrics are not counted, so Prometheus reading it adds no requests
    client.get("/metrics")
    client.get("/metrics")
    labels = {"method": "GET", "endpoint": "/metrics", "status": "200"}
    assert REGISTRY.get_sample_value("http_requests_total", labels) is None


def test_request_duration_is_recorded(client):
    # One visit to the home page adds 1 to the number of timed requests
    labels = {"method": "GET", "endpoint": "/"}
    before = value("http_request_duration_seconds_count", labels)
    client.get("/")
    assert value("http_request_duration_seconds_count", labels) == before + 1


def test_tasks_added_counts_only_accepted_titles(client):
    # A valid title adds 1 to the task count. A blank title adds nothing.
    before = value("tasks_added_total")
    client.post("/add", data={"title": "Buy milk"})
    client.post("/add", data={"title": "   "})
    assert value("tasks_added_total") == before + 1