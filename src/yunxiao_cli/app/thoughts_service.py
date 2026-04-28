from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import importlib
import json
import re
from pathlib import Path
from typing import Any

import requests

from .errors import CliError


THOUGHTS_BASE_URL = "https://thoughts.aliyun.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

BROWSER_LOADERS = {
    "chrome": "chrome",
    "edge": "edge",
    "brave": "brave",
    "firefox": "firefox",
}


def extract_workspace_id(url: str) -> str:
    match = re.search(r"/workspaces/([A-Za-z0-9_-]+)", url or "")
    if not match:
        raise CliError("无效的知识库 URL，无法识别 workspace id")
    return match.group(1)


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", (name or "").strip())
    cleaned = cleaned.strip(". ")
    return cleaned or "untitled"


def parse_cookie_string(cookie_string: str) -> list[dict[str, Any]]:
    normalized = (cookie_string or "").strip()
    if not normalized:
        return []
    if normalized.startswith("["):
        return _parse_cookie_json(normalized)

    cookies: list[dict[str, Any]] = []
    for item in normalized.split(";"):
        if "=" not in item:
            continue
        name, value = item.split("=", 1)
        cookie_name = name.strip()
        cookie_value = value.strip()
        if not cookie_name:
            continue
        cookies.append(
            {
                "name": cookie_name,
                "value": cookie_value,
                "path": "/",
            }
        )
    return cookies


def build_cookie_header(cookie_string: str) -> str:
    pairs = [
        f'{item["name"]}={item["value"]}'
        for item in parse_cookie_string(cookie_string)
        if item.get("name") and item.get("value")
    ]
    if not pairs:
        raise CliError("缺少有效的知识库 Cookie")
    return "; ".join(pairs)


def _parse_cookie_json(cookie_string: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(cookie_string)
    except json.JSONDecodeError as error:
        raise CliError(f"Cookie JSON 解析失败: {error}") from error

    if not isinstance(payload, list):
        raise CliError("Cookie JSON 必须是数组")

    cookies: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        cookie_name = str(item.get("name") or "").strip()
        cookie_value = str(item.get("value") or "").strip()
        if not cookie_name or not cookie_value:
            continue
        cookie: dict[str, Any] = {
            "name": cookie_name,
            "value": cookie_value,
            "path": str(item.get("path") or "/").strip() or "/",
        }
        domain = str(item.get("domain") or "").strip()
        if domain:
            cookie["domain"] = domain
        expires = item.get("expirationDate")
        if expires not in (None, ""):
            try:
                cookie["expires"] = int(float(expires))
            except (TypeError, ValueError):
                pass
        if "secure" in item:
            cookie["secure"] = bool(item["secure"])
        if "httpOnly" in item:
            cookie["httpOnly"] = bool(item["httpOnly"])
        same_site = _normalize_same_site(item.get("sameSite"))
        if same_site:
            cookie["sameSite"] = same_site
        cookies.append(cookie)

    if not cookies:
        raise CliError("Cookie JSON 中没有可用条目")
    return cookies


def _normalize_same_site(value: Any) -> str | None:
    normalized = str(value or "").strip().lower()
    same_site_map = {
        "strict": "Strict",
        "lax": "Lax",
        "none": "None",
        "no_restriction": "None",
    }
    return same_site_map.get(normalized)


def load_browser_cookie_string(browser: str) -> str:
    loader_name = BROWSER_LOADERS.get((browser or "").lower())
    if not loader_name:
        raise CliError(f"不支持的浏览器: {browser}")
    try:
        cookie_module = importlib.import_module("browser_cookie3")
    except ImportError as error:
        raise CliError("缺少 browser-cookie3 依赖，请重新安装 CLI") from error

    jar_loader = getattr(cookie_module, loader_name, None)
    if not jar_loader:
        raise CliError(f"browser-cookie3 不支持浏览器: {browser}")

    try:
        try:
            jar = jar_loader(domain_name=".aliyun.com")
        except TypeError:
            jar = jar_loader()
    except Exception as error:
        raise CliError(f"读取 {browser} Cookie 失败: {error}") from error

    pairs: list[str] = []
    seen: set[str] = set()
    for cookie in jar:
        domain = (getattr(cookie, "domain", "") or "").lower()
        if "aliyun.com" not in domain:
            continue
        name = getattr(cookie, "name", "")
        value = getattr(cookie, "value", "")
        if not name or not value or name in seen:
            continue
        seen.add(name)
        pairs.append(f"{name}={value}")

    if not pairs:
        raise CliError(f"未从 {browser} 中找到 aliyun.com 相关 Cookie")
    return "; ".join(pairs)


class ThoughtsAPI:
    def __init__(self, *, cookie_string: str):
        if not cookie_string:
            raise CliError("缺少知识库 Cookie")
        self.cookie_string = build_cookie_header(cookie_string)

    def get_workspace(self, workspace_id: str) -> dict[str, Any]:
        payload = self._request(
            "GET",
            f"/api/workspaces/{workspace_id}",
            referer=f"{THOUGHTS_BASE_URL}/workspaces/{workspace_id}/overview",
        )
        if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
            return payload["result"]
        if isinstance(payload, dict):
            return payload
        raise CliError("获取知识库信息失败")

    def list_nodes(self, workspace_id: str, *, parent_id: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"pageSize": 500, "withDetail": "true"}
        if parent_id:
            params["_parentId"] = parent_id
        payload = self._request(
            "GET",
            f"/api/workspaces/{workspace_id}/nodes",
            params=params,
            referer=f"{THOUGHTS_BASE_URL}/workspaces/{workspace_id}/overview",
        )
        result = payload.get("result") if isinstance(payload, dict) else None
        return result if isinstance(result, list) else []

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        referer: str,
    ) -> Any:
        try:
            response = requests.request(
                method=method,
                url=f"{THOUGHTS_BASE_URL}{path}",
                params=params,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json, text/plain, */*",
                    "Cookie": self.cookie_string,
                    "Referer": referer,
                },
                timeout=30,
            )
        except requests.RequestException as error:
            raise CliError(f"请求知识库接口失败: {error}") from error
        if response.status_code >= 400:
            raise CliError(f"请求知识库接口失败: {response.status_code} {response.text}")
        if not response.content:
            return {}
        return response.json()


class ThoughtsMarkdownRenderer:
    def render(self, blocks: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for block in blocks:
            rendered = self._render_block(block)
            if not rendered:
                continue
            lines.extend(rendered.rstrip().splitlines())
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def _render_block(self, block: dict[str, Any]) -> str:
        block_type = str(block.get("type") or "")
        if block_type in {"title", "paragraph", "heading"}:
            text = str(block.get("text") or "").strip()
            if not text:
                return ""
            if block_type == "title":
                return f"# {text}"
            if block_type == "heading":
                level = max(1, min(int(block.get("level") or 1), 6))
                return f'{"#" * level} {text}'
            return text
        if block_type == "list":
            items = block.get("items") or []
            rendered_items: list[str] = []
            ordered = bool(block.get("ordered"))
            prefix = "1." if ordered else "-"
            for item in items:
                text = str(item.get("text") or "").strip()
                if not text:
                    continue
                depth = max(0, int(item.get("depth") or 0))
                rendered_items.append(f'{"  " * depth}{prefix} {text}')
            return "\n".join(rendered_items)
        if block_type == "table":
            rows = block.get("rows") or []
            normalized_rows = [[self._escape_table_cell(cell) for cell in row] for row in rows if row]
            if not normalized_rows:
                return ""
            width = max(len(row) for row in normalized_rows)
            padded_rows = [row + [""] * (width - len(row)) for row in normalized_rows]
            header = padded_rows[0]
            lines = [
                f'| {" | ".join(header)} |',
                f'| {" | ".join(["---"] * width)} |',
            ]
            lines.extend(f'| {" | ".join(row)} |' for row in padded_rows[1:])
            return "\n".join(lines)
        if block_type == "image":
            src = str(block.get("src") or "").strip()
            if not src:
                return ""
            alt = str(block.get("alt") or "").strip()
            return f"![{alt}]({src})"
        return ""

    @staticmethod
    def _escape_table_cell(value: Any) -> str:
        return str(value or "").replace("|", r"\|")


class ThoughtsDomExporter:
    _EXTRACTION_SCRIPT = r"""
    (editor) => {
      const normalizeText = (value) =>
        (value || "")
          .replace(/\uFEFF/g, "")
          .replace(/\u00A0/g, " ")
          .replace(/\r/g, "")
          .replace(/[ \t]+\n/g, "\n")
          .replace(/\n[ \t]+/g, "\n")
          .replace(/[ \t]{2,}/g, " ")
          .trim();

      const inlineText = (node) => {
        if (!node) return "";
        if (node.nodeType === Node.TEXT_NODE) return node.textContent || "";
        if (node.nodeType !== Node.ELEMENT_NODE) return "";
        const element = node;
        const tag = element.tagName.toLowerCase();
        if (tag === "br") return "\n";
        if (tag === "img") return "";
        if (element.getAttribute("contenteditable") === "false" && !element.querySelector("img")) {
          return "";
        }
        const text = Array.from(element.childNodes).map(inlineText).join("");
        const normalized = normalizeText(text);
        if (!normalized && tag !== "a") {
          return "";
        }
        if (tag === "strong" || tag === "b") {
          return `**${normalized}**`;
        }
        if (tag === "em" || tag === "i") {
          return `*${normalized}*`;
        }
        if (tag === "code") {
          return `\`${normalized}\``;
        }
        if (tag === "a") {
          const href = element.getAttribute("href") || "";
          return href ? `[${normalized || href}](${href})` : normalized;
        }
        return text;
      };

      const blocks = [];
      const headingLevelMap = {
        "header-one": 2,
        "header-two": 3,
        "header-three": 4,
        "header-four": 5,
      };

      const pushParagraph = (node) => {
        const text = normalizeText(inlineText(node));
        if (text) {
          blocks.push({ type: "paragraph", text });
        }
      };

      Array.from(editor.children).forEach((child) => {
        const type = child.getAttribute("data-type") || "";

        if (type === "title") {
          const text = normalizeText(inlineText(child.querySelector("h1") || child));
          if (text) {
            blocks.push({ type: "title", text });
          }
          return;
        }

        if (headingLevelMap[type]) {
          const text = normalizeText(inlineText(child.querySelector("h1,h2,h3,h4,h5,h6") || child));
          if (text) {
            blocks.push({ type: "heading", level: headingLevelMap[type], text });
          }
          return;
        }

        if (type === "paragraph") {
          pushParagraph(child.querySelector("p") || child);
          return;
        }

        if (type === "table") {
          const table = child.querySelector("table");
          if (!table) {
            return;
          }
          const rows = Array.from(table.querySelectorAll("tr"))
            .map((row) =>
              Array.from(row.children).map((cell) =>
                normalizeText(inlineText(cell)).replace(/\n+/g, "<br>")
              )
            )
            .filter((row) => row.some((cell) => cell));
          if (rows.length) {
            blocks.push({ type: "table", rows });
          }
          return;
        }

        if (
          type === "unordered-list-wrapper" ||
          type === "ordered-list-wrapper" ||
          type === "todo-list-wrapper"
        ) {
          const items = Array.from(child.querySelectorAll("li"))
            .map((item) => {
              const className = item.getAttribute("class") || "";
              const depthMatch = className.match(/depth(\d+)/);
              const text = normalizeText(
                inlineText(item.querySelector(".text__2Esm") || item)
              ).replace(/\n+/g, " ");
              if (!text) {
                return null;
              }
              return {
                depth: depthMatch ? Number(depthMatch[1]) : 0,
                text,
              };
            })
            .filter(Boolean);
          if (items.length) {
            blocks.push({
              type: "list",
              ordered: type === "ordered-list-wrapper",
              items,
            });
          }
          return;
        }

        const image = child.querySelector("img");
        if (image) {
          const src = image.getAttribute("src") || "";
          if (src) {
            blocks.push({
              type: "image",
              src,
              alt: image.getAttribute("alt") || "",
            });
          }
          return;
        }

        pushParagraph(child);
      });

      return blocks;
    }
    """

    def __init__(self, *, renderer: ThoughtsMarkdownRenderer | None = None):
        self.renderer = renderer or ThoughtsMarkdownRenderer()

    def export_markdown(self, *, page, url: str) -> str:
        page.goto(url, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        if not page.locator('[data-slate-editor="true"]').count():
            return self._export_empty_document(page=page)
        page.wait_for_selector('[data-slate-editor="true"]', timeout=20000)
        page.wait_for_function(
            """() => {
              const title = document.querySelector('[data-slate-editor="true"] [data-type="title"] h1');
              return Boolean(title && title.innerText && title.innerText.trim());
            }""",
            timeout=10000,
        )
        blocks = page.locator('[data-slate-editor="true"]').evaluate(self._EXTRACTION_SCRIPT)
        markdown = self.renderer.render(blocks)
        if not markdown.strip():
            raise CliError("未从页面中提取到正文")
        return markdown

    @staticmethod
    def _export_empty_document(*, page) -> str:
        body_text = page.locator("body").inner_text()
        if "标准模板" not in body_text or "空白文档" not in body_text:
            raise CliError("未找到文档编辑区")
        title = (page.title() or "").split(" · ", 1)[0].strip()
        if not title:
            raise CliError("未识别空文档标题")
        return f"# {title}\n"


class ThoughtsDocumentExporter:
    def __init__(
        self,
        *,
        cookie_string: str,
        dom_exporter: ThoughtsDomExporter | None = None,
    ):
        self.cookie_string = cookie_string
        self.dom_exporter = dom_exporter or ThoughtsDomExporter()

    def export_documents(
        self,
        *,
        workspace_id: str,
        documents: list[dict[str, Any]],
        output_dir: Path,
        concurrency: int = 3,
    ) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        if not documents:
            return {"downloaded_files": [], "failures": []}

        worker_count = self._normalize_concurrency(concurrency=concurrency, document_count=len(documents))
        indexed_documents = list(enumerate(documents))
        worker_inputs = [indexed_documents[index::worker_count] for index in range(worker_count)]

        batch_results: list[dict[str, Any]] = []
        if worker_count == 1:
            batch_results.append(self._export_document_batch(indexed_documents=worker_inputs[0], output_dir=output_dir))
        else:
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = [
                    executor.submit(self._export_document_batch, indexed_documents=batch, output_dir=output_dir)
                    for batch in worker_inputs
                    if batch
                ]
                for future in futures:
                    batch_results.append(future.result())

        downloaded_entries: list[tuple[int, str]] = []
        failure_entries: list[tuple[int, dict[str, str]]] = []
        for batch_result in batch_results:
            downloaded_entries.extend(batch_result["downloaded_files"])
            failure_entries.extend(batch_result["failures"])

        downloaded_entries.sort(key=lambda item: item[0])
        failure_entries.sort(key=lambda item: item[0])
        return {
            "downloaded_files": [path for _, path in downloaded_entries],
            "failures": [item for _, item in failure_entries],
        }

    def _export_document_batch(
        self,
        *,
        indexed_documents: list[tuple[int, dict[str, Any]]],
        output_dir: Path,
    ) -> dict[str, Any]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise CliError("缺少 playwright 依赖，请重新安装 CLI") from error

        downloaded_files: list[tuple[int, str]] = []
        failures: list[tuple[int, dict[str, str]]] = []
        cookie_dicts = self._build_context_cookies()
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except Exception as error:
                raise CliError(
                    f"启动 Chromium 失败: {error}。如首次使用，请先执行 `playwright install chromium`"
                ) from error
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            try:
                context.route("**/*", self._handle_route)
                context.add_cookies(cookie_dicts)
                page = context.new_page()
                for index, document in indexed_documents:
                    target_path = self._target_path(output_dir=output_dir, document=document)
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        if target_path.exists():
                            target_path.unlink()
                        markdown = self.dom_exporter.export_markdown(page=page, url=document["url"])
                        target_path.write_text(markdown, encoding="utf-8")
                        downloaded_files.append((index, str(target_path)))
                    except Exception as error:
                        try:
                            self._export_markdown_from_ui(page=page, url=document["url"], target_path=target_path)
                            downloaded_files.append((index, str(target_path)))
                        except Exception as fallback_error:
                            failures.append(
                                (
                                    index,
                                    {
                                        "id": str(document["id"]),
                                        "title": str(document["title"]),
                                        "path": document["relative_path"],
                                        "message": f"{error}; fallback: {fallback_error}",
                                    },
                                )
                            )
            finally:
                context.close()
                browser.close()
        return {"downloaded_files": downloaded_files, "failures": failures}

    @staticmethod
    def _normalize_concurrency(*, concurrency: int, document_count: int) -> int:
        if concurrency < 1:
            raise CliError("`--concurrency` 必须大于 0")
        return min(concurrency, document_count)

    @staticmethod
    def _handle_route(route, request) -> None:
        if request.resource_type in {"font", "image", "media"}:
            route.abort()
            return
        route.continue_()

    def _build_context_cookies(self) -> list[dict[str, str]]:
        context_cookies: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str, str]] = set()
        for item in parse_cookie_string(self.cookie_string):
            domains = [str(item.get("domain") or "").strip()] if item.get("domain") else [".aliyun.com", "thoughts.aliyun.com"]
            for domain in domains:
                if not domain:
                    continue
                cookie = {
                    "name": item["name"],
                    "value": item["value"],
                    "domain": domain,
                    "path": str(item.get("path") or "/"),
                }
                for field in ("expires", "httpOnly", "sameSite", "secure"):
                    if field in item:
                        cookie[field] = item[field]
                key = (cookie["name"], cookie["domain"], cookie["path"])
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                context_cookies.append(cookie)
        return context_cookies

    @staticmethod
    def _target_path(*, output_dir: Path, document: dict[str, Any]) -> Path:
        relative_path = Path(document["relative_path"])
        return output_dir / relative_path

    @staticmethod
    def _find_first(page, selectors: list[str]):
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if locator.count() and locator.is_visible():
                    return locator
            except Exception:
                continue
        return None

    def _export_markdown_from_ui(self, *, page, url: str, target_path: Path) -> None:
        page.goto(url, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        more_button = self._find_first(
            page,
            [
                ".tool-icon__305j.more__3hHl",
                '[aria-label="更多"]',
                '[title="更多"]',
                ".anticon-ellipsis",
                '[class*="more"]',
            ],
        )
        if not more_button:
            raise CliError("未找到导出菜单")
        more_button.click()
        page.wait_for_timeout(500)

        export_trigger = page.locator("li.item__2iIF").filter(has_text="导出为").first.locator(".trigger__3_t3")
        try:
            if export_trigger.count() and export_trigger.is_visible():
                export_trigger.hover()
                page.wait_for_timeout(500)
        except Exception:
            pass

        export_menu = page.get_by_text("导出为").first
        if export_menu.count():
            try:
                export_menu.hover()
                page.wait_for_timeout(500)
            except Exception:
                try:
                    export_menu.click()
                    page.wait_for_timeout(500)
                except Exception:
                    pass

        markdown_option = page.get_by_text("导出 Markdown").first
        if not markdown_option.count():
            raise CliError("未找到 Markdown 导出入口")

        with page.expect_download(timeout=15000) as download_info:
            markdown_option.click()
        download = download_info.value
        download.save_as(str(target_path))


class ThoughtsDownloader:
    def __init__(
        self,
        *,
        cookie_string: str,
        api: ThoughtsAPI | None = None,
        exporter: ThoughtsDocumentExporter | None = None,
    ):
        self.api = api or ThoughtsAPI(cookie_string=cookie_string)
        self.exporter = exporter or ThoughtsDocumentExporter(cookie_string=cookie_string)

    def download_workspace(self, *, url: str, output_dir: str | None, concurrency: int = 3) -> dict[str, Any]:
        workspace_id = extract_workspace_id(url)
        workspace = self.api.get_workspace(workspace_id)
        documents = self._collect_documents(
            workspace_id=workspace_id,
            parent_id=None,
            path_parts=[],
            seen_paths=set(),
        )
        root_name = sanitize_filename(str(workspace.get("name") or workspace_id))
        target_dir = Path(output_dir) if output_dir else Path(root_name)
        export_result = self.exporter.export_documents(
            workspace_id=workspace_id,
            documents=documents,
            output_dir=target_dir,
            concurrency=concurrency,
        )
        return {
            "workspace": {
                "id": workspace_id,
                "name": workspace.get("name") or root_name,
            },
            "output_dir": str(target_dir.resolve()),
            "documents": {
                "total": len(documents),
                "downloaded": len(export_result["downloaded_files"]),
                "failed": len(export_result["failures"]),
            },
            "failures": export_result["failures"],
        }

    def _collect_documents(
        self,
        *,
        workspace_id: str,
        parent_id: str | None,
        path_parts: list[str],
        seen_paths: set[str],
    ) -> list[dict[str, Any]]:
        documents: list[dict[str, Any]] = []
        for node in self.api.list_nodes(workspace_id, parent_id=parent_id):
            node_type = str(node.get("type") or "")
            title = sanitize_filename(str(node.get("title") or "untitled"))
            node_id = str(node.get("_id") or "")
            current_parts = [*path_parts, title]
            if node_type == "folder" and node_id:
                documents.extend(
                    self._collect_documents(
                        workspace_id=workspace_id,
                        parent_id=node_id,
                        path_parts=current_parts,
                        seen_paths=seen_paths,
                    )
                )
                continue
            if node_type != "document" or not node_id:
                continue
            relative_path = Path(*current_parts).with_suffix(".md")
            relative_path_text = relative_path.as_posix()
            path_key = relative_path_text.lower()
            if path_key in seen_paths:
                relative_path = relative_path.with_name(f"{relative_path.stem}__{node_id}.md")
                relative_path_text = relative_path.as_posix()
            seen_paths.add(relative_path_text.lower())
            documents.append(
                {
                    "id": node_id,
                    "title": title,
                    "relative_path": relative_path_text,
                    "url": f"{THOUGHTS_BASE_URL}/workspaces/{workspace_id}/docs/{node_id}",
                }
            )
        return documents


class ThoughtsKnowledgeService:
    def download(
        self,
        *,
        url: str,
        output_dir: str | None = None,
        cookie: str | None = None,
        cookie_file: str | None = None,
        browser: str | None = None,
        concurrency: int = 3,
    ) -> dict[str, Any]:
        cookie_string = self._resolve_cookie(cookie=cookie, cookie_file=cookie_file, browser=browser)
        downloader = ThoughtsDownloader(cookie_string=cookie_string)
        return downloader.download_workspace(url=url, output_dir=output_dir, concurrency=concurrency)

    @staticmethod
    def _resolve_cookie(*, cookie: str | None, cookie_file: str | None, browser: str | None) -> str:
        normalized_cookie = (cookie or "").strip()
        normalized_cookie_file = (cookie_file or "").strip()
        normalized_browser = (browser or "").strip().lower()
        provided_auth_count = sum(bool(item) for item in (normalized_cookie, normalized_cookie_file, normalized_browser))
        if provided_auth_count > 1:
            raise CliError("`--cookie`、`--cookie-file` 和 `--browser` 只能三选一")
        if normalized_cookie:
            return normalized_cookie
        if normalized_cookie_file:
            try:
                return Path(normalized_cookie_file).read_text(encoding="utf-8")
            except OSError as error:
                raise CliError(f"读取 Cookie 文件失败: {error}") from error
        if normalized_browser:
            return load_browser_cookie_string(normalized_browser)
        raise CliError("必须提供 `--cookie`、`--cookie-file` 或 `--browser`")
