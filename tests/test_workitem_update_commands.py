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
                {"id": "task-type", "categoryId": "Task", "defaultType": True, "name": "任务"},
            ],
            statuses={
                "task-type": [{"id": "task-dev", "name": "功能开发", "displayName": "功能开发"}],
            },
            fields={
                "task-type": [
                    {"id": "field-plan", "name": "计划完成时间"},
                    {"id": "101586", "name": "预计工时"},
                ]
            },
            members=[{"id": "member-1", "userId": "user-1", "name": "Alice"}],
            updated_at="2099-01-01T00:00:00+00:00",
            ttl_seconds=3600,
            invalidated=False,
        )
    )
    return store


class WorkitemUpdateCommandsTest(unittest.TestCase):
    @patch("requests.request")
    def test_workitem_transition_resolves_status_name_from_cache(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001") and method == "GET":
                return FakeResponse({"id": "1001", "workitemType": {"id": "task-type"}})
            if url.endswith("/workitems/1001") and method == "PUT":
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "1001"})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    ["workitem", "transition", "1001", "--profile", "pm-dev", "--to", "功能开发"]
                )

        self.assertTrue(result["success"])
        self.assertEqual("task-dev", captured["payload"]["status"])

    @patch("requests.request")
    def test_workitem_transition_accepts_required_fields(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001") and method == "GET":
                return FakeResponse({"id": "1001", "workitemType": {"id": "task-type"}})
            if url.endswith("/workitems/1001") and method == "PUT":
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "1001"})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "transition",
                        "1001",
                        "--profile",
                        "pm-dev",
                        "--to",
                        "功能开发",
                        "--field",
                        "field-plan=2026-04-01",
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual("task-dev", captured["payload"]["status"])
        self.assertEqual("2026-04-01", captured["payload"]["field-plan"])

    @patch("requests.request")
    def test_workitem_update_resolves_member_and_field_names(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001") and method == "GET":
                return FakeResponse({"id": "1001", "workitemType": {"id": "task-type"}})
            if url.endswith("/workitems/1001") and method == "PUT":
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "1001"})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "update",
                        "1001",
                        "--profile",
                        "pm-dev",
                        "--assigned-to",
                        "Alice",
                        "--field",
                        "计划完成时间=2026-03-31",
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual("user-1", captured["payload"]["assignedTo"])
        self.assertEqual("2026-03-31", captured["payload"]["field-plan"])

    @patch("requests.request")
    def test_workitem_update_accepts_field_id(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001") and method == "GET":
                return FakeResponse({"id": "1001", "workitemType": {"id": "task-type"}})
            if url.endswith("/workitems/1001") and method == "PUT":
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "1001"})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "update",
                        "1001",
                        "--profile",
                        "pm-dev",
                        "--field",
                        "field-plan=2026-04-01",
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual("2026-04-01", captured["payload"]["field-plan"])

    @patch("requests.request")
    def test_workitem_update_accepts_field_json_object(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001") and method == "GET":
                return FakeResponse({"id": "1001", "workitemType": {"id": "task-type"}})
            if url.endswith("/workitems/1001") and method == "PUT":
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "1001"})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "update",
                        "1001",
                        "--profile",
                        "pm-dev",
                        "--field-json",
                        '{"预计工时": 1.5}',
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual(1.5, captured["payload"]["101586"])


if __name__ == "__main__":
    unittest.main()
