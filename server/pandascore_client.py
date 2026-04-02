from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterable

import requests


class PandaScoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class PandaScoreClient:
    base_url: str
    token: str
    page_size: int = 50
    max_pages: int = 10
    timeout_s: int = 20

    def _headers(self) -> dict[str, str]:
        if not self.token:
            raise PandaScoreError("Missing PANDASCORE_TOKEN")
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def _get(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}{path}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout_s)
        if resp.status_code == 429:
            # Very small backoff; generation is user-triggered.
            time.sleep(1.0)
            resp = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout_s)
        if not resp.ok:
            raise PandaScoreError(f"PandaScore API error {resp.status_code}: {resp.text}")
        data = resp.json()
        if not isinstance(data, list):
            raise PandaScoreError("Unexpected PandaScore response shape (expected list)")
        return data

    def iter_matches(
        self,
        *,
        kind: str,
        begin_at_gte: str,
        begin_at_lt: str,
    ) -> Iterable[dict[str, Any]]:
        """
        kind: 'past' -> /matches/past, 'upcoming' -> /matches/upcoming
        Date filtering uses range[begin_at] with a start..end interval.
        """
        if kind not in ("past", "upcoming"):
            raise ValueError("kind must be 'past' or 'upcoming'")

        path = f"/matches/{kind}"
        for page_num in range(1, self.max_pages + 1):
            params: dict[str, Any] = {
                "page[number]": page_num,
                "page[size]": self.page_size,
                "range[begin_at]": f"{begin_at_gte},{begin_at_lt}",
                "sort": "begin_at",
            }
            items = self._get(path, params=params)
            if not items:
                return
            for m in items:
                yield m

            if len(items) < self.page_size:
                return


def normalize_match(m: dict[str, Any]) -> dict[str, Any]:
    opponents = m.get("opponents") or []
    teams: list[dict[str, Any]] = []
    for entry in opponents:
        opp = (entry or {}).get("opponent") or {}
        if opp.get("name"):
            teams.append(
                {
                    "id": opp.get("id"),
                    "name": opp.get("name"),
                    "acronym": opp.get("acronym"),
                    "image_url": opp.get("image_url"),
                }
            )

    league = (m.get("league") or {}) if isinstance(m.get("league"), dict) else {}
    tournament = (m.get("tournament") or {}) if isinstance(m.get("tournament"), dict) else {}
    videogame = (m.get("videogame") or {}) if isinstance(m.get("videogame"), dict) else {}

    return {
        "id": m.get("id"),
        "slug": m.get("slug"),
        "name": m.get("name"),
        "status": m.get("status"),
        "begin_at": m.get("begin_at") or m.get("scheduled_at"),
        "end_at": m.get("end_at"),
        "league": {"name": league.get("name"), "image_url": league.get("image_url"), "slug": league.get("slug")},
        "tournament": {"name": tournament.get("name"), "slug": tournament.get("slug")},
        "videogame": {"name": videogame.get("name"), "slug": videogame.get("slug")},
        "teams": teams,
        "streams": m.get("streams_list") or [],
        "raw": m,
    }


def dedupe_and_sort(matches: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for m in matches:
        mid = str(m.get("id") or m.get("slug") or "")
        if not mid:
            continue
        by_id[mid] = m

    def sort_key(x: dict[str, Any]) -> str:
        return str(x.get("begin_at") or "")

    return sorted(by_id.values(), key=sort_key)

