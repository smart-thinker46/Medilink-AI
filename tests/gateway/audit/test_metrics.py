from medilink_ai.gateway.monitoring.metrics import InMemoryGatewayMetrics


def test_metrics_are_bounded_by_explicit_labels():
    metrics = InMemoryGatewayMetrics()
    metrics.increment("medilink_ai_requests_total", labels={"capability": "knowledge.ask"})
    metrics.observe("medilink_ai_request_duration_seconds", 0.25, labels={"stage": "AUTHORIZATION"})
    assert list(metrics.counters.values()) == [1]
    assert list(metrics.observations.values()) == [[0.25]]
