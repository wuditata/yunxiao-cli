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
                {"id": "bug-type", "categoryId": "Bug", "defaultType": True, "name": "缺陷"},
            ],
            statuses={
                "req-type": [{"id": "req-new", "name": "需求创建", "displayName": "需求创建"}],
                "task-type": [{"id": "task-dev", "name": "功能开发", "displayName": "功能开发"}],
            },
            fields={
                "req-type": [{"id": "field-subject", "name": "标题"}],
                "task-type": [],
                "bug-type": [{"id": "field-severity", "name": "严重程度"}],
            },
            members=[{"id": "member-1", "userId": "user-1", "name": "Alice"}],
            updated_at="2099-01-01T00:00:00+00:00",
            ttl_seconds=3600,
            invalidated=False,
        )
    )
    return store


def seed_multi_project_store(root: Path) -> Store:
    store = Store(root=root)
    store.save_account(
        AccountConfig(
            name="pm-a",
            token="token-a",
            user={"id": "user-1", "name": "Alice"},
            organizations=[{"id": "123", "name": "FOXHIS"}],
        )
    )
    store.save_profile(
        ProfileConfig(
            name="pm-dev",
            account="pm-a",
            org="123",
            project="456",
            projects=["456", "457"],
        )
    )
    store.set_default_profile("pm-dev")
    for project_id, project_name in (("456", "AI 项目"), ("457", "测试项目")):
        store.save_meta_cache(
            MetaCache(
                account="pm-a",
                org="123",
                project=project_id,
                project_info={"id": project_id, "name": project_name},
                workitem_types=[
                    {"id": "req-type", "categoryId": "Req", "defaultType": True, "name": "产品需求"},
                    {"id": "task-type", "categoryId": "Task", "defaultType": True, "name": "任务"},
                    {"id": "bug-type", "categoryId": "Bug", "defaultType": True, "name": "缺陷"},
                ],
                statuses={
                    "req-type": [{"id": "req-new", "name": "需求创建", "displayName": "需求创建"}],
                    "task-type": [{"id": "task-dev", "name": "功能开发", "displayName": "功能开发"}],
                    "bug-type": [{"id": "bug-new", "name": "待修复", "displayName": "待修复"}],
                },
                fields={
                    "req-type": [{"id": "field-subject", "name": "标题"}],
                    "task-type": [],
                    "bug-type": [{"id": "field-severity", "name": "严重程度"}],
                },
                members=[{"id": "member-1", "userId": "user-1", "name": "Alice"}],
                updated_at="2099-01-01T00:00:00+00:00",
                ttl_seconds=3600,
                invalidated=False,
            )
        )
    return store


def seed_project_config_store(root: Path) -> Store:
    store = Store(root=root)
    store.save_account(
        AccountConfig(
            name="pm-a",
            token="token-a",
            user={"id": "user-1", "name": "Alice"},
            organizations=[{"id": "123", "name": "FOXHIS"}],
        )
    )
    store.save_profile(
        ProfileConfig(
            name="apollo",
            account="pm-a",
            org="123",
            project="456",
            projects=["456", "457"],
        )
    )
    store.set_default_profile("apollo")
    for project_id, project_name in (("456", "AI 项目"), ("457", "Apollo 项目")):
        store.save_meta_cache(
            MetaCache(
                account="pm-a",
                org="123",
                project=project_id,
                project_info={"id": project_id, "name": project_name},
                workitem_types=[
                    {"id": "task-type", "categoryId": "Task", "defaultType": True, "name": "任务"},
                ],
                statuses={"task-type": [{"id": "task-dev", "name": "功能开发", "displayName": "功能开发"}]},
                fields={"task-type": []},
                members=[
                    {"id": "member-1", "userId": "user-1", "name": "Alice"},
                    {"id": "member-2", "userId": "user-2", "name": "wyx"},
                ],
                updated_at="2099-01-01T00:00:00+00:00",
                ttl_seconds=3600,
                invalidated=False,
            )
        )
    return store


class WorkitemQueryCommandsTest(unittest.TestCase):
    @patch("requests.request")
    def test_workitem_create_uses_project_config_profile_project_and_assignee(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems"):
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "1001", "subject": kwargs["json"]["subject"]})
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_project_config_store(Path(temp_dir))
            project_root = Path(temp_dir) / "apollo-repo"
            project_root.mkdir(parents=True, exist_ok=True)
            (project_root / ".yunxiao.json").write_text(
                json.dumps(
                    {
                        "profile": "apollo",
                        "assignee": "wyx",
                        "project": "457",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            current_dir = Path.cwd()
            try:
                os.chdir(project_root)
                with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                    result = run_cli_json(
                        [
                            "workitem",
                            "create",
                            "--category",
                            "Task",
                            "--subject",
                            "来自项目配置",
                        ]
                    )
            finally:
                os.chdir(current_dir)

        self.assertTrue(result["success"])
        self.assertEqual("457", captured["payload"]["spaceId"])
        self.assertEqual("user-2", captured["payload"]["assignedTo"])
        self.assertEqual("apollo", result["profile"]["name"])
        self.assertEqual("457", result["profile"]["project"])

    @patch("requests.request")
    def test_workitem_mine_prefers_project_config_assignee(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if not url.endswith("/workitems:search"):
                raise AssertionError(url)
            payload = kwargs["json"]
            if payload["spaceId"] != "457" or payload["page"] != 1:
                return FakeResponse([])
            data = {
                "Req": [],
                "Task": [
                    {"id": "task-1", "assignedTo": {"userId": "user-2"}, "spaceId": "457"},
                    {"id": "task-2", "assignedTo": {"userId": "user-1"}, "spaceId": "457"},
                ],
                "Bug": [],
            }
            return FakeResponse(data[payload["category"]])

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_project_config_store(Path(temp_dir))
            project_root = Path(temp_dir) / "apollo-repo"
            project_root.mkdir(parents=True, exist_ok=True)
            (project_root / ".yunxiao.json").write_text(
                json.dumps(
                    {
                        "profile": "apollo",
                        "assignee": "wyx",
                        "project": "457",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            current_dir = Path.cwd()
            try:
                os.chdir(project_root)
                with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                    result = run_cli_json(["workitem", "mine"])
            finally:
                os.chdir(current_dir)

        self.assertTrue(result["success"])
        self.assertEqual(["task-1"], [item["id"] for item in result["data"]["items"]])
        self.assertEqual(["457"], result["data"]["filters"]["projects"])

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
    def test_workitem_create_accepts_field_name(self, request_mock):
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
                    [
                        "workitem",
                        "create",
                        "--profile",
                        "pm-dev",
                        "--category",
                        "Bug",
                        "--subject",
                        "严重程度必填",
                        "--field",
                        "严重程度=3-一般",
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual("bug-type", captured["payload"]["workitemTypeId"])
        self.assertEqual("3-一般", captured["payload"]["customFieldValues"]["field-severity"])

    @patch("requests.request")
    def test_workitem_create_accepts_field_json_object(self, request_mock):
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
                    [
                        "workitem",
                        "create",
                        "--profile",
                        "pm-dev",
                        "--category",
                        "Bug",
                        "--subject",
                        "严重程度必填",
                        "--field-json",
                        '{"严重程度":"3-一般"}',
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual("3-一般", captured["payload"]["customFieldValues"]["field-severity"])

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
                if kwargs["json"]["page"] != 1:
                    return FakeResponse([])
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
        self.assertEqual("Task", search_result["data"]["items"][0]["category"])
        self.assertEqual("功能开发", search_result["data"]["items"][0]["status"])
        self.assertEqual("in_progress", search_result["data"]["items"][0]["statusPhase"])
        self.assertEqual("AI 项目", search_result["data"]["items"][0]["project"])
        self.assertNotIn("workitemType", search_result["data"]["items"][0])
        self.assertEqual({"Task": 1}, search_result["data"]["summary"]["byCategory"])

    @patch("requests.request")
    def test_workitem_mine_filters_assigned_to_self(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems:search"):
                category = kwargs["json"]["category"]
                page = kwargs["json"]["page"]
                if page != 1:
                    return FakeResponse([])
                payload = {
                    "Req": [{"id": "req-1", "assignedTo": "user-1", "status": {"displayName": "待评审"}}],
                    "Task": [{"id": "task-1", "assignedTo": "user-2"}],
                    "Bug": [{"id": "bug-1", "assignedTo": {"userId": "user-1"}, "status": {"displayName": "已完成"}}],
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
        self.assertEqual({"todo": 1, "done": 1}, result["data"]["summary"]["byStatusPhase"])

    @patch("requests.request")
    def test_workitem_mine_aggregates_multiple_projects_with_full_paging_and_time_sort(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if not url.endswith("/workitems:search"):
                raise AssertionError(url)
            payload = kwargs["json"]
            project_id = payload["spaceId"]
            category = payload["category"]
            page = payload["page"]
            data = {
                ("456", "Req", 1): [
                    {
                        "id": "req-1",
                        "assignedTo": "user-1",
                        "gmtModified": "2026-03-26T09:00:00+08:00",
                        "spaceId": "456",
                        "status": {"displayName": "待评审"},
                    },
                ],
                ("456", "Task", 1): [
                    {
                        "id": "task-2",
                        "assignedTo": "user-1",
                        "gmtModified": "2026-03-26T12:00:00+08:00",
                        "spaceId": "456",
                        "status": {"displayName": "功能开发"},
                        "workitemType": {"id": "task-type"},
                    },
                ],
                ("456", "Task", 2): [
                    {
                        "id": "task-1",
                        "assignedTo": {"userId": "user-1"},
                        "gmtModified": "2026-03-26T11:00:00+08:00",
                        "spaceId": "456",
                        "status": {"displayName": "测试中"},
                        "workitemType": {"id": "task-type"},
                    },
                ],
                ("456", "Bug", 1): [],
                ("457", "Req", 1): [],
                ("457", "Task", 1): [
                    {"id": "task-3", "assignedTo": "user-2", "gmtModified": "2026-03-26T13:00:00+08:00"},
                ],
                ("457", "Bug", 1): [
                    {
                        "id": "bug-1",
                        "assignedTo": {"userId": "user-1"},
                        "gmtModified": "2026-03-26T10:00:00+08:00",
                        "spaceId": "457",
                        "status": {"displayName": "待修复"},
                        "workitemType": {"id": "bug-type"},
                    },
                ],
                ("457", "Bug", 2): [
                    {
                        "id": "bug-2",
                        "assignedTo": {"userId": "user-1"},
                        "gmtModified": "2026-03-26T08:00:00+08:00",
                        "spaceId": "457",
                        "status": {"displayName": "已取消"},
                        "workitemType": {"id": "bug-type"},
                    },
                ],
            }
            return FakeResponse(data.get((project_id, category, page), []))

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_multi_project_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(["workitem", "mine", "--profile", "pm-dev", "--sort", "time"])

        self.assertTrue(result["success"])
        self.assertEqual(5, result["data"]["total"])
        self.assertEqual(["task-2", "task-1", "bug-1", "req-1", "bug-2"], [item["id"] for item in result["data"]["items"]])
        self.assertEqual(["456", "457"], result["data"]["filters"]["projects"])
        self.assertEqual("time", result["data"]["filters"]["sort"])
        self.assertEqual({"AI 项目": 3, "测试项目": 2}, result["data"]["summary"]["byProject"])
        self.assertEqual({"in_progress": 2, "todo": 2, "canceled": 1}, result["data"]["summary"]["byStatusPhase"])

    @patch("requests.request")
    def test_workitem_search_supports_project_filter_full_paging_and_time_sort(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if not url.endswith("/workitems:search"):
                raise AssertionError(url)
            payload = kwargs["json"]
            self.assertEqual("457", payload["spaceId"])
            self.assertEqual("Task", payload["category"])
            conditions = json.loads(payload["conditions"])
            self.assertEqual("task-dev", conditions["conditionGroups"][0][1]["value"][0])
            page = payload["page"]
            data = {
                1: [
                    {"id": "task-2", "gmtModified": "2026-03-26T11:00:00+08:00", "spaceId": "457"},
                ],
                2: [
                    {"id": "task-1", "gmtModified": "2026-03-26T09:00:00+08:00", "spaceId": "457"},
                ],
            }
            return FakeResponse(data.get(page, []))

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_multi_project_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "search",
                        "--profile",
                        "pm-dev",
                        "--project",
                        "457",
                        "--category",
                        "Task",
                        "--status",
                        "功能开发",
                        "--sort",
                        "time",
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual(["task-2", "task-1"], [item["id"] for item in result["data"]["items"]])
        self.assertEqual(["457"], result["data"]["filters"]["projects"])
        self.assertEqual("time", result["data"]["filters"]["sort"])
        self.assertEqual("测试项目", result["data"]["items"][0]["project"])

    @patch("requests.request")
    def test_workitem_search_raw_keeps_original_item_fields(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems:search"):
                return FakeResponse(
                    [
                        {
                            "id": "task-1",
                            "subject": "raw item",
                            "spaceId": "456",
                            "workitemType": {"id": "task-type", "name": "任务"},
                            "status": {"displayName": "功能开发"},
                        }
                    ]
                )
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "search",
                        "--profile",
                        "pm-dev",
                        "--category",
                        "Task",
                        "--raw",
                    ]
                )

        self.assertTrue(result["success"])
        self.assertIn("workitemType", result["data"]["items"][0])
        self.assertNotIn("summary", result["data"])

    @patch("requests.request")
    def test_workitem_summary_phase_matches_real_workflow_keywords(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if not url.endswith("/workitems:search"):
                raise AssertionError(url)
            payload = kwargs["json"]
            project_id = payload["spaceId"]
            category = payload["category"]
            if project_id != "456":
                return FakeResponse([])
            data = {
                "Req": [{"id": "req-1", "assignedTo": "user-1", "status": {"displayName": "已选择"}}],
                "Task": [{"id": "task-1", "assignedTo": "user-1", "status": {"displayName": "已解决"}}],
                "Bug": [{"id": "bug-1", "assignedTo": "user-1", "status": {"displayName": "暂不修复"}}],
            }
            return FakeResponse(data[category])

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(["workitem", "mine", "--profile", "pm-dev"])

        by_id = {item["id"]: item["statusPhase"] for item in result["data"]["items"]}
        self.assertEqual("todo", by_id["req-1"])
        self.assertEqual("done", by_id["task-1"])
        self.assertEqual("canceled", by_id["bug-1"])

    @patch("requests.request")
    def test_workitem_create_normalizes_escaped_newlines_in_desc(self, request_mock):
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
                    [
                        "workitem",
                        "create",
                        "--profile",
                        "pm-dev",
                        "--category",
                        "Task",
                        "--subject",
                        "desc newline",
                        "--desc",
                        "## title\\n- item1\\n- item2\\n\\nparagraph2",
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual("## title\n- item1\n- item2\n\nparagraph2", captured["payload"]["description"])
        self.assertEqual("MARKDOWN", captured["payload"]["formatType"])

    @patch("requests.request")
    def test_workitem_create_uses_parent_id_field(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/parent-1"):
                return FakeResponse({"id": "parent-1", "serialNumber": "MGKH-68"})
            if url.endswith("/workitems"):
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "1001", "subject": kwargs["json"]["subject"]})
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "create",
                        "--profile",
                        "pm-dev",
                        "--category",
                        "Task",
                        "--subject",
                        "child task",
                        "--parent",
                        "parent-1",
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual("parent-1", captured["payload"]["parentId"])

    @patch("requests.request")
    def test_workitem_create_resolves_parent_serial_number(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/MGKH-68"):
                return FakeResponse({"message": "Not Found"}, status_code=404)
            if url.endswith("/workitems:search"):
                category = kwargs["json"]["category"]
                if category == "Req":
                    return FakeResponse([{"id": "parent-1", "serialNumber": "MGKH-68"}])
                return FakeResponse([])
            if url.endswith("/workitems"):
                captured["payload"] = kwargs["json"]
                return FakeResponse({"id": "1001", "subject": kwargs["json"]["subject"]})
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "create",
                        "--profile",
                        "pm-dev",
                        "--category",
                        "Task",
                        "--subject",
                        "child task",
                        "--parent",
                        "MGKH-68",
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual("parent-1", captured["payload"]["parentId"])


if __name__ == "__main__":
    unittest.main()
