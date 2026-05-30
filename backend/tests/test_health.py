def test_health_check(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.1.0"
