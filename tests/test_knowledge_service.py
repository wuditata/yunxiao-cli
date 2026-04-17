import tempfile
import unittest
from pathlib import Path

import requests

from yunxiao_cli.app.knowledge_service import ThoughtsAPI, ThoughtsDownloader, ThoughtsMarkdownRenderer
from yunxiao_cli.app.errors import CliError


WORKSPACE_URL = "https://thoughts.aliyun.com/workspaces/ws-123/overview"


class FakeThoughtsAPI:
    def get_workspace(self, workspace_id: str):
        return {"id": workspace_id, "name": "研发/知识库"}

    def list_nodes(self, workspace_id: str, *, parent_id: str | None = None):
        if parent_id is None:
            return [
                {"_id": "doc-1", "title": "首页", "type": "document"},
                {"_id": "folder-1", "title": "后端/服务", "type": "folder"},
            ]
        if parent_id == "folder-1":
            return [
                {"_id": "doc-2", "title": "接口:说明", "type": "document"},
                {"_id": "doc-3", "title": "接口:说明", "type": "document"},
            ]
        return []


class FakeExporter:
    def __init__(self):
        self.calls = []

    def export_documents(self, *, workspace_id, documents, output_dir, concurrency):
        self.calls.append(
            {
                "workspace_id": workspace_id,
                "documents": documents,
                "output_dir": output_dir,
                "concurrency": concurrency,
            }
        )
        return {
            "downloaded_files": [str(output_dir / "首页.md"), str(output_dir / "后端_服务" / "接口_说明.md")],
            "failures": [{"id": "doc-3", "title": "接口_说明", "path": "后端_服务/接口_说明__doc-3.md", "message": "fail"}],
        }


class KnowledgeServiceTest(unittest.TestCase):
    def test_markdown_renderer_renders_blocks(self):
        renderer = ThoughtsMarkdownRenderer()

        markdown = renderer.render(
            [
                {"type": "title", "text": "产品计划迭代流程管理"},
                {"type": "paragraph", "text": "根据评审结果调整 PRD。"},
                {"type": "heading", "level": 2, "text": "PRD 评审"},
                {
                    "type": "list",
                    "ordered": False,
                    "items": [
                        {"depth": 0, "text": "明确范围"},
                        {"depth": 1, "text": "补充细节"},
                    ],
                },
                {
                    "type": "table",
                    "rows": [
                        ["序号", "流程"],
                        ["1", "PRD 书写"],
                    ],
                },
                {"type": "image", "src": "https://example.com/demo.png", "alt": "示意图"},
            ]
        )

        self.assertEqual(
            "\n".join(
                [
                    "# 产品计划迭代流程管理",
                    "",
                    "根据评审结果调整 PRD。",
                    "",
                    "## PRD 评审",
                    "",
                    "- 明确范围",
                    "  - 补充细节",
                    "",
                    "| 序号 | 流程 |",
                    "| --- | --- |",
                    "| 1 | PRD 书写 |",
                    "",
                    "![示意图](https://example.com/demo.png)",
                    "",
                ]
            ),
            markdown,
        )

    def test_api_wraps_request_exception_as_cli_error(self):
        api = ThoughtsAPI(cookie_string="sid=1")

        original_request = requests.request
        requests.request = lambda *args, **kwargs: (_ for _ in ()).throw(
            requests.ConnectionError("dns failed")
        )
        try:
            with self.assertRaises(CliError) as error:
                api.get_workspace("ws-123")
        finally:
            requests.request = original_request

        self.assertIn("请求知识库接口失败", str(error.exception))

    def test_downloader_collects_nested_documents_and_sanitizes_paths(self):
        exporter = FakeExporter()
        downloader = ThoughtsDownloader(
            cookie_string="sid=1",
            api=FakeThoughtsAPI(),
            exporter=exporter,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = downloader.download_workspace(url=WORKSPACE_URL, output_dir=temp_dir)

        self.assertEqual(1, len(exporter.calls))
        documents = exporter.calls[0]["documents"]
        self.assertEqual(
            ["首页.md", "后端_服务/接口_说明.md", "后端_服务/接口_说明__doc-3.md"],
            [item["relative_path"] for item in documents],
        )
        self.assertEqual(3, exporter.calls[0]["concurrency"])
        self.assertEqual(3, result["documents"]["total"])
        self.assertEqual(2, result["documents"]["downloaded"])
        self.assertEqual(1, result["documents"]["failed"])

    def test_downloader_passes_custom_concurrency(self):
        exporter = FakeExporter()
        downloader = ThoughtsDownloader(
            cookie_string="sid=1",
            api=FakeThoughtsAPI(),
            exporter=exporter,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            downloader.download_workspace(url=WORKSPACE_URL, output_dir=temp_dir, concurrency=5)

        self.assertEqual(5, exporter.calls[0]["concurrency"])

    def test_downloader_uses_workspace_name_as_default_output_dir(self):
        exporter = FakeExporter()
        downloader = ThoughtsDownloader(
            cookie_string="sid=1",
            api=FakeThoughtsAPI(),
            exporter=exporter,
        )

        result = downloader.download_workspace(url=WORKSPACE_URL, output_dir=None)

        output_dir = Path(result["output_dir"])
        self.assertEqual("研发_知识库", output_dir.name)

    def test_downloader_rejects_invalid_workspace_url(self):
        downloader = ThoughtsDownloader(
            cookie_string="sid=1",
            api=FakeThoughtsAPI(),
            exporter=FakeExporter(),
        )

        with self.assertRaises(CliError):
            downloader.download_workspace(url="https://thoughts.aliyun.com/overview", output_dir=None)


if __name__ == "__main__":
    unittest.main()
