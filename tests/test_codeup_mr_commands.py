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


class CodeupMrCommandsTest(unittest.TestCase):
    @patch("requests.request")
    def test_codeup_mr_create_posts_change_request_payload(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["json"] = kwargs["json"]
            captured["headers"] = kwargs["headers"]
            if method == "POST" and url.endswith("/oapi/v1/codeup/organizations/123/repositories/2813489/changeRequests"):
                return FakeResponse(
                    {
                        "localId": "7",
                        "title": kwargs["json"]["title"],
                        "sourceBranch": kwargs["json"]["sourceBranch"],
                        "targetBranch": kwargs["json"]["targetBranch"],
                        "webUrl": "https://codeup.aliyun.com/123/repo/merge_requests/7",
                    }
                )
            raise AssertionError(url)

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            current_dir = Path.cwd()
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                    result = run_cli_json(
                        [
                            "codeup",
                            "mr",
                            "create",
                            "2813489",
                            "--title",
                            "支持 CLI 创建 MR",
                            "--source",
                            "feature/mr-create",
                            "--target",
                            "main",
                            "--desc",
                            "实现命令行创建合并请求",
                            "--reviewer",
                            "user-1,user-2",
                            "--workitem",
                            "workitem-1",
                            "--ai-review",
                        ]
                    )
            finally:
                os.chdir(current_dir)

        self.assertTrue(result["success"])
        self.assertEqual("7", result["data"]["changeRequest"]["localId"])
        self.assertEqual("token-a", captured["headers"]["x-yunxiao-token"])
        self.assertEqual(
            {
                "title": "支持 CLI 创建 MR",
                "sourceBranch": "feature/mr-create",
                "targetBranch": "main",
                "sourceProjectId": "2813489",
                "targetProjectId": "2813489",
                "createFrom": "COMMAND_LINE",
                "description": "实现命令行创建合并请求",
                "reviewerUserIds": ["user-1", "user-2"],
                "workItemIds": ["workitem-1"],
                "triggerAIReviewRun": True,
            },
            captured["json"],
        )


if __name__ == "__main__":
    unittest.main()
