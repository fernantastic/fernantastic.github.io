#!/usr/bin/env python3

import cgi
import html
import json
import mimetypes
import os
import posixpath
import re
import shutil
import subprocess
import tempfile
import urllib.parse
from collections import OrderedDict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
CMS_DIR = ROOT / "cms"
CONTENT_DIR = ROOT / "content"
PROJECTS_DIR = CONTENT_DIR / "projects"
RAW_ASSETS_DIR = ROOT / "assets" / "raw-static-assets" / "projects"
STATIC_ASSETS_DIR = ROOT / "static" / "projects"
STATIC_DIR = ROOT / "static"
PREPARE_SCRIPT = ROOT / "prepare-static-assets.sh"
INDEX_FILE = CONTENT_DIR / "_index.md"
SIDEBAR_FILE = CONTENT_DIR / "_sidebar.md"
MAX_UPLOAD_BYTES = 1024 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".webm",
    ".avi",
    ".ogv",
    ".gif",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}
PROJECT_FIELDS = [
    "draft",
    "title",
    "home_img",
    "home_title",
    "home_subtitle",
    "side",
    "description",
]
IMAGE_EXTENSIONS = {".gif", ".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".ogv"}
IMAGE_SHORTCODE_RE = re.compile(r'{{<\s*img\s+"([^"]+)"\s+"([^"]*)"\s*>}}', re.MULTILINE)
IMAGE_PAIR_SHORTCODE_RE = re.compile(r'{{<\s*imgpair\s+"([^"]*)"\s+"([^"]*)"\s+"([^"]+)"\s*>}}', re.MULTILINE)
VIDEO_SHORTCODE_RE = re.compile(r'{{<\s*video\s+"([^"]+)"\s*>}}', re.MULTILINE)
YOUTUBE_SHORTCODE_RE = re.compile(r'{{<\s*youtube\s+"([^"]+)"\s*>}}', re.MULTILINE)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value:
      raise ValueError("Slug cannot be empty.")
    return value


def parse_front_matter(text: str) -> Tuple[OrderedDict, str]:
    if not text.startswith("+++\n"):
        return OrderedDict(), text
    end = text.find("\n+++\n", 4)
    if end == -1:
        raise ValueError("Invalid front matter.")
    front_matter = text[4:end]
    body = text[end + 5 :]
    data = parse_simple_toml(front_matter)
    return data, body.lstrip("\n")


def parse_simple_toml(text: str) -> OrderedDict:
    data = OrderedDict()
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value == '"""':
            parts = []
            while i < len(lines):
                current = lines[i]
                i += 1
                if current == '"""':
                    break
                parts.append(current)
            data[key] = "\n".join(parts)
            continue
        if raw_value in {"true", "false"}:
            data[key] = raw_value == "true"
            continue
        if raw_value.startswith('"') and raw_value.endswith('"'):
            data[key] = raw_value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            continue
        data[key] = raw_value
    return data


def format_toml_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return '""'
    text = str(value)
    if "\n" in text:
        return '"""\n' + text.rstrip("\n") + '\n"""'
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def dump_front_matter(data: OrderedDict) -> str:
    lines = ["+++"]
    for key, value in data.items():
        lines.append(f"{key} = {format_toml_value(value)}")
    lines.append("+++")
    return "\n".join(lines)


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def project_path(slug: str) -> Path:
    safe_slug = slugify(slug)
    return PROJECTS_DIR / f"{safe_slug}.md"


def load_project(slug: str) -> Dict:
    path = project_path(slug)
    if not path.exists():
        raise FileNotFoundError(f"Project '{slug}' not found.")
    data, body = parse_front_matter(read_text_file(path))
    ordered = OrderedDict()
    for field in PROJECT_FIELDS:
        if field in data:
            ordered[field] = data[field]
    for key, value in data.items():
        if key not in ordered:
            ordered[key] = value
    return {
        "slug": slugify(path.stem),
        "path": str(path.relative_to(ROOT)),
        "meta": ordered,
        "body": body,
        "blocks": parse_body_blocks(body),
        "image_options": list_image_options(),
        "video_options": list_video_options(),
    }


def save_project(slug: str, payload: Dict, *, creating: bool = False) -> Dict:
    safe_slug = slugify(slug)
    path = project_path(safe_slug)
    if creating and path.exists():
        raise FileExistsError(f"Project '{safe_slug}' already exists.")

    existing_meta = OrderedDict()
    existing_body = ""
    if path.exists():
        existing_meta, existing_body = parse_front_matter(read_text_file(path))

    if "blocks" in payload:
        body = serialize_body_blocks(payload.get("blocks", []))
    else:
        body = payload.get("body", existing_body).rstrip() + "\n"
    meta_input = payload.get("meta", {})
    merged = OrderedDict()

    for field in PROJECT_FIELDS:
        if field in meta_input:
            merged[field] = meta_input[field]
        elif field in existing_meta:
            merged[field] = existing_meta[field]

    for key, value in existing_meta.items():
        if key not in merged:
            merged[key] = value

    for key, value in meta_input.items():
        if key not in merged:
            merged[key] = value

    if "draft" not in merged:
        merged["draft"] = False
    if "title" not in merged or not str(merged["title"]).strip():
        merged["title"] = safe_slug.replace("-", " ").title()

    text = dump_front_matter(merged) + "\n\n" + body
    write_atomic(path, text)
    return load_project(safe_slug)


def parse_body_blocks(body: str) -> List[Dict[str, str]]:
    blocks: List[Dict[str, str]] = []
    matches = []
    matches.extend(("image", match) for match in IMAGE_SHORTCODE_RE.finditer(body))
    matches.extend(("image_pair", match) for match in IMAGE_PAIR_SHORTCODE_RE.finditer(body))
    matches.extend(("video", match) for match in VIDEO_SHORTCODE_RE.finditer(body))
    matches.extend(("youtube", match) for match in YOUTUBE_SHORTCODE_RE.finditer(body))
    matches.sort(key=lambda item: item[1].start())

    cursor = 0
    for block_type, match in matches:
        before = body[cursor:match.start()]
        if before.strip():
            blocks.append({"type": "markdown", "content": before.strip()})
        if block_type == "image_pair":
            blocks.append({
                "type": "image_pair",
                "left_path": match.group(1),
                "right_path": match.group(2),
                "split": match.group(3),
            })
        elif block_type == "youtube":
            blocks.append({"type": "youtube", "value": match.group(1)})
        else:
            blocks.append({"type": block_type, "path": match.group(1)})
        cursor = match.end()
    tail = body[cursor:]
    if tail.strip():
        blocks.append({"type": "markdown", "content": tail.strip()})
    if not blocks:
        blocks.append({"type": "markdown", "content": ""})
    return blocks


def serialize_body_blocks(blocks: List[Dict[str, str]]) -> str:
    parts: List[str] = []
    for block in blocks:
        block_type = block.get("type")
        if block_type == "image":
            path = str(block.get("path", "")).strip()
            if path:
                parts.append(f'{{{{< img "{path}" "" >}}}}')
        elif block_type == "image_pair":
            left_path = str(block.get("left_path", "")).strip()
            right_path = str(block.get("right_path", "")).strip()
            split = str(block.get("split", "50")).strip() or "50"
            if left_path or right_path:
                parts.append(f'{{{{< imgpair "{left_path}" "{right_path}" "{split}" >}}}}')
        elif block_type == "video":
            path = str(block.get("path", "")).strip()
            if path:
                parts.append(f'{{{{< video "{path}" >}}}}')
        elif block_type == "youtube":
            value = str(block.get("value", "")).strip()
            if value:
                parts.append(f'{{{{< youtube "{value}" >}}}}')
        elif block_type == "markdown":
            content = str(block.get("content", "")).strip()
            if content:
                parts.append(content)
    return ("\n\n".join(parts).rstrip() + "\n") if parts else ""


def list_project_assets(slug: str) -> Dict[str, List[str]]:
    safe_slug = slugify(slug)
    raw_dir = RAW_ASSETS_DIR / safe_slug
    static_dir = STATIC_ASSETS_DIR / safe_slug
    raw_files = sorted(
        str(path.relative_to(ROOT)).replace(os.sep, "/")
        for path in raw_dir.rglob("*")
        if path.is_file()
    ) if raw_dir.exists() else []
    static_files = sorted(
        str(path.relative_to(ROOT)).replace(os.sep, "/")
        for path in static_dir.rglob("*")
        if path.is_file()
    ) if static_dir.exists() else []
    return {"raw": raw_files, "static": static_files}


def list_image_options() -> List[str]:
    if not STATIC_ASSETS_DIR.exists():
        return []
    options = []
    for path in sorted(STATIC_ASSETS_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            options.append(str(path.relative_to(ROOT / "static")).replace(os.sep, "/"))
    return options


def list_video_options() -> List[str]:
    if not STATIC_ASSETS_DIR.exists():
        return []
    options = []
    for path in sorted(STATIC_ASSETS_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            options.append(str(path.relative_to(ROOT / "static")).replace(os.sep, "/"))
    return options


def uploaded_blocks_for_files(slug: str, saved_raw_paths: List[str]) -> List[Dict[str, str]]:
    blocks: List[Dict[str, str]] = []
    safe_slug = slugify(slug)
    static_project_dir = STATIC_ASSETS_DIR / safe_slug

    for raw_path in saved_raw_paths:
        raw_name = Path(raw_path).name
        stem = Path(raw_name).stem
        ext = Path(raw_name).suffix.lower()

        candidates: List[Path] = []
        if ext in IMAGE_EXTENSIONS:
            candidates.append(static_project_dir / raw_name)
            candidates.append(static_project_dir / f"{stem}.jpg")
            candidates.append(static_project_dir / f"{stem}.jpeg")
            candidates.append(static_project_dir / f"{stem}.png")
            candidates.append(static_project_dir / f"{stem}.webp")
            candidates.append(static_project_dir / f"{stem}.gif")
        elif ext in VIDEO_EXTENSIONS:
            candidates.append(static_project_dir / f"{stem}.webm")
            candidates.append(static_project_dir / f"{stem}.ogv")
            candidates.append(static_project_dir / f"{stem}.mp4")
            candidates.append(static_project_dir / raw_name)

        seen = set()
        resolved = None
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate.exists() and candidate.is_file():
                resolved = candidate
                break

        if not resolved:
            continue

        rel = str(resolved.relative_to(STATIC_DIR)).replace(os.sep, "/")
        suffix = resolved.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            blocks.append({"type": "image", "path": rel})
        elif suffix in VIDEO_EXTENSIONS:
            blocks.append({"type": "video", "path": rel})

    return blocks


def list_projects() -> List[Dict]:
    home_order = load_home_order()
    home_positions = {slug: index for index, slug in enumerate(home_order)}
    projects = []
    for path in sorted(PROJECTS_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        project = load_project(path.stem)
        meta = project["meta"]
        projects.append(
            {
                "slug": project["slug"],
                "title": str(meta.get("title", path.stem)),
                "home_title": str(meta.get("home_title", meta.get("title", path.stem))).strip(),
                "home_img": str(meta.get("home_img", "")),
                "home_subtitle": str(meta.get("home_subtitle", "")),
                "is_on_home": project["slug"] in home_positions,
                "home_position": home_positions.get(project["slug"]),
            }
        )
    projects.sort(key=lambda item: (item["home_position"] is None, item["home_position"] or 9999, item["slug"]))
    return projects


HOME_SHORTCODE_RE = re.compile(r'{{<\s*homeproject\s+"([^"]+)"\s*>}}')


def load_home_file() -> Tuple[str, str]:
    text = read_text_file(INDEX_FILE)
    meta, body = parse_front_matter(text)
    return dump_front_matter(meta), body


def load_home_order() -> List[str]:
    _, body = load_home_file()
    return HOME_SHORTCODE_RE.findall(body)


def load_sidebar_content() -> Dict[str, str]:
    text = read_text_file(SIDEBAR_FILE)
    _, body = parse_front_matter(text)
    return {"body": body.rstrip("\n")}


def save_sidebar_content(body: str) -> Dict[str, str]:
    text = read_text_file(SIDEBAR_FILE)
    meta, _ = parse_front_matter(text)
    new_text = dump_front_matter(meta) + "\n\n" + body.rstrip() + "\n"
    write_atomic(SIDEBAR_FILE, new_text)
    return load_sidebar_content()


def save_home_order(order: List[str]) -> None:
    slugs = [slugify(slug) for slug in order]
    seen = []
    for slug in slugs:
        if slug not in seen:
            seen.append(slug)
    front_matter, _ = load_home_file()
    body = "\n\n".join(f'{{{{< homeproject "{slug}" >}}}}' for slug in seen)
    write_atomic(INDEX_FILE, front_matter + "\n\n" + body + "\n")


def run_prepare_assets(slug: str | None = None, paths: List[str] | None = None) -> None:
    command = ["bash", str(PREPARE_SCRIPT)]
    if paths:
        for path in paths:
            command.append(str((ROOT / path).resolve()))
    elif slug:
        command.append(str(RAW_ASSETS_DIR / slugify(slug)))
    subprocess.run(command, cwd=str(ROOT), check=True)


def handle_uploads(slug: str, form: cgi.FieldStorage) -> Dict:
    safe_slug = slugify(slug)
    target_dir = RAW_ASSETS_DIR / safe_slug
    target_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    files = form["files"] if "files" in form else []
    if not isinstance(files, list):
        files = [files]

    for item in files:
        if not getattr(item, "filename", ""):
            continue
        filename = Path(item.filename).name
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_UPLOAD_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {filename}")
        destination = target_dir / filename
        with destination.open("wb") as handle:
            shutil.copyfileobj(item.file, handle)
        saved.append(str(destination.relative_to(ROOT)).replace(os.sep, "/"))

    run_prepare_assets(paths=saved)
    return {
        "saved": saved,
        "image_options": list_image_options(),
        "video_options": list_video_options(),
        "new_blocks": uploaded_blocks_for_files(safe_slug, saved),
    }


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ferfolio CMS</title>
  <link rel="stylesheet" href="/app.css">
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-main">
        <div class="sidebar-block">
          <button id="edit-home-button">Edit Homepage</button>
          <button id="edit-sidebar-button">Edit Sidebar</button>
        </div>
        <div class="sidebar-block">
          <h2>Projects</h2>
          <button id="new-project-button" class="danger">New Project</button>
        </div>
        <div class="sidebar-block">
          <div id="project-list" class="project-list"></div>
        </div>
      </div>
      <div class="sidebar-footer">
        <button id="refresh-assets-button">Refresh Assets Cache</button>
      </div>
    </aside>
    <main class="main">
      <section id="home-editor" class="panel hidden">
        <div class="panel-header">
          <h1>Homepage Projects</h1>
          <p>Select which projects appear on home and drag to reorder them.</p>
        </div>
        <div id="home-items" class="home-items"></div>
        <div class="actions">
          <button id="save-home-button" class="primary">Save Home Order</button>
        </div>
      </section>

      <section id="project-editor" class="panel hidden">
        <div class="panel-header panel-header-split">
          <div>
            <h1 id="project-editor-title">Project</h1>
            <p>Edit metadata and body. Changes write back to the project markdown file.</p>
          </div>
          <button id="save-project-button" class="primary" type="submit" form="project-form">Save Project</button>
        </div>
        <form id="project-form">
          <div class="grid">
            <label>
              <span>Slug</span>
              <input name="slug" id="project-slug" required>
            </label>
            <label class="checkbox">
              <input type="checkbox" name="draft" id="project-draft">
              <span>Draft</span>
            </label>
          </div>
          <label>
            <span>Home image</span>
            <div class="image-picker">
              <select name="home_img" id="project-home-img"></select>
              <img id="project-home-img-preview" class="image-preview" alt="">
            </div>
          </label>
          <label>
            <span>Home title</span>
            <input name="home_title" id="project-home-title">
          </label>
          <label>
            <span>Home subtitle</span>
            <input name="home_subtitle" id="project-home-subtitle">
          </label>
          <label>
            <span>Title</span>
            <input name="title" id="project-title">
          </label>
          <label>
            <span>Side</span>
            <textarea name="side" id="project-side" rows="6"></textarea>
          </label>
          <label>
            <span>Description</span>
            <textarea name="description" id="project-description" rows="8"></textarea>
          </label>
          <div class="body-editor">
            <div class="body-editor-header">
              <span>Body blocks</span>
              <div class="actions compact">
                <button id="add-markdown-block" type="button">Add Markdown</button>
                <button id="add-image-block" type="button">Add Image</button>
                <button id="add-image-pair-block" type="button">Add Image Pair</button>
                <button id="add-video-block" type="button">Add Video</button>
                <button id="add-youtube-block" type="button">Add YouTube</button>
              </div>
            </div>
            <div id="body-blocks" class="body-blocks"></div>
          </div>
          <div id="upload-dropzone" class="dropzone">
            <strong>Drop assets here</strong>
            <span>Files go to assets/raw-static-assets/projects/&lt;slug&gt; and are processed into static/.</span>
          </div>
        </form>
      </section>

      <section id="sidebar-editor" class="panel hidden">
        <div class="panel-header">
          <h1>Sidebar Markdown</h1>
          <p>Edit the markdown body of content/_sidebar.md.</p>
        </div>
        <form id="sidebar-form">
          <label>
            <span>Sidebar body</span>
            <textarea id="sidebar-body" rows="16"></textarea>
          </label>
          <div class="actions">
            <button id="save-sidebar-button" class="primary" type="submit">Save Sidebar</button>
          </div>
        </form>
      </section>

      <section id="empty-state" class="panel">
        <div class="panel-header">
          <h1>Ferfolio CMS</h1>
          <p>Select a project on the left or edit the homepage order.</p>
        </div>
      </section>
    </main>
  </div>
  <script src="/app.js" defer></script>
</body>
</html>
"""


APP_CSS = """
:root {
  --bg: #f7f5f1;
  --panel: #ffffff;
  --line: #d8d1c7;
  --text: #171411;
  --muted: #6a6259;
  --accent: #0b6ef3;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: linear-gradient(180deg, #f5f1ea 0%, #f8f7f4 100%);
  color: var(--text);
}
.app {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 22rem minmax(0, 1fr);
}
.sidebar {
  border-right: 1px solid var(--line);
  padding: 1.25rem;
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: auto;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.sidebar-block + .sidebar-block { margin-top: 1.5rem; }
.sidebar h2, .panel h1, .panel h3 { margin: 0 0 0.75rem; }
.sidebar-main {
  display: grid;
  gap: 1.5rem;
}
.sidebar-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
}
.project-list { display: grid; gap: 0.5rem; }
.project-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 0.75rem;
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 0.5rem;
  cursor: pointer;
}
.project-item.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(11,110,243,0.15);
}
.main {
  padding: 1.5rem;
}
.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 0.75rem;
  padding: 1.25rem;
  max-width: 70rem;
}
.hidden { display: none; }
.panel-header p { color: var(--muted); margin-top: 0; }
.panel-header-split {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}
button, input, textarea, select {
  font: inherit;
}
button {
  border: 1px solid var(--line);
  background: white;
  color: var(--text);
  border-radius: 0.5rem;
  padding: 0.7rem 1rem;
  cursor: pointer;
}
button.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}
button.danger {
  background: #c9382c;
  border-color: #c9382c;
  color: white;
}
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem;
}
label { display: grid; gap: 0.35rem; margin-bottom: 1rem; }
label span { font-size: 0.9rem; color: var(--muted); }
input, textarea, select {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 0.5rem;
  padding: 0.7rem 0.8rem;
  background: #fffdfa;
}
.image-picker {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 4rem;
  gap: 0.75rem;
  align-items: center;
}
.image-preview {
  width: 4rem;
  height: 4rem;
  object-fit: cover;
  border-radius: 0.4rem;
  border: 1px solid var(--line);
  background: #f2ede6;
  display: none;
}
.image-preview.visible {
  display: block;
}
.image-pair-picker {
  display: grid;
  gap: 0.75rem;
}
.image-pair-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}
.image-pair-slider {
  display: grid;
  gap: 0.35rem;
}
.image-pair-slider output {
  color: var(--muted);
  font-size: 0.9rem;
}
.checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.checkbox input { width: auto; }
.home-items {
  display: grid;
  gap: 0.75rem;
}
.home-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.75rem;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 0.6rem;
  padding: 0.85rem 1rem;
  background: #fffdfa;
}
.home-item[draggable="true"] { cursor: grab; }
.home-item.dragging { opacity: 0.45; }
.drag-handle { font-size: 1.1rem; color: var(--muted); }
.dropzone {
  border: 2px dashed var(--line);
  border-radius: 0.75rem;
  padding: 1.2rem;
  margin-bottom: 1rem;
  background: #faf7f2;
  display: grid;
  gap: 0.35rem;
  text-align: center;
}
.dropzone.drag-over {
  border-color: var(--accent);
  background: #eef5ff;
}
.actions { margin-top: 1rem; display: flex; gap: 0.75rem; }
.status {
  margin-top: 1rem;
  color: var(--muted);
}
.body-editor {
  margin-bottom: 1rem;
}
.body-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
  color: var(--muted);
  font-size: 0.9rem;
}
.body-blocks {
  display: grid;
  gap: 0.75rem;
}
.body-block {
  border: 1px solid var(--line);
  border-radius: 0.75rem;
  background: #fffdfa;
  padding: 0.9rem;
  display: grid;
  gap: 0.75rem;
}
.body-block.dragging {
  opacity: 0.45;
}
.body-block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}
.body-block-meta {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--muted);
  font-size: 0.9rem;
}
.drag-handle-button {
  border: 0;
  background: transparent;
  padding: 0;
  color: var(--muted);
  cursor: grab;
}
.body-block textarea {
  min-height: 9rem;
}
.body-block input[type="text"] {
  width: 100%;
}
.actions.compact {
  margin-top: 0;
}
@media (max-width: 960px) {
  .app { grid-template-columns: 1fr; }
  .sidebar {
    position: static;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }
  .sidebar-main,
  .sidebar-footer {
    display: grid;
  }
  .grid { grid-template-columns: 1fr; }
}
"""


APP_JS = r"""
const state = {
  projects: [],
  currentProject: null,
  creating: false,
  imageOptions: [],
  videoOptions: [],
};

const els = {
  projectList: document.getElementById("project-list"),
  editHomeButton: document.getElementById("edit-home-button"),
  editSidebarButton: document.getElementById("edit-sidebar-button"),
  newProjectButton: document.getElementById("new-project-button"),
  refreshAssetsButton: document.getElementById("refresh-assets-button"),
  homeEditor: document.getElementById("home-editor"),
  homeItems: document.getElementById("home-items"),
  saveHomeButton: document.getElementById("save-home-button"),
  projectEditor: document.getElementById("project-editor"),
  sidebarEditor: document.getElementById("sidebar-editor"),
  emptyState: document.getElementById("empty-state"),
  projectEditorTitle: document.getElementById("project-editor-title"),
  saveProjectButton: document.getElementById("save-project-button"),
  form: document.getElementById("project-form"),
  slug: document.getElementById("project-slug"),
  title: document.getElementById("project-title"),
  homeImg: document.getElementById("project-home-img"),
  homeImgPreview: document.getElementById("project-home-img-preview"),
  homeTitle: document.getElementById("project-home-title"),
  homeSubtitle: document.getElementById("project-home-subtitle"),
  draft: document.getElementById("project-draft"),
  side: document.getElementById("project-side"),
  description: document.getElementById("project-description"),
  bodyBlocks: document.getElementById("body-blocks"),
  dropzone: document.getElementById("upload-dropzone"),
  addMarkdownBlock: document.getElementById("add-markdown-block"),
  addImageBlock: document.getElementById("add-image-block"),
  addImagePairBlock: document.getElementById("add-image-pair-block"),
  addVideoBlock: document.getElementById("add-video-block"),
  addYoutubeBlock: document.getElementById("add-youtube-block"),
  sidebarForm: document.getElementById("sidebar-form"),
  sidebarBody: document.getElementById("sidebar-body"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  const type = response.headers.get("content-type") || "";
  return type.includes("application/json") ? response.json() : response.text();
}

function showPanel(name) {
  els.homeEditor.classList.add("hidden");
  els.projectEditor.classList.add("hidden");
  els.sidebarEditor.classList.add("hidden");
  els.emptyState.classList.add("hidden");
  if (name === "home") els.homeEditor.classList.remove("hidden");
  else if (name === "project") els.projectEditor.classList.remove("hidden");
  else if (name === "sidebar") els.sidebarEditor.classList.remove("hidden");
  else els.emptyState.classList.remove("hidden");
}

function renderProjectList() {
  els.projectList.innerHTML = "";
  state.projects.forEach((project) => {
    const button = document.createElement("button");
    button.className = "project-item" + (state.currentProject === project.slug ? " active" : "");
    button.type = "button";
    button.innerHTML = `<strong>${escapeHtml(project.home_title || project.title || project.slug)}</strong><div>${escapeHtml(project.slug)}</div>`;
    button.addEventListener("click", () => loadProject(project.slug));
    els.projectList.appendChild(button);
  });
}

function escapeHtml(value) {
  return (value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function refreshProjects() {
  state.projects = await api("/api/projects");
  state.imageOptions = await api("/api/images");
  state.videoOptions = await api("/api/videos");
  renderProjectList();
  renderHomeItems();
}

function renderHomeItems() {
  const items = [...state.projects].sort((a, b) => {
    const ap = a.home_position ?? 9999;
    const bp = b.home_position ?? 9999;
    return ap - bp || a.slug.localeCompare(b.slug);
  });

  els.homeItems.innerHTML = "";
  items.forEach((project) => {
    const row = document.createElement("label");
    row.className = "home-item";
    row.draggable = true;
    row.dataset.slug = project.slug;
    row.innerHTML = `
      <span class="drag-handle">::</span>
      <div>
        <strong>${escapeHtml(project.home_title || project.title || project.slug)}</strong>
        <div>${escapeHtml(project.slug)}</div>
      </div>
      <input type="checkbox" ${project.is_on_home ? "checked" : ""}>
    `;

    row.addEventListener("dragstart", () => row.classList.add("dragging"));
    row.addEventListener("dragend", () => row.classList.remove("dragging"));
    row.addEventListener("dragover", (event) => {
      event.preventDefault();
      const dragging = els.homeItems.querySelector(".dragging");
      if (!dragging || dragging === row) return;
      const rect = row.getBoundingClientRect();
      const shouldInsertAfter = event.clientY > rect.top + rect.height / 2;
      els.homeItems.insertBefore(dragging, shouldInsertAfter ? row.nextSibling : row);
    });

    els.homeItems.appendChild(row);
  });
}

function collectHomeOrder() {
  const rows = [...els.homeItems.querySelectorAll(".home-item")];
  return rows
    .filter((row) => row.querySelector('input[type="checkbox"]').checked)
    .map((row) => row.dataset.slug);
}

async function loadProject(slug) {
  const data = await api(`/api/project/${slug}`);
  state.currentProject = slug;
  state.creating = false;
  els.projectEditorTitle.textContent = `Project: ${slug}`;
  const meta = data.meta || {};
  els.slug.value = data.slug || "";
  els.slug.disabled = true;
  renderImageOptions(data.image_options || [], meta.home_img || "");
  els.title.value = meta.title || "";
  els.homeTitle.value = meta.home_title || "";
  els.homeSubtitle.value = meta.home_subtitle || "";
  els.draft.checked = Boolean(meta.draft);
  els.side.value = meta.side || "";
  els.description.value = meta.description || "";
  state.imageOptions = data.image_options || [];
  state.videoOptions = data.video_options || [];
  renderBodyBlocks(data.blocks || [{ type: "markdown", content: data.body || "" }]);
  renderProjectList();
  showPanel("project");
}

function renderImageOptions(options, selected) {
  els.homeImg.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "Select an image";
  els.homeImg.appendChild(empty);
  options.forEach((item) => {
    const option = document.createElement("option");
    option.value = item;
    option.textContent = item;
    if (item === selected) option.selected = true;
    els.homeImg.appendChild(option);
  });
  if (selected && !options.includes(selected)) {
    const option = document.createElement("option");
    option.value = selected;
    option.textContent = `${selected} (missing)`;
    option.selected = true;
    els.homeImg.appendChild(option);
  }
  updateImagePreview(els.homeImg, els.homeImgPreview);
}

function imageUrl(path) {
  if (!path) return "";
  const cleaned = path.replace(/^\/+/, "");
  const encoded = cleaned
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
  return `/${encoded}`;
}

function updateImagePreview(select, preview) {
  const value = select.value;
  if (!value) {
    preview.removeAttribute("src");
    preview.classList.remove("visible");
    preview.alt = "";
    return;
  }
  preview.src = imageUrl(value);
  preview.alt = value;
  preview.classList.add("visible");
}

function blockImageOptions(selected) {
  const options = state.imageOptions || [];
  let html = '<option value="">Select an image</option>';
  options.forEach((item) => {
    const isSelected = item === selected ? " selected" : "";
    html += `<option value="${escapeHtml(item)}"${isSelected}>${escapeHtml(item)}</option>`;
  });
  if (selected && !options.includes(selected)) {
    html += `<option value="${escapeHtml(selected)}" selected>${escapeHtml(selected)} (missing)</option>`;
  }
  return html;
}

function blockVideoOptions(selected) {
  const options = state.videoOptions || [];
  let html = '<option value="">Select a video</option>';
  options.forEach((item) => {
    const isSelected = item === selected ? " selected" : "";
    html += `<option value="${escapeHtml(item)}"${isSelected}>${escapeHtml(item)}</option>`;
  });
  if (selected && !options.includes(selected)) {
    html += `<option value="${escapeHtml(selected)}" selected>${escapeHtml(selected)} (missing)</option>`;
  }
  return html;
}

function createBodyBlock(block = { type: "markdown", content: "" }) {
  const row = document.createElement("div");
  row.className = "body-block";
  row.draggable = true;
  row.dataset.type = block.type;

  let content = `<textarea class="body-block-markdown" rows="8">${escapeHtml(block.content || "")}</textarea>`;
  if (block.type === "image") {
    content = `<div class="image-picker"><select class="body-block-image">${blockImageOptions(block.path || "")}</select><img class="image-preview body-block-preview" alt=""></div>`;
  } else if (block.type === "image_pair") {
    const split = Number(block.split || 50);
    content = `
      <div class="image-pair-picker">
        <div class="image-pair-grid">
          <div class="image-picker">
            <select class="body-block-image-pair-left">${blockImageOptions(block.left_path || "")}</select>
            <img class="image-preview body-block-preview-left" alt="">
          </div>
          <div class="image-picker">
            <select class="body-block-image-pair-right">${blockImageOptions(block.right_path || "")}</select>
            <img class="image-preview body-block-preview-right" alt="">
          </div>
        </div>
        <label class="image-pair-slider">
          <span>Left image width</span>
          <input class="body-block-image-pair-split" type="range" min="20" max="80" step="1" value="${split}">
          <output>${split}% / ${100 - split}%</output>
        </label>
      </div>
    `;
  } else if (block.type === "video") {
    content = `<select class="body-block-video">${blockVideoOptions(block.path || "")}</select>`;
  } else if (block.type === "youtube") {
    content = `<input class="body-block-youtube" type="text" value="${escapeHtml(block.value || "")}" placeholder="YouTube URL or video ID">`;
  }

  row.innerHTML = `
    <div class="body-block-head">
      <div class="body-block-meta">
        <button class="drag-handle-button" type="button">::</button>
        <strong>${block.type === "image" ? "Image" : block.type === "image_pair" ? "Image Pair" : block.type === "video" ? "Video" : block.type === "youtube" ? "YouTube" : "Markdown"}</strong>
      </div>
      <button class="remove-block" type="button">Remove</button>
    </div>
    ${content}
  `;

  row.addEventListener("dragstart", () => row.classList.add("dragging"));
  row.addEventListener("dragend", () => row.classList.remove("dragging"));
  row.addEventListener("dragover", (event) => {
    event.preventDefault();
    const dragging = els.bodyBlocks.querySelector(".dragging");
    if (!dragging || dragging === row) return;
    const rect = row.getBoundingClientRect();
    const after = event.clientY > rect.top + rect.height / 2;
    els.bodyBlocks.insertBefore(dragging, after ? row.nextSibling : row);
  });
  row.querySelector(".remove-block").addEventListener("click", () => {
    row.remove();
    if (!els.bodyBlocks.children.length) {
      renderBodyBlocks([{ type: "markdown", content: "" }], []);
    }
  });
  if (block.type === "image") {
    const select = row.querySelector(".body-block-image");
    const preview = row.querySelector(".body-block-preview");
    updateImagePreview(select, preview);
    select.addEventListener("change", () => updateImagePreview(select, preview));
  } else if (block.type === "image_pair") {
    const leftSelect = row.querySelector(".body-block-image-pair-left");
    const rightSelect = row.querySelector(".body-block-image-pair-right");
    const leftPreview = row.querySelector(".body-block-preview-left");
    const rightPreview = row.querySelector(".body-block-preview-right");
    const splitInput = row.querySelector(".body-block-image-pair-split");
    const output = row.querySelector("output");
    const syncSplit = () => {
      const value = Number(splitInput.value || 50);
      output.value = `${value}% / ${100 - value}%`;
      output.textContent = output.value;
    };
    updateImagePreview(leftSelect, leftPreview);
    updateImagePreview(rightSelect, rightPreview);
    leftSelect.addEventListener("change", () => updateImagePreview(leftSelect, leftPreview));
    rightSelect.addEventListener("change", () => updateImagePreview(rightSelect, rightPreview));
    splitInput.addEventListener("input", syncSplit);
    syncSplit();
  }
  return row;
}

function renderBodyBlocks(blocks) {
  els.bodyBlocks.innerHTML = "";
  blocks.forEach((block) => {
    els.bodyBlocks.appendChild(createBodyBlock(block));
  });
  if (!els.bodyBlocks.children.length) {
    els.bodyBlocks.appendChild(createBodyBlock({ type: "markdown", content: "" }));
  }
}

function startNewProject() {
  state.currentProject = null;
  state.creating = true;
  els.projectEditorTitle.textContent = "New Project";
  els.form.reset();
  els.slug.disabled = false;
  renderImageOptions(state.imageOptions || [], "");
  renderBodyBlocks([{ type: "markdown", content: "" }], []);
  renderProjectList();
  showPanel("project");
}

function collectBodyBlocks() {
  return [...els.bodyBlocks.querySelectorAll(".body-block")].map((block) => {
    if (block.dataset.type === "image") {
      return {
        type: "image",
        path: block.querySelector(".body-block-image").value,
      };
    }
    if (block.dataset.type === "image_pair") {
      return {
        type: "image_pair",
        left_path: block.querySelector(".body-block-image-pair-left").value,
        right_path: block.querySelector(".body-block-image-pair-right").value,
        split: block.querySelector(".body-block-image-pair-split").value,
      };
    }
    if (block.dataset.type === "video") {
      return {
        type: "video",
        path: block.querySelector(".body-block-video").value,
      };
    }
    if (block.dataset.type === "youtube") {
      return {
        type: "youtube",
        value: block.querySelector(".body-block-youtube").value,
      };
    }
    return {
      type: "markdown",
      content: block.querySelector(".body-block-markdown").value,
    };
  });
}

function projectPayload() {
  return {
    meta: {
      draft: els.draft.checked,
      title: els.title.value,
      home_img: els.homeImg.value,
      home_title: els.homeTitle.value,
      home_subtitle: els.homeSubtitle.value,
      side: els.side.value,
      description: els.description.value,
    },
    blocks: collectBodyBlocks(),
  };
}

async function saveProject(event) {
  event.preventDefault();
  const slug = els.slug.value.trim();
  if (!slug) {
    alert("Slug is required.");
    return;
  }
  const path = state.creating ? "/api/projects" : `/api/project/${slug}`;
  const method = state.creating ? "POST" : "PUT";
  const payload = state.creating ? { slug, ...projectPayload() } : projectPayload();
  const saved = await api(path, { method, body: JSON.stringify(payload) });
  await refreshProjects();
  await loadProject(saved.slug);
}

async function saveHome() {
  const order = collectHomeOrder();
  await api("/api/home", {
    method: "POST",
    body: JSON.stringify({ order }),
  });
  await refreshProjects();
  alert("Homepage order saved.");
}

async function loadSidebar() {
  const data = await api("/api/sidebar");
  els.sidebarBody.value = data.body || "";
  showPanel("sidebar");
}

async function saveSidebar(event) {
  event.preventDefault();
  await api("/api/sidebar", {
    method: "POST",
    body: JSON.stringify({ body: els.sidebarBody.value }),
  });
  alert("Sidebar saved.");
}

async function refreshAssetsCache() {
  const result = await api("/api/assets/refresh", {
    method: "POST",
    body: JSON.stringify({ slug: state.currentProject || "" }),
  });
  state.imageOptions = result.image_options || [];
  state.videoOptions = result.video_options || [];
  renderImageOptions(state.imageOptions, els.homeImg.value);
  const imageSelects = els.bodyBlocks.querySelectorAll(".body-block-image, .body-block-image-pair-left, .body-block-image-pair-right");
  imageSelects.forEach((select) => {
    const current = select.value;
    select.innerHTML = blockImageOptions(current);
    const preview = select.parentElement.querySelector("img");
    updateImagePreview(select, preview);
  });
  const videoSelects = els.bodyBlocks.querySelectorAll(".body-block-video");
  videoSelects.forEach((select) => {
    const current = select.value;
    select.innerHTML = blockVideoOptions(current);
  });
  alert("Assets cache refreshed.");
}

async function uploadFiles(files) {
  const slug = els.slug.value.trim();
  if (!slug) {
    alert("Save the project with a slug before uploading assets.");
    return;
  }
  const formData = new FormData();
  [...files].forEach((file) => formData.append("files", file));
  const result = await api(`/api/project/${slug}/upload`, { method: "POST", body: formData });
  state.imageOptions = result.image_options || [];
  state.videoOptions = result.video_options || [];
  renderImageOptions(result.image_options || [], els.homeImg.value);
  const imageSelects = els.bodyBlocks.querySelectorAll(".body-block-image, .body-block-image-pair-left, .body-block-image-pair-right");
  imageSelects.forEach((select) => {
    const current = select.value;
    select.innerHTML = blockImageOptions(current);
    const preview = select.parentElement.querySelector("img");
    updateImagePreview(select, preview);
  });
  const videoSelects = els.bodyBlocks.querySelectorAll(".body-block-video");
  videoSelects.forEach((select) => {
    const current = select.value;
    select.innerHTML = blockVideoOptions(current);
  });
  (result.new_blocks || []).forEach((block) => {
    els.bodyBlocks.appendChild(createBodyBlock(block));
  });
}

els.editHomeButton.addEventListener("click", async () => {
  await refreshProjects();
  showPanel("home");
});
els.editSidebarButton.addEventListener("click", loadSidebar);
els.newProjectButton.addEventListener("click", startNewProject);
els.refreshAssetsButton.addEventListener("click", refreshAssetsCache);
els.form.addEventListener("submit", saveProject);
els.saveHomeButton.addEventListener("click", saveHome);
els.sidebarForm.addEventListener("submit", saveSidebar);
els.homeImg.addEventListener("change", () => updateImagePreview(els.homeImg, els.homeImgPreview));
els.addMarkdownBlock.addEventListener("click", () => {
  els.bodyBlocks.appendChild(createBodyBlock({ type: "markdown", content: "" }));
});
els.addImageBlock.addEventListener("click", () => {
  els.bodyBlocks.appendChild(createBodyBlock({ type: "image", path: "" }));
});
els.addImagePairBlock.addEventListener("click", () => {
  els.bodyBlocks.appendChild(createBodyBlock({ type: "image_pair", left_path: "", right_path: "", split: "50" }));
});
els.addVideoBlock.addEventListener("click", () => {
  els.bodyBlocks.appendChild(createBodyBlock({ type: "video", path: "" }));
});
els.addYoutubeBlock.addEventListener("click", () => {
  els.bodyBlocks.appendChild(createBodyBlock({ type: "youtube", value: "" }));
});

["dragenter", "dragover"].forEach((type) => {
  els.dropzone.addEventListener(type, (event) => {
    event.preventDefault();
    els.dropzone.classList.add("drag-over");
  });
});
["dragleave", "drop"].forEach((type) => {
  els.dropzone.addEventListener(type, (event) => {
    event.preventDefault();
    els.dropzone.classList.remove("drag-over");
  });
});
els.dropzone.addEventListener("drop", (event) => uploadFiles(event.dataTransfer.files));

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
    if (!els.projectEditor.classList.contains("hidden")) {
      event.preventDefault();
      els.saveProjectButton.click();
    }
  }
});

refreshProjects().catch((error) => {
  console.error(error);
  alert(error.message);
});
"""


class CMSHandler(BaseHTTPRequestHandler):
    server_version = "FerfolioCMS/0.1"

    def _send(self, status=HTTPStatus.OK, body="", content_type="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status=HTTPStatus.OK):
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, status, message):
        self._send(status, message)

    def do_GET(self):
        try:
            path = self.path.split("?", 1)[0]
            if path == "/":
                return self._send(body=INDEX_HTML, content_type="text/html; charset=utf-8")
            if path == "/app.css":
                return self._send(body=APP_CSS, content_type="text/css; charset=utf-8")
            if path == "/app.js":
                return self._send(body=APP_JS, content_type="application/javascript; charset=utf-8")
            if path.startswith("/projects/") or path.startswith("/images/") or path.startswith("/js/") or path.startswith("/css/"):
                return self._serve_static_file(path)
            if path == "/api/projects":
                return self._json(list_projects())
            if path == "/api/images":
                return self._json(list_image_options())
            if path == "/api/videos":
                return self._json(list_video_options())
            if path == "/api/sidebar":
                return self._json(load_sidebar_content())
            if path == "/api/home":
                return self._json({"order": load_home_order(), "projects": list_projects()})
            if path.startswith("/api/project/"):
                slug = path.removeprefix("/api/project/")
                return self._json(load_project(slug))
            return self._error(HTTPStatus.NOT_FOUND, "Not found.")
        except FileNotFoundError as exc:
            self._error(HTTPStatus.NOT_FOUND, str(exc))
        except Exception as exc:  # pragma: no cover
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_POST(self):
        try:
            path = self.path.split("?", 1)[0]
            if path == "/api/home":
                payload = self._read_json()
                save_home_order(payload.get("order", []))
                return self._json({"ok": True})
            if path == "/api/sidebar":
                payload = self._read_json()
                return self._json(save_sidebar_content(payload.get("body", "")))
            if path == "/api/assets/refresh":
                payload = self._read_json()
                run_prepare_assets(payload.get("slug"))
                return self._json({
                    "ok": True,
                    "image_options": list_image_options(),
                    "video_options": list_video_options(),
                })
            if path == "/api/projects":
                payload = self._read_json()
                slug = payload.get("slug", "")
                project = save_project(slug, payload, creating=True)
                return self._json(project, HTTPStatus.CREATED)
            if path.startswith("/api/project/") and path.endswith("/upload"):
                slug = path.removeprefix("/api/project/").removesuffix("/upload").strip("/")
                form = self._read_form_data()
                result = handle_uploads(slug, form)
                return self._json(result, HTTPStatus.CREATED)
            self._error(HTTPStatus.NOT_FOUND, "Not found.")
        except (ValueError, FileExistsError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except subprocess.CalledProcessError as exc:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Asset processing failed: {exc}")
        except Exception as exc:  # pragma: no cover
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_PUT(self):
        try:
            path = self.path.split("?", 1)[0]
            if path.startswith("/api/project/"):
                slug = path.removeprefix("/api/project/")
                payload = self._read_json()
                project = save_project(slug, payload, creating=False)
                return self._json(project)
            self._error(HTTPStatus.NOT_FOUND, "Not found.")
        except (ValueError, FileNotFoundError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_UPLOAD_BYTES:
            raise ValueError("Request too large.")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8") or "{}")

    def _read_form_data(self):
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": self.headers.get("Content-Type"),
            "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
        }
        return cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=environ)

    def _serve_static_file(self, request_path: str):
        relative = urllib.parse.unquote(request_path.lstrip("/"))
        target = (STATIC_DIR / relative).resolve()
        static_root = STATIC_DIR.resolve()
        if static_root not in target.parents and target != static_root:
            return self._error(HTTPStatus.FORBIDDEN, "Forbidden.")
        if not target.exists() or not target.is_file():
            return self._error(HTTPStatus.NOT_FOUND, "Not found.")
        content_type, _ = mimetypes.guess_type(str(target))
        self._send(
            body=target.read_bytes(),
            content_type=content_type or "application/octet-stream",
        )


def main():
    port = int(os.environ.get("FERFOLIO_CMS_PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), CMSHandler)
    print(f"Ferfolio CMS running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
