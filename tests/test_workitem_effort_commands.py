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
            workitem_types=[],
            statuses={},
            fields={},
            members=[],
            updated_at="2099-01-01T00:00:00+00:00",
            ttl_seconds=3600,
            invalidated=False,
        )
    )


class WorkitemEffortCommandsTest(unittest.TestCase):
    def test_workitem_effort_add_help(self):
        code, output = run_cli(["workitem", "effort", "add", "--help"])
        self.assertEqual(0, code)
        self.assertIn("--hours", output)
        self.assertIn("--date", output)
        self.assertIn("--work-type", output)

    @patch("requests.request")
    def test_workitem_effort_add_and_list(self, request_mock):
        captured: dict = {}
        record = {
            "id": "effort-1",
            "actualTime": 4,
            "description": "Gateway SLS logging",
            "gmtStart": 1784563200000,
            "gmtEnd": 1784563200000,
            "workType": None,
        }

        def request_side_effect(method, url, **kwargs):
            if url.endswith("/workitems/1001/effortRecords") and method == "POST":
                captured.update(kwargs["json"])
                return FakeResponse({"id": "effort-1"})
            if url.endswith("/workitems/1001/effortRecords") and method == "GET":
                return FakeResponse([record])
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                add_result = run_cli_json(
                    [
                        "workitem",
                        "effort",
                        "add",
                        "1001",
                        "--profile",
                        "pm-dev",
                        "--hours",
                        "4",
                        "--date",
                        "2026-07-21",
                        "--description",
                        "Gateway SLS logging",
                    ]
                )
                list_result = run_cli_json(["workitem", "effort", "list", "1001", "--profile", "pm-dev"])

        self.assertEqual("effort-1", add_result["data"]["effort"]["id"])
        self.assertEqual(4.0, captured["actualTime"])
        self.assertEqual("2026-07-21T00:00:00.000Z", captured["gmtStart"])
        self.assertEqual(captured["gmtStart"], captured["gmtEnd"])
        self.assertEqual("Gateway SLS logging", captured["description"])
        self.assertNotIn("workType", captured)
        self.assertEqual(record, list_result["data"]["efforts"][0])

    @patch("requests.request")
    def test_workitem_effort_add_rejects_invalid_date(self, request_mock):
        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                code, output = run_cli_main(
                    [
                        "workitem",
                        "effort",
                        "add",
                        "1001",
                        "--profile",
                        "pm-dev",
                        "--hours",
                        "4",
                        "--date",
                        "2026-02-30",
                    ]
                )

        self.assertEqual(1, code)
        self.assertIn("invalid effort date", json.loads(output)["error"]["message"])
        request_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
