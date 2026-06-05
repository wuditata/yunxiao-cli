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
    def __init__(self, payload, status_code: int = 200):
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


class FlowCommandsTest(unittest.TestCase):
    @patch("requests.request")
    def test_flow_pipeline_list_filters_by_search(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["params"] = kwargs["params"]
            captured["headers"] = kwargs["headers"]
            if method == "GET" and url.endswith("/oapi/v1/flow/organizations/123/pipelines"):
                return FakeResponse(
                    [
                        {"pipelineId": 4921657, "pipelineName": "xm-sfe-admin-ui-uat"},
                        {"pipelineId": 4921658, "pipelineName": "xm-sfe-admin-service-uat"},
                    ]
                )
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        result = self._run(["flow", "pipeline", "list", "--search", "sfe", "--profile", "default"])

        self.assertTrue(result["success"])
        self.assertEqual(2, result["data"]["total"])
        self.assertEqual("xm-sfe-admin-ui-uat", result["data"]["pipelines"][0]["pipelineName"])
        self.assertEqual(
            {"page": 1, "perPage": 20, "pipelineName": "sfe"},
            captured["params"],
        )
        self.assertEqual("token-a", captured["headers"]["x-yunxiao-token"])

    @patch("requests.request")
    def test_flow_pipeline_get_returns_detail(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            if method == "GET" and url.endswith("/oapi/v1/flow/organizations/123/pipelines/4921657"):
                return FakeResponse(
                    {
                        "name": "xm-sfe-admin-ui-uat",
                        "pipelineConfig": {
                            "sources": [
                                {"data": {"repo": "https://codeup.aliyun.com/org/xmsfe.git"}},
                            ]
                        },
                    }
                )
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        result = self._run(["flow", "pipeline", "get", "4921657"])

        self.assertTrue(result["success"])
        self.assertEqual("xm-sfe-admin-ui-uat", result["data"]["pipeline"]["name"])
        self.assertEqual("GET", captured["method"])
        self.assertTrue(captured["url"].endswith("/oapi/v1/flow/organizations/123/pipelines/4921657"))

    @patch("requests.request")
    def test_flow_run_create_passes_raw_params(self, request_mock):
        captured = {}
        raw_params = '{"branchModeBranchs":["main"],"envs":{"ENV":"prod"}}'

        def request_side_effect(method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["json"] = kwargs["json"]
            captured["headers"] = kwargs["headers"]
            if method == "POST" and url.endswith("/oapi/v1/flow/organizations/123/pipelines/789/runs"):
                return FakeResponse(9001)
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        result = self._run(["flow", "run", "create", "789", "--params", raw_params])

        self.assertTrue(result["success"])
        self.assertEqual(9001, result["data"]["pipelineRunId"])
        self.assertEqual("POST", captured["method"])
        self.assertEqual({"params": raw_params}, captured["json"])
        self.assertEqual("token-a", captured["headers"]["x-yunxiao-token"])

    @patch("requests.request")
    def test_flow_run_create_builds_params_from_simplified_options(self, request_mock):
        calls = []

        def request_side_effect(method, url, **kwargs):
            calls.append((method, url, kwargs.get("json")))
            if method == "GET" and url.endswith("/oapi/v1/flow/organizations/123/pipelines/789"):
                return FakeResponse(
                    {
                        "pipelineConfig": {
                            "sources": [
                                {"data": {"repo": "https://codeup.aliyun.com/org/repo.git"}},
                            ]
                        }
                    }
                )
            if method == "POST" and url.endswith("/oapi/v1/flow/organizations/123/pipelines/789/runs"):
                return FakeResponse(9002)
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        result = self._run(
            [
                "flow",
                "run",
                "create",
                "789",
                "--branch",
                "release/1.0",
                "--env",
                "ENV=prod",
                "--param",
                "debug=true",
                "--comment",
                "deploy release",
            ]
        )

        self.assertTrue(result["success"])
        self.assertEqual(9002, result["data"]["pipelineRunId"])
        payload = json.loads(calls[-1][2]["params"])
        self.assertEqual(True, payload["debug"])
        self.assertEqual({"ENV": "prod"}, payload["envs"])
        self.assertEqual(
            {"https://codeup.aliyun.com/org/repo.git": "release/1.0"},
            payload["runningBranchs"],
        )
        self.assertEqual("deploy release", payload["comment"])

    @patch("requests.request")
    def test_flow_job_start_posts_start_endpoint(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["json"] = kwargs["json"]
            if method == "POST" and url.endswith(
                "/oapi/v1/flow/organizations/123/pipelines/789/pipelineRuns/12/jobs/34/start"
            ):
                return FakeResponse(True)
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        result = self._run(["flow", "job", "start", "789", "12", "34"])

        self.assertTrue(result["success"])
        self.assertTrue(result["data"]["started"])
        self.assertEqual("POST", captured["method"])
        self.assertIsNone(captured["json"])

    def _run(self, args: list[str]) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            current_dir = Path.cwd()
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                    return run_cli_json(args)
            finally:
                os.chdir(current_dir)


if __name__ == "__main__":
    unittest.main()
