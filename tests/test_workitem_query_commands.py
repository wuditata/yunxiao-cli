import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import run_cli_json
from yunxiao_cli.domain.models import AccountConfig, ProfileConfig, MetaCache
from yunxiao_cli.domain.store import Store


class FakeResponse:
    def __init__(self, payload: dict | list, status_code: int = 200):
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self):
        return self._payload


def seed_store(root: Path) -> Store:
    store = Store(root=root)
    store.save_account(
        AccountConfig(
            name="pm-a",
            token="token-a",
            user={"id": "user-1"},
            organizations=[{"id": "123", "name": "FOXHIS"}],
        )
    )
    store.save_profile(ProfileConfig(name="pm-dev", account="pm-a", org="123", project="456"))
    store.set_default_profile("pm-dev")
    store.save_meta_cache(
        MetaCache(
            account="pm-a",
            org="123",
            project="456",
            project_info={"id": "456", "name": "AI 项目"},
            workitem_types=[
                {"id": "req-type", "categoryId": "Req", "defaultType": True, "name": "产品需求"},
                {"id": "task-type", "categoryId": "Task", "defaultType": True, "name": "任务"},
            ],
            statuses={
                "req-type": [{"id": "req-new", "name": "需求创建", "displayName": "需求创建"}],
                "task-type": [{"id": "task-dev", "name": "功能开发", "displayName": "功能开发"}],
            },
            fields={"req-type": [{"id": "field-subject", "name": "标题"}], "task-type": []},
            members=[{"id": "member-1", "userId": "user-1", "name": "Alice"}],
            updated_at="2099-01-01T00:00:00+00:00",
            ttl_seconds=3600,
            invalidated=False,
        )
    )
    return store


class WorkitemQueryCommandsTest(unittest.TestCase):
    @patch("requests.request")
    def test_workitem_create_uses_default_type_from_category(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems"):
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "1001", "subject": kwargs["json"]["subject"]})
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    ["workitem", "create", "--profile", "pm-dev", "--category", "Req", "--subject", "支持 CLI"]
                )

        self.assertTrue(result["success"])
        self.assertEqual("req-type", captured["payload"]["workitemTypeId"])

    @patch("requests.request")
    def test_workitem_get_and_search_use_profile_cache(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001/comments"):
                return FakeResponse([{"id": "comment-1"}])
            if url.endswith("/workitems/9001"):
                return FakeResponse({"id": "9001", "subject": "父需求"})
            if url.endswith("/workitems/1001"):
                return FakeResponse(
                    {
                        "id": "1001",
                        "subject": "子任务",
                        "parentId": "9001",
                        "attachments": [{"id": "file-1"}],
                        "description": "![图1](https://img.example.com/1.png)",
                    }
                )
            if url.endswith("/workitems:search"):
                payload = json.loads(kwargs["json"]["conditions"])
                self.assertEqual("task-dev", payload["conditionGroups"][0][1]["value"][0])
                return FakeResponse([{"id": "1001", "subject": "子任务"}])
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                get_result = run_cli_json(
                    [
                        "workitem",
                        "get",
                        "1001",
                        "--profile",
                        "pm-dev",
                        "--with-parent",
                    ]
                )
                search_result = run_cli_json(
                    ["workitem", "search", "--profile", "pm-dev", "--category", "Task", "--status", "功能开发"]
                )

        self.assertEqual("comment-1", get_result["data"]["comments"][0]["id"])
        self.assertEqual("file-1", get_result["data"]["attachments"][0]["id"])
        self.assertEqual("https://img.example.com/1.png", get_result["data"]["description_images"][0])
        self.assertEqual("9001", get_result["data"]["parent"]["id"])
        self.assertEqual("1001", search_result["data"]["items"][0]["id"])

    @patch("requests.request")
    def test_workitem_mine_filters_assigned_to_self(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems:search"):
                category = kwargs["json"]["category"]
                payload = {
                    "Req": [{"id": "req-1", "assignedTo": "user-1"}],
                    "Task": [{"id": "task-1", "assignedTo": "user-2"}],
                    "Bug": [{"id": "bug-1", "assignedTo": {"userId": "user-1"}}],
                }
                return FakeResponse(payload[category])
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(["workitem", "mine", "--profile", "pm-dev"])

        self.assertTrue(result["success"])
        self.assertEqual(2, result["data"]["total"])
        self.assertEqual({"req-1", "bug-1"}, {item["id"] for item in result["data"]["items"]})


if __name__ == "__main__":
    unittest.main()
