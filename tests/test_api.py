import pytest


class TestRoot:
    """Test root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test activities retrieval endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_activity_initial_participants(self, client):
        """Test that activities have expected initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]


class TestSignup:
    """Test signup endpoint"""
    
    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up newstudent@mergington.edu for Chess Club" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup adds participant to activity"""
        # Signup a student
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Chess Club"]["participants"]
    
    def test_duplicate_signup(self, client):
        """Test that duplicate signup fails"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_at_capacity(self, client):
        """Test signup when activity is at capacity"""
        # Create a full activity by adding participants up to max
        response = client.get("/activities")
        data = response.json()
        
        # Tennis Club has max 10, currently has 2
        # Add 8 more to reach capacity
        for i in range(8):
            client.post(
                f"/activities/Tennis Club/signup?email=student{i}@mergington.edu"
            )
        
        # Try to signup when at capacity
        response = client.post(
            "/activities/Tennis Club/signup?email=fullstudent@mergington.edu"
        )
        assert response.status_code == 400
        assert "capacity" in response.json()["detail"]


class TestUnregister:
    """Test unregister endpoint"""
    
    def test_successful_unregister(self, client):
        """Test successful unregister from an activity"""
        response = client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered michael@mergington.edu from Chess Club" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister removes participant from activity"""
        # Unregister a student
        client.post("/activities/Chess Club/unregister?email=michael@mergington.edu")
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
    
    def test_unregister_not_registered(self, client):
        """Test unregister fails for student not registered"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_reopens_spot(self, client):
        """Test that unregistering reopens a spot in activity"""
        # Fill activity to capacity
        for i in range(8):
            client.post(
                f"/activities/Tennis Club/signup?email=student{i}@mergington.edu"
            )
        
        # Verify at capacity
        response = client.get("/activities")
        data = response.json()
        assert len(data["Tennis Club"]["participants"]) == 10
        
        # Unregister someone
        client.post("/activities/Tennis Club/unregister?email=lucas@mergington.edu")
        
        # Verify spot is available
        response = client.post(
            "/activities/Tennis Club/signup?email=newspot@mergington.edu"
        )
        assert response.status_code == 200


class TestIntegration:
    """Integration tests"""
    
    def test_signup_and_unregister_flow(self, client):
        """Test complete signup and unregister flow"""
        test_email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={test_email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        data = response.json()
        assert test_email in data[activity]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister?email={test_email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        data = response.json()
        assert test_email not in data[activity]["participants"]
    
    def test_multiple_activities_signup(self, client):
        """Test student can signup for multiple activities"""
        student = "multi@mergington.edu"
        
        # Sign up for multiple activities
        response1 = client.post(
            f"/activities/Chess Club/signup?email={student}"
        )
        response2 = client.post(
            f"/activities/Programming Class/signup?email={student}"
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify in both activities
        response = client.get("/activities")
        data = response.json()
        assert student in data["Chess Club"]["participants"]
        assert student in data["Programming Class"]["participants"]
