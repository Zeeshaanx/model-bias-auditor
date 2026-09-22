async def test_end_to_end_audit_with_mock_target(client):
    target = await client.post(
        "/api/v1/targets",
        json={"name": "Mock model", "provider": "mock", "model_name": "mock-model"},
    )
    assert target.status_code == 201
    target_id = target.json()["id"]

    audit = await client.post(
        "/api/v1/audits",
        json={
            "name": "Baseline fairness sweep",
            "target_id": target_id,
            "probe_ids": [],
            "evaluator_id": "composite-disparity",
        },
    )
    assert audit.status_code == 201
    audit_id = audit.json()["id"]
    assert len(audit.json()["probe_ids"]) >= 10

    run = await client.post(f"/api/v1/audits/{audit_id}/run")
    assert run.status_code == 200
    summary = run.json()
    assert summary["status"] == "completed"
    assert summary["probes_run"] >= 10

    results = await client.get(f"/api/v1/audits/{audit_id}/results")
    assert results.status_code == 200
    assert len(results.json()) == summary["probes_run"]

    findings = await client.get(f"/api/v1/audits/{audit_id}/findings")
    assert findings.status_code == 200
    assert len(findings.json()) == summary["findings"]

    for report_format in ("json", "markdown", "html"):
        report = await client.post("/api/v1/reports", json={"audit_id": audit_id, "format": report_format})
        assert report.status_code == 201
        assert report.json()["content"]

    dashboard = await client.get("/api/v1/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["audits"] == 1


async def test_standalone_probe_run(client):
    response = await client.post(
        "/api/v1/probes/us-hiring-summary-race-male/run",
        json={"provider": "mock", "model_name": "mock-model"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["prompts"]) == 2
    assert body["evaluation"]["evaluator_id"] == "composite-disparity"
