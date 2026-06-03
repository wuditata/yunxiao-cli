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
    def test_codeup_mr_merge_posts_safe_default_payload(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["json"] = kwargs["json"]
            captured["headers"] = kwargs["headers"]
            if method == "POST" and url.endswith(
                "/oapi/v1/codeup/organizations/123/repositories/2813489/changeRequests/7/merge"
            ):
                return FakeResponse(
                    {
                        "localId": "7",
                        "status": "MERGED",
                        "mergedRevision": "merge-sha",
                        "sourceBranch": "feature/mr-merge",
                        "targetBranch": "main",
                    }
                )
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            current_dir = Path.cwd()
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                    result = run_cli_json(["codeup", "mr", "merge", "2813489", "7"])
            finally:
                os.chdir(current_dir)

        self.assertTrue(result["success"])
        self.assertEqual("MERGED", result["data"]["changeRequest"]["status"])
        self.assertEqual("merge-sha", result["data"]["changeRequest"]["mergedRevision"])
        self.assertEqual("token-a", captured["headers"]["x-yunxiao-token"])
        self.assertEqual(
            {
                "mergeType": "no-fast-forward",
                "removeSourceBranch": False,
            },
            captured["json"],
        )

    @patch("requests.request")
    def test_codeup_mr_merge_accepts_merge_options(self, request_mock):
        captured = {}

        def request_side_effect(method, url, **kwargs):
            captured["json"] = kwargs["json"]
            if method == "POST" and url.endswith(
                "/oapi/v1/codeup/organizations/123/repositories/2813489/changeRequests/7/merge"
            ):
                return FakeResponse({"localId": "7", "status": "MERGED"})
            raise AssertionError(f"{method} {url}")

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
                            "merge",
                            "2813489",
                            "7",
                            "--merge-type",
                            "squash",
                            "--message",
                            "merge message",
                            "--remove-source-branch",
                        ]
                    )
            finally:
                os.chdir(current_dir)

        self.assertTrue(result["success"])
        self.assertEqual(
            {
                "mergeType": "squash",
                "mergeMessage": "merge message",
                "removeSourceBranch": True,
            },
            captured["json"],
        )

    @patch("requests.request")
    def test_codeup_mr_comments_uses_official_comments_list_endpoint(self, request_mock):
        captured = []

        def request_side_effect(method, url, **kwargs):
            captured.append((method, url, kwargs.get("json")))
            if method == "POST" and url.endswith(
                "/oapi/v1/codeup/organizations/123/repositories/2813489/changeRequests/7/comments/list"
            ):
                comment_type = kwargs["json"]["commentType"]
                if comment_type == "GLOBAL_COMMENT":
                    return FakeResponse([{"bizId": "global-1", "commentType": comment_type}])
                if comment_type == "INLINE_COMMENT":
                    return FakeResponse([{"bizId": "inline-1", "commentType": comment_type}])
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            current_dir = Path.cwd()
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                    result = run_cli_json(["codeup", "mr", "comments", "2813489", "7"])
            finally:
                os.chdir(current_dir)

        self.assertTrue(result["success"])
        self.assertEqual(
            [
                {"bizId": "global-1", "commentType": "GLOBAL_COMMENT"},
                {"bizId": "inline-1", "commentType": "INLINE_COMMENT"},
            ],
            result["data"]["comments"],
        )
        self.assertEqual(2, result["data"]["total"])
        self.assertEqual(
            [
                {
                    "patchSetBizIds": [],
                    "commentType": "GLOBAL_COMMENT",
                    "state": "OPENED",
                    "resolved": False,
                },
                {
                    "patchSetBizIds": [],
                    "commentType": "INLINE_COMMENT",
                    "state": "OPENED",
                    "resolved": False,
                },
            ],
            [payload for _, _, payload in captured],
        )

    @patch("requests.request")
    def test_codeup_mr_review_fetches_github_style_context(self, request_mock):
        calls = []

        def request_side_effect(method, url, **kwargs):
            calls.append((method, url, kwargs.get("params"), kwargs.get("json")))
            if method == "GET" and url.endswith(
                "/oapi/v1/codeup/organizations/123/repositories/2813489/changeRequests/7"
            ):
                return FakeResponse(
                    {
                        "localId": "7",
                        "title": "支持本地 agent review",
                        "sourceBranch": "feature/review",
                        "targetBranch": "main",
                    }
                )
            if method == "GET" and url.endswith(
                "/oapi/v1/codeup/organizations/123/repositories/2813489/changeRequests/7/diffs/patches"
            ):
                return FakeResponse(
                    [
                        {"patchSetBizId": "base-patch", "patchSetName": "main"},
                        {"patchSetBizId": "head-patch", "patchSetName": "feature/review"},
                    ]
                )
            if method == "POST" and url.endswith(
                "/oapi/v1/codeup/organizations/123/repositories/2813489/changeRequests/7/comments/list"
            ):
                if kwargs["json"]["commentType"] == "GLOBAL_COMMENT":
                    return FakeResponse([{"bizId": "global-1", "content": "整体说明"}])
                return FakeResponse([{"bizId": "inline-1", "filePath": "src/app.py", "lineNumber": 12}])
            if method == "GET" and url.endswith(
                "/oapi/v1/codeup/organizations/123/repositories/2813489/compares"
            ):
                self.assertEqual(
                    {"from": "main", "to": "feature/review"},
                    kwargs["params"],
                )
                return FakeResponse(
                    {
                        "diffs": [
                            {
                                "newPath": "src/app.py",
                                "diff": "@@ -1 +1 @@\n-old\n+new",
                            }
                        ]
                    }
                )
            raise AssertionError(f"{method} {url}")

        request_mock.side_effect = request_side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            seed_store(Path(temp_dir))
            current_dir = Path.cwd()
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"YUNXIAO_CLI_HOME": temp_dir}, clear=False):
                    result = run_cli_json(["codeup", "mr", "review", "2813489", "7"])
            finally:
                os.chdir(current_dir)

        self.assertTrue(result["success"])
        self.assertEqual("7", result["data"]["changeRequest"]["localId"])
        self.assertEqual("base-patch", result["data"]["patchSets"][0]["patchSetBizId"])
        self.assertEqual("global-1", result["data"]["comments"][0]["bizId"])
        self.assertEqual("inline-1", result["data"]["comments"][1]["bizId"])
        self.assertEqual("src/app.py", result["data"]["compare"]["diffs"][0]["newPath"])
        self.assertFalse(any("/diffs/compare" in call[1] for call in calls))

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
