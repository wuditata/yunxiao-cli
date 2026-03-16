import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import run_cli_json
from yunxiao_cli.domain.models import AccountConfig, ProfileConfig
from yunxiao_cli.domain.store import Store


class FakeResponse:
    def __init__(self, payload: dict | list, status_code: int = 200):
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self):
        return self._payload


def seed_store(root: Path) -> None:
    store = Store(root=root)
    store.save_account(
        AccountConfig(
            name="pm-a",
            token="token-a",
            user={"id": "user-1"},
            organizations=[{"id": "123", "name": "FOXHIS"}],
        )
    )
    store.save_profile(ProfileConfig(name="default", account="pm-a", org="123", project="456"))
    store.set_default_profile("default")


class MetaProjectCommandsTest(unittest.TestCase):
    @patch("requests.request")
    def test_meta_reload_works_with_default_profile(self, request_mock):
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
                return FakeResponse({"statuses": [{"id": "req-new", "name": "需求创建"}]})
            if url.endswith("/workitemTypes/task-type/workflows"):
                return FakeResponse({"statuses": [{"id": "task-dev", "name": "功能开发"}]})
            if url.endswith("/workitemTypes/bug-type/workflows"):
                return FakeResponse({"statuses": [{"id": "bug-new", "name": "待修复"}]})
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
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(["meta", "reload"])

        self.assertTrue(result["success"])
        self.assertEqual("AI 项目", result["data"]["meta"]["project_info"]["name"])

    @patch("requests.request")
    def test_project_list_and_get(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/projex/organizations/123/projects"):
                return FakeResponse(
                    [
                        {"id": "456", "name": "AI 项目"},
                        {"id": "457", "name": "测试项目"},
                    ]
                )
            if url.endswith("/projex/organizations/123/projects/456"):
                return FakeResponse({"id": "456", "name": "AI 项目"})
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                list_result = run_cli_json(["project", "list"])
                get_result = run_cli_json(["project", "get"])

        self.assertTrue(list_result["success"])
        self.assertEqual("457", list_result["data"]["projects"][1]["id"])
        self.assertEqual("AI 项目", get_result["data"]["project"]["name"])


if __name__ == "__main__":
    unittest.main()
