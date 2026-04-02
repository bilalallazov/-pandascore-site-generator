from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .settings import GENERATED_DIR, SITE_LOGO_URL, SITE_NAME, SITE_URL, TIMEZONE


@dataclass(frozen=True)
class RenderContext:
    site_name: str
    site_url: str
    site_logo_url: str
    timezone_name: str
    generated_at_utc: str


def jinja_env(templates_dir: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
    return env


def org_schema(site_name: str, site_url: str, site_logo_url: str) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site_name,
        "url": site_url,
    }
    if site_logo_url:
        schema["logo"] = site_logo_url
    return schema


def write_day_page(
    *,
    templates_dir: str,
    out_dir: Path,
    day_key: str,
    day_title: str,
    canonical_path: str,
    matches: list[dict[str, Any]],
) -> None:
    env = jinja_env(templates_dir)
    tpl = env.get_template("day.html")

    rc = RenderContext(
        site_name=SITE_NAME,
        site_url=SITE_URL,
        site_logo_url=SITE_LOGO_URL,
        timezone_name=TIMEZONE,
        generated_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )

    description = f"{day_title}: расписание и результаты киберспортивных матчей (все игры)."

    html = tpl.render(
        page={
            "day_key": day_key,
            "title": f"{day_title} — {rc.site_name}",
            "description": description,
            "canonical": f"{rc.site_url}{canonical_path}",
        },
        site={
            "name": rc.site_name,
            "url": rc.site_url,
            "timezone": rc.timezone_name,
            "generated_at_utc": rc.generated_at_utc,
        },
        org_schema=org_schema(rc.site_name, rc.site_url, rc.site_logo_url),
        matches=matches,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")


def write_index_page(*, templates_dir: str, out_path: Path) -> None:
    env = jinja_env(templates_dir)
    tpl = env.get_template("index.html")
    html = tpl.render(
        site={"name": SITE_NAME, "url": SITE_URL, "timezone": TIMEZONE},
        org_schema=org_schema(SITE_NAME, SITE_URL, SITE_LOGO_URL),
    )
    out_path.write_text(html, encoding="utf-8")


def ensure_generated_tree() -> None:
    Path(GENERATED_DIR).mkdir(parents=True, exist_ok=True)
    for key in ("yesterday", "today", "tomorrow"):
        Path(GENERATED_DIR, key).mkdir(parents=True, exist_ok=True)

