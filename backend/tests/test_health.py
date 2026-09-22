async def test_health_reports_registry_sizes(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["probes"] >= 10
    assert body["evaluators"] >= 5
