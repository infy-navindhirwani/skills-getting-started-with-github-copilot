"""
Tests for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Create a test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"]


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities(self):
        """Test fetching all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that activities are returned
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check structure of an activity
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_specific_activity(self):
        """Test that Chess Club activity exists"""
        response = client.get("/activities")
        data = response.json()
        
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity(self, reset_activities):
        """Test signing up for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" in activities_data["Basketball Team"]["participants"]

    def test_signup_duplicate_email(self, reset_activities):
        """Test that duplicate signups are rejected"""
        # Sign up first time
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Try to sign up again with same email
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_from_activity(self, reset_activities):
        """Test unregistering a participant from an activity"""
        # First, sign up
        client.post(
            "/activities/Drama Club/signup",
            params={"email": "drama_student@mergington.edu"}
        )
        
        # Verify signup
        activities_response = client.get("/activities")
        assert "drama_student@mergington.edu" in activities_response.json()["Drama Club"]["participants"]
        
        # Now unregister
        response = client.post(
            "/activities/Drama Club/unregister",
            params={"email": "drama_student@mergington.edu"}
        )
        
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert "drama_student@mergington.edu" not in activities_response.json()["Drama Club"]["participants"]

    def test_unregister_not_signed_up(self, reset_activities):
        """Test unregistering someone who isn't signed up"""
        response = client.post(
            "/activities/Tennis Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
