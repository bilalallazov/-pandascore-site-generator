from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .pandascore_client import PandaScoreClient, dedupe_and_sort, normalize_match
from .render_site import ensure_generated_tree, write_day_page, write_index_page
from .settings import (
    DATA_DIR,
    GENERATED_DIR,
    MAX_PAGES,
    PAGE_SIZE,
    PANDASCORE_BASE_URL,
    PANDASCORE_TOKEN,
    TIMEZONE,
)
from .time_ranges import yesterday_today_tomorrow


APP_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = str(APP_ROOT / "templates")
STATIC_DIR = str(APP_ROOT / "static")

app = FastAPI(title="Esports Matches Site Generator")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _safe_read_generated(day_key: str) -> Path:
    out_path = Path(GENERATED_DIR, day_key, "index.html")
    if not out_path.exists():
        raise HTTPException(status_code=404, detail="Page not generated yet. Open / and click generate.")
    return out_path


@app.get("/", response_class=HTMLResponse)
def index() -> Response:
    # render index dynamically so it always works before generation
    tmp_dir = Path(GENERATED_DIR)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    index_path = tmp_dir / "_index.html"
    write_index_page(templates_dir=TEMPLATES_DIR, out_path=index_path)
    return FileResponse(index_path)


@app.post("/api/generate")
def generate() -> JSONResponse:
    ensure_generated_tree()

    if not PANDASCORE_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="Missing PANDASCORE_TOKEN env var. Get your token in PandaScore Dashboard and set it before generation.",
        )

    client = PandaScoreClient(
        base_url=PANDASCORE_BASE_URL,
        token=PANDASCORE_TOKEN,
        page_size=PAGE_SIZE,
        max_pages=MAX_PAGES,
    )

    ranges = yesterday_today_tomorrow(tz_name=TIMEZONE)

    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    def fetch_day(day_key: str) -> list[dict[str, Any]]:
        dr = ranges[day_key]
        begin = dr.start_utc_iso()
        end = dr.end_utc_iso()

        if day_key == "tomorrow":
            raw = list(client.iter_matches(kind="upcoming", begin_at_gte=begin, begin_at_lt=end))
        elif day_key == "yesterday":
            raw = list(client.iter_matches(kind="past", begin_at_gte=begin, begin_at_lt=end))
        else:
            raw = []
            raw.extend(client.iter_matches(kind="past", begin_at_gte=begin, begin_at_lt=end))
            raw.extend(client.iter_matches(kind="upcoming", begin_at_gte=begin, begin_at_lt=end))

        normalized = [normalize_match(m) for m in raw]
        normalized = dedupe_and_sort(normalized)
        (Path(DATA_DIR) / f"{day_key}.json").write_text(json.dumps(normalized, ensure_ascii=False), encoding="utf-8")
        return normalized

    try:
        yesterday_matches = fetch_day("yesterday")
        today_matches = fetch_day("today")
        tomorrow_matches = fetch_day("tomorrow")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    write_day_page(
        templates_dir=TEMPLATES_DIR,
        out_dir=Path(GENERATED_DIR, "yesterday"),
        day_key="yesterday",
        day_title="Матчи за вчера",
        canonical_path="/yesterday",
        matches=yesterday_matches,
    )
    write_day_page(
        templates_dir=TEMPLATES_DIR,
        out_dir=Path(GENERATED_DIR, "today"),
        day_key="today",
        day_title="Матчи за сегодня",
        canonical_path="/today",
        matches=today_matches,
    )
    write_day_page(
        templates_dir=TEMPLATES_DIR,
        out_dir=Path(GENERATED_DIR, "tomorrow"),
        day_key="tomorrow",
        day_title="Матчи на завтра",
        canonical_path="/tomorrow",
        matches=tomorrow_matches,
    )

    return JSONResponse({"ok": True, "redirect": "/today"})


@app.get("/yesterday", response_class=HTMLResponse)
def page_yesterday() -> Response:
    return FileResponse(_safe_read_generated("yesterday"))


@app.get("/today", response_class=HTMLResponse)
def page_today() -> Response:
    return FileResponse(_safe_read_generated("today"))


@app.get("/tomorrow", response_class=HTMLResponse)
def page_tomorrow() -> Response:
    return FileResponse(_safe_read_generated("tomorrow"))


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}

