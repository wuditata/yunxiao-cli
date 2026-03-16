import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import run_cli_json
from yunxiao_cli.domain.models import AccountConfig
from yunxiao_cli.domain.store import Store


class FakeResponse:
    def __init__(self, payload: dict | list, status_code: int = 200):
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self):
        return self._payload


class ProfileCommandTest(unittest.TestCase):
    @patch("requests.request")
    def test_profile_add_creates_meta_cache(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/projects/456"):
                return FakeResponse({"id": "456", "name": "AI 项目"})
            if url.endswith("/projects/456/workitemTypes"):
                category = kwargs["params"]["category"]
                payload = {
                    "Req": [{"id": "req-type", "categoryId": "Req", "defaultType": True, "name": "产品需求"}],
                    "Task": [{"id": "task-type", "categoryId": "Task", "defaultType": True, "name": "任务"}],
                    "Bug": [{"id": "bug-type", "categoryId": "Bug", "defaultType": True, "name": "缺陷"}],
                }
                return FakeResponse(payload[category])
            if url.endswith("/workitemTypes/req-type/workflows"):
                return FakeResponse({"statuses": [{"id": "req-new", "name": "需求创建", "displayName": "需求创建"}]})
            if url.endswith("/workitemTypes/task-type/workflows"):
                return FakeResponse({"statuses": [{"id": "task-dev", "name": "功能开发", "displayName": "功能开发"}]})
            if url.endswith("/workitemTypes/bug-type/workflows"):
                return FakeResponse({"statuses": [{"id": "bug-new", "name": "待修复", "displayName": "待修复"}]})
            if url.endswith("/workitemTypes/req-type/fields"):
                return FakeResponse([{"id": "field-subject", "name": "标题"}])
            if url.endswith("/workitemTypes/task-type/fields"):
                return FakeResponse([{"id": "field-owner", "name": "负责人"}])
            if url.endswith("/workitemTypes/bug-type/fields"):
                return FakeResponse([{"id": "field-severity", "name": "严重程度"}])
            if "/platform/organizations/123/members" in url:
                return FakeResponse([{"id": "member-1", "userId": "user-1", "name": "Alice"}])
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            store = Store(root=Path(temp_dir))
            store.save_account(
                AccountConfig(
                    name="pm-a",
                    token="token-a",
                    user={"id": "user-1", "name": "Alice"},
                    organizations=[{"id": "123", "name": "FOXHIS"}],
                )
            )
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    ["profile", "add", "pm-dev", "--account", "pm-a", "--org", "123", "--project", "456"]
                )

            profile = store.get_profile("pm-dev")
            cache = store.get_meta_cache("pm-a", "123", "456")

        self.assertTrue(result["success"])
        self.assertEqual("AI 项目", profile.project_ref["name"])
        self.assertIn("task-type", cache.statuses)
        self.assertEqual("Alice", cache.members[0]["name"])


if __name__ == "__main__":
    unittest.main()
