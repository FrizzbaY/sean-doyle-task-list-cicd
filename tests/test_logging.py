import json
import logging

from app import JsonFormatter


def test_request_is_logged_with_fields(client, caplog):
    with caplog.at_level(logging.INFO, logger="task_list"):
        client.get("/")
    record = caplog.records[-1]
    assert record.fields["method"] == "GET"
    assert record.fields["endpoint"] == "/"
    assert record.fields["status"] == 200


def test_metrics_requests_are_not_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="task_list"):
        client.get("/metrics")
    assert caplog.records == []


def test_formatter_writes_one_line_of_structured_text(client, caplog):
    with caplog.at_level(logging.INFO, logger="task_list"):
        client.get("/")
    entry = json.loads(JsonFormatter().format(caplog.records[-1]))
    assert entry["message"] == "request"
    assert entry["status"] == 200
