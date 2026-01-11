class TestPatternAnalysisAPI:

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_analyze_patterns_without_data(self, client):
        response = client.post(
            "/api/v1/patterns/analyze",
            json={"user_id": 1, "days": 30},
        )
        assert response.status_code == 400




    def test_get_user_patterns_success(self, client):
        client.post(
            "/api/v1/patterns/analyze",
            json={"user_id": 1, "days": 30},
        )

        response = client.get("/api/v1/patterns/1/patterns")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_user_personality_not_found(self, client):
        response = client.get("/api/v1/patterns/1/personality")
        assert response.status_code == 404

    def test_analyze_patterns_invalid_days(self, client):
        response = client.post(
            "/api/v1/patterns/analyze",
            json={"user_id": 1, "days": 5},
        )

        assert response.status_code == 422

