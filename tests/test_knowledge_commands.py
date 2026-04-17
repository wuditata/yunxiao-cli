import json
import tempfile
import unittest

from tests import run_cli, run_cli_json, run_cli_main


WORKSPACE_URL = "https://thoughts.aliyun.com/workspaces/ws-123/overview"


class KnowledgeCommandsTest(unittest.TestCase):
    def test_knowledge_download_help_mentions_auth_options(self):
        code, output = run_cli(["knowledge", "download", "--help"])
        self.assertEqual(0, code)
        self.assertIn("--cookie", output)
        self.assertIn("--cookie-file", output)
        self.assertIn("--browser", output)
        self.assertIn("--thread", output)
        self.assertIn("工作区概览 URL", output)

    def test_knowledge_download_uses_explicit_cookie(self):
        import yunxiao_cli.app.knowledge_service as knowledge_service

        calls = {"cookies": [], "downloads": [], "browser": []}

        class FakeDownloader:
            def __init__(self, *, cookie_string):
                calls["cookies"].append(cookie_string)

            def download_workspace(self, *, url, output_dir, concurrency):
                calls["downloads"].append({"url": url, "output_dir": output_dir, "concurrency": concurrency})
                return {
                    "workspace": {"id": "ws-123", "name": "知识库"},
                    "output_dir": "D:/tmp/out",
                    "documents": {"total": 2, "downloaded": 2, "failed": 0},
                    "failures": [],
                }

        original_downloader = knowledge_service.ThoughtsDownloader
        original_loader = knowledge_service.load_browser_cookie_string
        knowledge_service.ThoughtsDownloader = FakeDownloader
        knowledge_service.load_browser_cookie_string = lambda browser: calls["browser"].append(browser)
        try:
            result = run_cli_json(
                [
                    "knowledge",
                    "download",
                    "--url",
                    WORKSPACE_URL,
                    "--cookie",
                    "a=1; b=2",
                ]
            )
        finally:
            knowledge_service.ThoughtsDownloader = original_downloader
            knowledge_service.load_browser_cookie_string = original_loader

        self.assertEqual([], calls["browser"])
        self.assertEqual(["a=1; b=2"], calls["cookies"])
        self.assertEqual([{"url": WORKSPACE_URL, "output_dir": None, "concurrency": 3}], calls["downloads"])
        self.assertTrue(result["success"])
        self.assertEqual("ws-123", result["data"]["workspace"]["id"])

    def test_knowledge_download_imports_browser_cookie(self):
        import yunxiao_cli.app.knowledge_service as knowledge_service

        calls = {"cookies": [], "downloads": [], "browser": []}

        class FakeDownloader:
            def __init__(self, *, cookie_string):
                calls["cookies"].append(cookie_string)

            def download_workspace(self, *, url, output_dir, concurrency):
                calls["downloads"].append({"url": url, "output_dir": output_dir, "concurrency": concurrency})
                return {
                    "workspace": {"id": "ws-123", "name": "知识库"},
                    "output_dir": "D:/tmp/out",
                    "documents": {"total": 1, "downloaded": 1, "failed": 0},
                    "failures": [],
                }

        original_downloader = knowledge_service.ThoughtsDownloader
        original_loader = knowledge_service.load_browser_cookie_string
        knowledge_service.ThoughtsDownloader = FakeDownloader
        knowledge_service.load_browser_cookie_string = lambda browser: calls["browser"].append(browser) or "c=3; d=4"
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                result = run_cli_json(
                    [
                        "knowledge",
                        "download",
                        "--url",
                        WORKSPACE_URL,
                        "--browser",
                        "edge",
                        "--output",
                        temp_dir,
                    ]
                )
        finally:
            knowledge_service.ThoughtsDownloader = original_downloader
            knowledge_service.load_browser_cookie_string = original_loader

        self.assertEqual(["edge"], calls["browser"])
        self.assertEqual(["c=3; d=4"], calls["cookies"])
        self.assertEqual([{"url": WORKSPACE_URL, "output_dir": temp_dir, "concurrency": 3}], calls["downloads"])
        self.assertTrue(result["success"])
        self.assertEqual("知识库", result["data"]["workspace"]["name"])

    def test_knowledge_download_passes_custom_thread(self):
        import yunxiao_cli.app.knowledge_service as knowledge_service

        calls = {"downloads": []}

        class FakeDownloader:
            def __init__(self, *, cookie_string):
                self.cookie_string = cookie_string

            def download_workspace(self, *, url, output_dir, concurrency):
                calls["downloads"].append({"url": url, "output_dir": output_dir, "concurrency": concurrency})
                return {
                    "workspace": {"id": "ws-123", "name": "知识库"},
                    "output_dir": "D:/tmp/out",
                    "documents": {"total": 1, "downloaded": 1, "failed": 0},
                    "failures": [],
                }

        original_downloader = knowledge_service.ThoughtsDownloader
        knowledge_service.ThoughtsDownloader = FakeDownloader
        try:
            result = run_cli_json(
                [
                    "knowledge",
                    "download",
                    "--url",
                    WORKSPACE_URL,
                    "--cookie",
                    "a=1",
                    "--thread",
                    "5",
                ]
            )
        finally:
            knowledge_service.ThoughtsDownloader = original_downloader

        self.assertEqual([{"url": WORKSPACE_URL, "output_dir": None, "concurrency": 5}], calls["downloads"])
        self.assertTrue(result["success"])

    def test_knowledge_download_rejects_mixed_auth_inputs(self):
        code, output = run_cli_main(
            [
                "knowledge",
                "download",
                "--url",
                WORKSPACE_URL,
                "--cookie",
                "a=1",
                "--browser",
                "edge",
            ]
        )

        self.assertEqual(1, code)
        result = json.loads(output)
        self.assertFalse(result["success"])
        self.assertIn("三选一", result["error"]["message"])


if __name__ == "__main__":
    unittest.main()
