import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import run_cli, run_cli_json, run_cli_main
from yunxiao_cli.domain.models import AccountConfig, MetaCache, ProfileConfig
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
            ],
            statuses={"req-type": []},
            fields={"req-type": []},
            members=[{"id": "member-1", "userId": "user-1", "name": "Alice"}],
            updated_at="2099-01-01T00:00:00+00:00",
            ttl_seconds=3600,
            invalidated=False,
        )
    )
    return store


class WorkitemAttachmentCommandsTest(unittest.TestCase):
    def test_workitem_create_help_mentions_attachment_behavior(self):
        code, output = run_cli(["workitem", "create", "--help"])
        self.assertEqual(0, code)
        self.assertIn("--attachment", output)
        self.assertIn("失败即停止", output)

    def test_workitem_attachment_upload_help(self):
        code, output = run_cli(["workitem", "attachment", "upload", "--help"])
        self.assertEqual(0, code)
        self.assertIn("--path", output)
        self.assertIn("本地文件路径", output)

    @patch("requests.request")
    def test_workitem_attachment_upload_uses_multipart_request(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001/attachments") and method == "POST":
                captured["headers"] = kwargs["headers"]
                captured["data"] = kwargs.get("data")
                captured["files"] = kwargs["files"]
                return FakeResponse({"id": "att-1", "fileName": "a.txt"})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            file_path = Path(temp_dir) / "a.txt"
            file_path.write_text("hello", encoding="utf-8")
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "attachment",
                        "upload",
                        "1001",
                        "--profile",
                        "pm-dev",
                        "--path",
                        str(file_path),
                    ]
                )

        self.assertTrue(result["success"])
        self.assertNotIn("Content-Type", captured["headers"])
        self.assertNotIn("json", request_mock.call_args.kwargs)
        self.assertEqual("a.txt", captured["files"]["file"][0])
        self.assertEqual("att-1", result["data"]["attachment"]["id"])

    @patch("requests.request")
    def test_workitem_attachment_list_and_get_commands(self, request_mock):
        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001/attachments") and method == "GET":
                return FakeResponse([{"id": "att-1", "fileName": "a.txt"}])
            if url.endswith("/workitems/1001/files/file-1") and method == "GET":
                return FakeResponse({"result": {"id": "file-1", "name": "a.txt"}})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                list_result = run_cli_json(["workitem", "attachment", "list", "1001", "--profile", "pm-dev"])
                get_result = run_cli_json(
                    [
                        "workitem",
                        "attachment",
                        "get",
                        "1001",
                        "--profile",
                        "pm-dev",
                        "--file",
                        "file-1",
                    ]
                )

        self.assertEqual("att-1", list_result["data"]["attachments"][0]["id"])
        self.assertEqual("file-1", get_result["data"]["file"]["id"])

    @patch("requests.request")
    def test_workitem_create_uploads_multiple_attachments_in_order(self, request_mock):
        upload_names: list[str] = []

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems") and method == "POST":
                return FakeResponse({"id": "1001", "subject": kwargs["json"]["subject"]})
            if url.endswith("/workitems/1001/attachments") and method == "POST":
                upload_names.append(kwargs["files"]["file"][0])
                return FakeResponse({"id": f"att-{len(upload_names)}", "fileName": kwargs["files"]["file"][0]})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            file_a = Path(temp_dir) / "a.txt"
            file_b = Path(temp_dir) / "b.txt"
            file_a.write_text("A", encoding="utf-8")
            file_b.write_text("B", encoding="utf-8")
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                result = run_cli_json(
                    [
                        "workitem",
                        "create",
                        "--profile",
                        "pm-dev",
                        "--category",
                        "Req",
                        "--subject",
                        "支持附件",
                        "--attachment",
                        str(file_a),
                        "--attachment",
                        str(file_b),
                    ]
                )

        self.assertTrue(result["success"])
        self.assertEqual(["a.txt", "b.txt"], upload_names)
        self.assertEqual("att-1", result["data"]["attachments"][0]["id"])
        self.assertEqual("att-2", result["data"]["attachments"][1]["id"])

    @patch("requests.request")
    def test_workitem_create_attachment_failure_is_fail_fast(self, request_mock):
        upload_names: list[str] = []

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems") and method == "POST":
                return FakeResponse({"id": "1001", "subject": kwargs["json"]["subject"]})
            if url.endswith("/workitems/1001/attachments") and method == "POST":
                upload_names.append(kwargs["files"]["file"][0])
                if len(upload_names) == 2:
                    return FakeResponse({"message": "upload failed"}, status_code=500)
                return FakeResponse({"id": f"att-{len(upload_names)}", "fileName": kwargs["files"]["file"][0]})
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            file_a = Path(temp_dir) / "a.txt"
            file_b = Path(temp_dir) / "b.txt"
            file_c = Path(temp_dir) / "c.txt"
            for path in (file_a, file_b, file_c):
                path.write_text(path.stem, encoding="utf-8")
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                code, output = run_cli_main(
                    [
                        "workitem",
                        "create",
                        "--profile",
                        "pm-dev",
                        "--category",
                        "Req",
                        "--subject",
                        "支持附件",
                        "--attachment",
                        str(file_a),
                        "--attachment",
                        str(file_b),
                        "--attachment",
                        str(file_c),
                    ]
                )

        self.assertEqual(1, code)
        result = json.loads(output)
        self.assertFalse(result["success"])
        self.assertEqual(["a.txt", "b.txt"], upload_names)
        self.assertEqual("1001", result["error"]["response"]["workitem"]["id"])
        self.assertEqual(str(file_b.resolve()), result["error"]["response"]["failed_attachment"])
        self.assertEqual("att-1", result["error"]["response"]["uploaded_attachments"][0]["id"])


if __name__ == "__main__":
    unittest.main()
