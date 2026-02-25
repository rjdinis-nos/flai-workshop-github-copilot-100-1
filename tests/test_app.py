import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Snapshot of the original activities data taken at import time
_ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore activities to their original state before each test."""
    activities.clear()
    activities.update(copy.deepcopy(_ORIGINAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestRoot:
    def test_redirect_to_index(self, client):
        # Arrange
        url = "/"

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code in (302, 307)
        assert response.headers["location"].endswith("/static/index.html")


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        # Arrange
        url = "/activities"

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200

    def test_returns_dict(self, client):
        # Arrange
        url = "/activities"

        # Act
        response = client.get(url)

        # Assert
        assert isinstance(response.json(), dict)

    def test_contains_known_activities(self, client):
        # Arrange
        url = "/activities"

        # Act
        data = client.get(url).json()

        # Assert
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_has_expected_fields(self, client):
        # Arrange
        url = "/activities"

        # Act
        chess = client.get(url).json()["Chess Club"]

        # Assert
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_signup_adds_participant(self, client):
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        client.post(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        participants = client.get("/activities").json()[activity]["participants"]
        assert email in participants

    def test_signup_unknown_activity_returns_404(self, client):
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_returns_400(self, client):
        # Arrange — michael@mergington.edu is already in Chess Club by default
        activity = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self, client):
        # Arrange — michael@mergington.edu is a default Chess Club participant
        activity = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        # Arrange — michael@mergington.edu is a default Chess Club participant
        activity = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        client.delete(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        participants = client.get("/activities").json()[activity]["participants"]
        assert email not in participants

    def test_unregister_unknown_activity_returns_404(self, client):
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up_returns_404(self, client):
        # Arrange
        activity = "Chess Club"
        email = "ghost@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student is not signed up for this activity"
