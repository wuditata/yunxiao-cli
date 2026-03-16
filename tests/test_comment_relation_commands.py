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
                {"id": "bug-type", "categoryId": "Bug", "defaultType": True, "name": "缺陷"},
            ],
            statuses={},
            fields={},
            members=[],
            updated_at="2099-01-01T00:00:00+00:00",
            ttl_seconds=3600,
            invalidated=False,
        )
    )


class CommentRelationCommandsTest(unittest.TestCase):
    @patch("requests.request")
    def test_comment_add_and_list(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001/comments") and method == "POST":
                return FakeResponse({"id": "comment-1", "content": kwargs["json"]["content"]})
            if url.endswith("/workitems/1001/comments") and method == "GET":
                return FakeResponse([{"id": "comment-1", "content": "请评审"}])
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                add_result = run_cli_json(
                    ["comment", "add", "--profile", "pm-dev", "--workitem", "1001", "--content", "请评审"]
                )
                list_result = run_cli_json(
                    ["comment", "list", "--profile", "pm-dev", "--workitem", "1001"]
                )

        self.assertTrue(add_result["success"])
        self.assertEqual("comment-1", add_result["data"]["comment"]["id"])
        self.assertEqual("comment-1", list_result["data"]["comments"][0]["id"])

    @patch("requests.request")
    def test_relation_add_links_parent_and_child(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/2001/relationRecords") and method == "POST":
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "rel-1", "relationType": "PARENT", "workitemId": "1001"})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    ["relation", "add", "--profile", "pm-dev", "--parent", "1001", "--child", "2001"]
                )

        self.assertTrue(result["success"])
        self.assertEqual({"relationType": "PARENT", "workitemId": "1001"}, captured["payload"])

    @patch("requests.request")
    def test_relation_children_searches_all_categories(self, request_mock):
        calls = []

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems:search") and method == "POST":
                calls.append(kwargs["json"]["category"])
                if kwargs["json"]["category"] == "Task":
                    return FakeResponse([{"id": "2001", "subject": "子任务"}])
                return FakeResponse([])
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    ["relation", "children", "--profile", "pm-dev", "--parent", "1001"]
                )

        self.assertTrue(result["success"])
        self.assertEqual(["Req", "Task", "Bug"], calls)
        self.assertEqual("2001", result["data"]["children"][0]["id"])


if __name__ == "__main__":
    unittest.main()
