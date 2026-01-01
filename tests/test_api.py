import pytest
from fastapi.testclient import TestClient


def test_root_redirect(client):
    """Test that root path redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    activities = response.json()
    assert isinstance(activities, dict)
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert "Basketball Team" in activities
    
    # Verify activity structure
    chess = activities["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess
    assert isinstance(chess["participants"], list)


def test_signup_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Basketball%20Team/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "message" in result
    assert "newstudent@mergington.edu" in result["message"]
    assert "Basketball Team" in result["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "newstudent@mergington.edu" in activities["Basketball Team"]["participants"]


def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    response = client.post(
        "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    
    result = response.json()
    assert "Activity not found" in result["detail"]


def test_signup_duplicate_participant(client):
    """Test that same student cannot signup twice"""
    email = "michael@mergington.edu"
    
    response = client.post(
        f"/activities/Chess%20Club/signup?email={email}"
    )
    assert response.status_code == 400
    
    result = response.json()
    assert "already signed up" in result["detail"]


def test_unregister_success(client):
    """Test successful unregistration from activity"""
    email = "michael@mergington.edu"
    
    # Verify participant exists
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities["Chess Club"]["participants"]
    
    # Unregister
    response = client.post(
        f"/activities/Chess%20Club/unregister?email={email}"
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "Unregistered" in result["message"]
    assert email in result["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_activity_not_found(client):
    """Test unregister for non-existent activity"""
    response = client.post(
        "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
    )
    assert response.status_code == 404
    
    result = response.json()
    assert "Activity not found" in result["detail"]


def test_unregister_participant_not_found(client):
    """Test unregister when participant is not in activity"""
    response = client.post(
        "/activities/Basketball%20Team/unregister?email=notmember@mergington.edu"
    )
    assert response.status_code == 400
    
    result = response.json()
    assert "not signed up" in result["detail"]


def test_signup_multiple_students(client):
    """Test signing up multiple students for same activity"""
    activity = "Soccer Club"
    emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
    
    for email in emails:
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
    
    # Verify all were added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    for email in emails:
        assert email in activities[activity]["participants"]


def test_signup_and_unregister_flow(client):
    """Test complete flow of signing up and then unregistering"""
    activity = "Art Club"
    email = "testuser@mergington.edu"
    
    # Initially not registered
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity]["participants"]
    
    # Sign up
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200
    
    # Verify registered
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]
    
    # Unregister
    response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200
    
    # Verify unregistered
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity]["participants"]


def test_participants_count(client):
    """Test that participant count is accurate"""
    activity = "Programming Class"
    
    activities_response = client.get("/activities")
    activities = activities_response.json()
    initial_count = len(activities[activity]["participants"])
    
    # Sign up new student
    email = "newprogrammer@mergington.edu"
    client.post(f"/activities/{activity}/signup?email={email}")
    
    # Verify count increased
    activities_response = client.get("/activities")
    activities = activities_response.json()
    new_count = len(activities[activity]["participants"])
    assert new_count == initial_count + 1
