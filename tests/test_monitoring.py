from fastapi.testclient import (
    TestClient,
)

from app.main import app

client = TestClient(
    app
)


def test_metrics_endpoint_available(
) -> None:
    response = client.get(
        "/metrics"
    )

    assert response.status_code == 200

    assert (
        "python_info"
        in response.text
    )


def test_http_request_metrics_recorded(
) -> None:
    response = client.get(
        "/docs"
    )

    assert response.status_code == 200

    metrics_response = client.get(
        "/metrics"
    )

    assert (
        metrics_response.status_code
        == 200
    )

    body = metrics_response.text

    assert (
        "chargeops_http_requests_total"
        in body
    )

    assert (
        "chargeops_http_request_duration_seconds"
        in body
    )

    assert (
        'method="GET"'
        in body
    )


def test_metrics_not_in_openapi(
) -> None:
    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200

    paths = response.json()[
        "paths"
    ]

    assert "/metrics" not in paths