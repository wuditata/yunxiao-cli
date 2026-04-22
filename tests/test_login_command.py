import json
import os
import tempfile
import unittest
from unittest.mock import patch

from tests import run_cli_json
from yunxiao_cli.domain.store import Store


class FakeResponse:
    def __init__(self, payload: dict | list, status_code: int = 200):
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self):
        return self._payload


class LoginCommandTest(unittest.TestCase):
    @patch("requests.request")
    def test_login_token_saves_account_and_returns_org_projects(self, request_mock):
        requested_urls = []

        def request_side_effect(method, url, **kwargs):
            requested_urls.append(url)
            if url.endswith("/oapi/v1/platform/user"):
                return FakeResponse({"id": "user-1", "name": "Alice"})
            if url.endswith("/oapi/v1/platform/organizations"):
                return FakeResponse([{"id": "org-1", "name": "FOXHIS"}, {"id": "org-2", "name": "LAB"}])
            if method == "POST" and url.endswith("/oapi/v1/projex/organizations/org-1/projects:search"):
                return FakeResponse([{"id": "proj-1", "name": "AI 项目"}])
            if method == "POST" and url.endswith("/oapi/v1/projex/organizations/org-2/projects:search"):
                return FakeResponse([{"id": "proj-2", "name": "测试项目"}])
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(["login", "token", "abc", "--account", "pm-a"])

            store = Store(root=temp_dir)
            account = store.get_account("pm-a")
            profiles = store.list_profiles()
            default_profile_name = store.get_default_profile_name()

        self.assertTrue(result["success"])
        self.assertIsNone(result["profile"])
        self.assertEqual("pm-a", result["data"]["account"]["name"])
        self.assertEqual("FOXHIS", result["data"]["organizations"][0]["name"])
        self.assertEqual("proj-2", result["data"]["projects"]["org-2"][0]["id"])
        self.assertEqual("Alice", account.user["name"])
        self.assertEqual([], profiles)
        self.assertIsNone(default_profile_name)
        self.assertTrue(account.cache_invalidated)
        self.assertEqual(
            [
                "https://openapi-rdc.aliyuncs.com/oapi/v1/platform/user",
                "https://openapi-rdc.aliyuncs.com/oapi/v1/platform/organizations",
                "https://openapi-rdc.aliyuncs.com/oapi/v1/projex/organizations/org-1/projects:search",
                "https://openapi-rdc.aliyuncs.com/oapi/v1/projex/organizations/org-2/projects:search",
            ],
            requested_urls,
        )

    @patch("requests.request")
    def test_login_token_keeps_success_when_one_org_project_query_fails(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/oapi/v1/platform/user"):
                return FakeResponse({"id": "user-1", "name": "Alice"})
            if url.endswith("/oapi/v1/platform/organizations"):
                return FakeResponse([{"id": "org-1", "name": "FOXHIS"}, {"id": "org-2", "name": "LAB"}])
            if method == "POST" and url.endswith("/oapi/v1/projex/organizations/org-1/projects:search"):
                return FakeResponse([{"id": "proj-1", "name": "AI 项目"}])
            if method == "POST" and url.endswith("/oapi/v1/projex/organizations/org-2/projects:search"):
                return FakeResponse({"errorCode": "NotFound", "errorMessage": "Not Found"}, status_code=404)
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(["login", "token", "abc", "--account", "pm-a"])

        self.assertTrue(result["success"])
        self.assertEqual("proj-1", result["data"]["projects"]["org-1"][0]["id"])
        self.assertEqual([], result["data"]["projects"]["org-2"])
        self.assertIn("org-2", result["warnings"][0])


if __name__ == "__main__":
    unittest.main()
