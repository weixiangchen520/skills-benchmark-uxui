"""Rendered artifact snapshots for UX/UI grading."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any

from pydantic import BaseModel, Field


class RenderSnapshot(BaseModel):
    artifact_path: str
    url: str = ""
    viewport: dict[str, int] = Field(default_factory=dict)
    title: str = ""
    section_count: int = 0
    heading_count: int = 0
    button_count: int = 0
    image_count: int = 0
    link_count: int = 0
    text_chars: int = 0
    body_text: str = ""
    screenshot_path: str | None = None
    used_playwright: bool = False
    error: str | None = None
    dom_metrics: dict[str, Any] = Field(default_factory=dict)

    def as_prompt_context(self, max_body_chars: int = 4_000) -> str:
        payload = {
            "artifact_path": self.artifact_path,
            "url": self.url,
            "viewport": self.viewport,
            "title": self.title,
            "section_count": self.section_count,
            "heading_count": self.heading_count,
            "button_count": self.button_count,
            "image_count": self.image_count,
            "link_count": self.link_count,
            "text_chars": self.text_chars,
            "screenshot_path": self.screenshot_path,
            "used_playwright": self.used_playwright,
            "error": self.error,
            "dom_metrics": self.dom_metrics,
            "body_text_excerpt": self.body_text[:max_body_chars],
        }
        return "Render snapshot:\n" + json.dumps(payload, ensure_ascii=True, indent=2)


class _HtmlSnapshotParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tag_counts: dict[str, int] = {}
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
            return
        if self._ignored_depth:
            return
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped)


def resolve_artifact_path(workdir: Path, artifact: str | None) -> Path:
    artifact_name = artifact or "index.html"
    path = Path(artifact_name)
    if not path.is_absolute():
        path = workdir / path
    return path


def _squash_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _snapshot_from_html(
    *,
    artifact_path: Path,
    url: str,
    viewport: dict[str, int],
    html: str,
    error: str | None = None,
    max_text_chars: int = 20_000,
) -> RenderSnapshot:
    parser = _HtmlSnapshotParser()
    parser.feed(html)

    tag_counts = parser.tag_counts
    body_text = _squash_text(" ".join(parser.text_parts))
    title = _squash_text(" ".join(parser.title_parts))
    heading_count = sum(tag_counts.get(f"h{level}", 0) for level in range(1, 7))
    image_count = sum(tag_counts.get(tag, 0) for tag in ("img", "svg", "canvas", "video"))

    return RenderSnapshot(
        artifact_path=str(artifact_path),
        url=url,
        viewport=viewport,
        title=title,
        section_count=tag_counts.get("section", 0),
        heading_count=heading_count,
        button_count=tag_counts.get("button", 0),
        image_count=image_count,
        link_count=tag_counts.get("a", 0),
        text_chars=len(body_text),
        body_text=body_text[:max_text_chars],
        used_playwright=False,
        error=error,
        dom_metrics={"source": "html_parser", "tag_counts": tag_counts},
    )


def _remote_requests_blocker(route: Any) -> None:
    url = route.request.url
    if url.startswith(("about:", "blob:", "data:", "file:")):
        route.continue_()
    else:
        route.abort()


def _collect_page_metrics(page: Any, max_text_chars: int) -> dict[str, Any]:
    return page.evaluate(
        """
        (maxTextChars) => {
          const count = (selector) => document.querySelectorAll(selector).length;
          const bodyText = (document.body?.innerText || "").replace(/\\s+/g, " ").trim();
          const headings = Array.from(
            document.querySelectorAll("h1,h2,h3,h4,h5,h6")
          ).map((node) => node.innerText.replace(/\\s+/g, " ").trim()).filter(Boolean);
          const sections = Array.from(document.querySelectorAll("section")).map(
            (node, index) => ({
              index: index + 1,
              heading: (
                node.querySelector("h1,h2,h3,h4,h5,h6")?.innerText || ""
              ).replace(/\\s+/g, " ").trim(),
              text_chars: (node.innerText || "").replace(/\\s+/g, " ").trim().length
            })
          );
          const root = document.documentElement;
          return {
            title: document.title || "",
            section_count: count("section"),
            heading_count: count("h1,h2,h3,h4,h5,h6"),
            button_count: count("button,[role=button]"),
            image_count: count("img,svg,canvas,video"),
            link_count: count("a[href]"),
            text_chars: bodyText.length,
            body_text: bodyText.slice(0, maxTextChars),
            headings,
            sections,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight,
            scroll_width: root.scrollWidth,
            scroll_height: root.scrollHeight,
            overflowing_x: root.scrollWidth > window.innerWidth + 1
          };
        }
        """,
        max_text_chars,
    )


def render_html_snapshot(
    *,
    workdir: Path,
    artifact: str | None = "index.html",
    output_dir: Path | None = None,
    viewport: tuple[int, int] = (1280, 720),
    timeout_ms: int = 5_000,
    max_text_chars: int = 20_000,
    use_playwright: bool = True,
) -> RenderSnapshot:
    artifact_path = resolve_artifact_path(workdir, artifact)
    viewport_dict = {"width": int(viewport[0]), "height": int(viewport[1])}
    url = ""
    if artifact_path.exists():
        url = artifact_path.resolve().as_uri()

    if not artifact_path.exists():
        return RenderSnapshot(
            artifact_path=str(artifact_path),
            url=url,
            viewport=viewport_dict,
            error=f"artifact missing: {artifact_path}",
        )
    if not artifact_path.is_file():
        return RenderSnapshot(
            artifact_path=str(artifact_path),
            url=url,
            viewport=viewport_dict,
            error=f"artifact is not a file: {artifact_path}",
        )

    html = artifact_path.read_text(encoding="utf-8", errors="replace")
    fallback = _snapshot_from_html(
        artifact_path=artifact_path,
        url=url,
        viewport=viewport_dict,
        html=html,
        max_text_chars=max_text_chars,
    )
    if not use_playwright:
        return fallback

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        fallback.error = f"playwright unavailable: {exc}"
        return fallback

    screenshot_path: Path | None = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport=viewport_dict)
                page.route("**/*", _remote_requests_blocker)
                page.goto(url, wait_until="load", timeout=timeout_ms)
                page.wait_for_timeout(100)
                metrics = _collect_page_metrics(page, max_text_chars)
                if output_dir is not None:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    screenshot_path = output_dir / f"{artifact_path.stem}-{viewport[0]}x{viewport[1]}.png"
                    page.screenshot(path=str(screenshot_path), full_page=True)
            finally:
                browser.close()
    except Exception as exc:  # noqa: BLE001
        fallback.error = f"playwright render failed: {exc}"
        return fallback

    return RenderSnapshot(
        artifact_path=str(artifact_path),
        url=url,
        viewport=viewport_dict,
        title=str(metrics.get("title") or ""),
        section_count=int(metrics.get("section_count") or 0),
        heading_count=int(metrics.get("heading_count") or 0),
        button_count=int(metrics.get("button_count") or 0),
        image_count=int(metrics.get("image_count") or 0),
        link_count=int(metrics.get("link_count") or 0),
        text_chars=int(metrics.get("text_chars") or 0),
        body_text=str(metrics.get("body_text") or ""),
        screenshot_path=str(screenshot_path) if screenshot_path else None,
        used_playwright=True,
        dom_metrics={
            "source": "playwright",
            "headings": metrics.get("headings", []),
            "sections": metrics.get("sections", []),
            "viewport_width": metrics.get("viewport_width"),
            "viewport_height": metrics.get("viewport_height"),
            "scroll_width": metrics.get("scroll_width"),
            "scroll_height": metrics.get("scroll_height"),
            "overflowing_x": metrics.get("overflowing_x"),
        },
    )
