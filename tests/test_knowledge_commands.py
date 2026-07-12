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


class KnowledgeCommandsTest(unittest.TestCase):
    @patch("requests.request")
    def test_knowledge_context_aggregates_workitem_sources(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001") and method == "GET":
                return FakeResponse({"id": "1001", "subject": "根需求", "parentId": None, "spaceId": "456"})
            if url.endswith("/workitems/1001/comments") and method == "GET":
                return FakeResponse([{"id": "comment-1", "content": "请评审"}])
            if url.endswith("/workitems/1001/attachments") and method == "GET":
                return FakeResponse([{"id": "file-1", "name": "spec.md"}])
            if url.endswith("/workitems:search") and method == "POST":
                self.assertEqual("456", kwargs["json"].get("spaceId"))
                conditions = kwargs["json"].get("conditions") or ""
                if "1001" in str(conditions):
                    return FakeResponse([{"id": "2001", "subject": "子任务", "parentId": "1001"}])
                return FakeResponse([])
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(["knowledge", "context", "1001", "--profile", "pm-dev"])

        self.assertTrue(result["success"])
        self.assertEqual("1001", result["data"]["workitem"]["id"])
        self.assertEqual("comment-1", result["data"]["comments"][0]["id"])
        self.assertEqual("file-1", result["data"]["attachments"][0]["id"])
        self.assertIn("parentChain", result["data"])
        self.assertIn("childrenTree", result["data"])

    @patch("requests.request")
    def test_knowledge_context_resolves_serial_number(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems:search") and method == "POST":
                payload = kwargs["json"]
                if payload.get("category") == "Req" and payload.get("page") == 1:
                    return FakeResponse([{"id": "1001", "serialNumber": "REQ-42", "subject": "根需求"}])
                return FakeResponse([])
            if url.endswith("/workitems/1001") and method == "GET":
                return FakeResponse({"id": "1001", "subject": "根需求", "parentId": None})
            if url.endswith("/workitems/1001/comments") and method == "GET":
                return FakeResponse([])
            if url.endswith("/workitems/1001/attachments") and method == "GET":
                return FakeResponse([])
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(["knowledge", "context", "REQ-42", "--profile", "pm-dev"])

        self.assertTrue(result["success"])
        self.assertEqual("1001", result["data"]["workitem"]["id"])

    @patch("requests.request")
    def test_knowledge_project_summary_counts_categories(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/projects/456") and method == "GET":
                return FakeResponse({"id": "456", "name": "AI 项目"})
            if url.endswith("/sprints") and method == "GET":
                return FakeResponse([{"id": "sprint-1", "name": "迭代一", "status": "DOING"}])
            if url.endswith("/workitems:search") and method == "POST":
                if kwargs["json"].get("category") == "Req":
                    return FakeResponse([{"id": "1001"}, {"id": "1002"}])
                return FakeResponse([])
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(["knowledge", "project-summary", "--profile", "pm-dev"])

        self.assertTrue(result["success"])
        summary = result["data"]["projects"][0]
        self.assertEqual("sprint-1", summary["activeSprints"][0]["id"])
        self.assertEqual({"total": 2, "capped": False}, summary["categoryStats"]["Req"])
        self.assertEqual({"total": 0, "capped": False}, summary["categoryStats"]["Task"])


if __name__ == "__main__":
    unittest.main()
