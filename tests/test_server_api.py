import unittest
from unittest.mock import patch

from auth.login import Session
from server import app
from services.academic import ServiceResult


class ServerApiTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    def authenticate_as(self, role="teacher"):
        identity = {
            "user_id": 1,
            "username": "test-user",
            "role": role,
            "teacher_id": 1 if role == "teacher" else None,
            "student_id": 2 if role == "student" else None,
        }
        with self.client.session_transaction() as browser_session:
            browser_session["identity"] = identity

    def test_homepage_uses_template_and_static_asset_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ScholarSync", response.data)
        asset_response = self.client.get("/assets/logo.png")
        self.assertEqual(asset_response.status_code, 200)
        asset_response.close()

    def test_student_list_requires_teacher_authentication(self):
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 401)

        self.authenticate_as("student")
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 403)

    @patch("server.academic.list_students")
    def test_student_list_returns_named_json_records(self, list_students):
        self.authenticate_as()
        list_students.return_value = ServiceResult(
            True,
            data=[(4, "12A-04", "Ada", "Lovelace", "ada@example.com", None, 2, "12A", "s_ada")],
        )

        response = self.client.get("/api/students")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"][0]["student_id"], 4)
        self.assertEqual(response.get_json()["data"][0]["class_name"], "12A")

    @patch("server.academic.create_student")
    def test_student_create_returns_created_status(self, create_student):
        self.authenticate_as()
        create_student.return_value = ServiceResult(True, data={"student_id": 17})

        response = self.client.post("/api/students", json={"username": "new-student"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["data"]["student_id"], 17)

    @patch("server.authenticate_user")
    def test_login_creates_session_and_logout_clears_it(self, authenticate):
        authenticate.return_value = Session(1, "teacher-user", "teacher", teacher_id=1)

        response = self.client.post(
            "/api/auth/login",
            json={"username": "teacher-user", "password": "valid-password", "role": "teacher"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").get_json()["data"]["role"], "teacher")
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_invalid_create_payload_returns_json_error(self):
        self.authenticate_as()
        response = self.client.post("/api/students", data="not-json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "A JSON object is required.")

    def test_unhashable_role_is_rejected_as_invalid_json_input(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "teacher-user", "password": "valid-password", "role": []},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
