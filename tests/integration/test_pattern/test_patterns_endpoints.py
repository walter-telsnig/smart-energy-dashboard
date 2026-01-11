# tests/test_api_endpoints.py - UPDATE ALL URLS
class TestPatternAnalysisAPI:
    
    def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        # Your app has health at root level, not in patterns router
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_analyze_patterns_success(self, test_client, seed_test_data):
        """Test successful pattern analysis"""
        request_data = {
            "user_id": 1,
            "days": 30
        }
        
        response = test_client.post(
            "/api/v1/patterns/analyze",  # ← CORRECT PATH!
            json=request_data
        )
        
        print(f"Response: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == 1
        assert "patterns" in data
        assert "personality" in data
    
    def test_get_user_patterns_success(self, test_client, seed_test_data):
        """Test retrieving user patterns"""
        # First analyze to create patterns
        test_client.post(
            "/api/v1/patterns/analyze",
            json={"user_id": 1, "days": 30}
        )
        
        # Then get patterns
        response = test_client.get("/api/v1/patterns/1/patterns")  # ← CORRECT PATH!
        
        assert response.status_code == 200
        patterns = response.json()
        assert isinstance(patterns, list)
    
    def test_get_user_personality_success(self, test_client, seed_test_data):
        """Test retrieving user personality"""
        # First analyze
        test_client.post(
            "/api/v1/patterns/analyze",
            json={"user_id": 1, "days": 30}
        )

        # Then get personality
        response = test_client.get("/api/v1/patterns/1/personality")

        assert response.status_code == 200
        personality = response.json()
        assert "personality_type" in personality
        assert "score" in personality
    
    def test_analyze_patterns_user_not_found(self, test_client, db_session):
        """Test analysis when no community data exists"""
        from infra.models import Consumption

        db_session.query(Consumption).delete()
        db_session.commit()

        response = test_client.post(
            "/api/v1/patterns/analyze",
            json={"user_id": 999, "days": 30}
        )

        assert response.status_code in [200, 400]

        if response.status_code == 400:
            assert "No consumption data for user" in response.json()["detail"]
    
    def test_analyze_patterns_invalid_days(self, test_client):
        """Test analysis with invalid days parameter"""
        # Days too low (should be validated by Pydantic)
        request_data = {
            "user_id": 1,
            "days": 5  # Below minimum of 7
        }
        
        response = test_client.post(
            "/api/v1/patterns/analyze",
            json=request_data
        )
        
        # Pydantic validation returns 422
        assert response.status_code == 422
    
    # ... update all other tests similarly