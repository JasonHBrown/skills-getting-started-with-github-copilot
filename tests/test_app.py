import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    return TestClient(app)


# ── GET / ────────────────────────────────────────────────────────────────

class TestRootRedirect:
    def test_redirects_to_index(self, client):
        # Arrange
        expected_url = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_url


# ── GET /activities ──────────────────────────────────────────────────────

class TestGetActivities:
    def test_returns_all_activities(self, client):
        # Arrange
        expected_count = len(activities)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_count

    def test_activity_has_expected_fields(self, client):
        # Arrange
        required_keys = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        for name, details in data.items():
            assert required_keys.issubset(details.keys()), f"{name} missing keys"


# ── POST /activities/{name}/signup ───────────────────────────────────────

class TestSignup:
    def test_signup_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
        assert "Signed up" in response.json()["message"]

    def test_signup_activity_not_found(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_adds_only_one_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "unique@mergington.edu"
        count_before = len(activities[activity_name]["participants"])

        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert len(activities[activity_name]["participants"]) == count_before + 1


# ── DELETE /activities/{name}/unregister ─────────────────────────────────

class TestUnregister:
    def test_unregister_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
        assert "Unregistered" in response.json()["message"]

    def test_unregister_activity_not_found(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_removes_only_one_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]
        count_before = len(activities[activity_name]["participants"])

        # Act
        client.delete(f"/activities/{activity_name}/unregister?email={email}")

        # Assert
        assert len(activities[activity_name]["participants"]) == count_before - 1
