from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_index, get_library_service
from app.metadata.models import Metadata
from app.providers import get_tmdb
from app.scanner.index import LibraryIndex
from app.services.library_service import LibraryService

router = APIRouter(prefix="/api/shows", tags=["shows"])


def _artwork(meta: Metadata | None) -> dict:
    if meta is None:
        return {}
    return {name: str(path) for name, path in meta.artwork.model_dump(mode="json").items() if path}


def _artwork_urls(meta: Metadata | None, media_id: str | None) -> dict:
    if meta is None or not media_id:
        return {}
    return {
        name: f"/api/items/{media_id}/artwork/{name}"
        for name, path in meta.artwork.model_dump(mode="json").items()
        if path
    }


def _episode_summary(ep, meta: Metadata | None) -> dict:
    return {
        "media_id": ep.media_id,
        "title": ep.title,
        "series_title": ep.series_title,
        "season": ep.season,
        "episode": ep.episode,
        "display_title": ep.display_title,
        "has_metadata": meta is not None,
        "optimized": meta is not None and bool(meta.optimization.path) and Path(meta.optimization.path, "master.m3u8").is_file(),
        "artwork": _artwork(meta),
        "metadata": meta.model_dump(mode="json") if meta else None,
    }


@router.get("")
def list_shows(
    index: LibraryIndex = Depends(get_index),
    service: LibraryService = Depends(get_library_service),
) -> list[dict]:
    episodes = [ep for ep in index.all() if ep.kind == "episode"]
    grouped: dict[str, list] = {}
    for ep in episodes:
        key = ep.series_title or ep.title
        grouped.setdefault(key, []).append(ep)

    result = []
    for title, eps in grouped.items():
        eps.sort(key=lambda e: (e.season or 0, e.episode or 0))
        first = service.builder.load(eps[0].media_id)
        show_meta = first
        artwork = _artwork(show_meta)
        seasons = sorted({e.season for e in eps if e.season is not None})
        total_episodes = sum(
            len([e for e in eps if e.season == s]) for s in seasons
        )
        result.append(
            {
                "series_title": title,
                "tmdb_id": show_meta.tmdb_id if show_meta else None,
                "year": show_meta.year if show_meta else None,
                "rating": show_meta.rating if show_meta else None,
                "status": show_meta.status if show_meta else None,
                "overview": show_meta.overview if show_meta else None,
                "genres": show_meta.genres if show_meta else [],
                "networks": show_meta.networks if show_meta else [],
                "first_air_date": show_meta.first_air_date if show_meta else None,
                "last_air_date": show_meta.last_air_date if show_meta else None,
                "number_of_seasons": len(seasons),
                "number_of_episodes": total_episodes,
                "episode_count": len(eps),
                "artwork": artwork,
                "artwork_urls": _artwork_urls(show_meta, first.media_id),
                "episodes": [_episode_summary(ep, service.builder.load(ep.media_id)) for ep in eps],
            }
        )
    result.sort(key=lambda s: s["series_title"].lower())
    return result


@router.get("/{series_title}")
async def show_detail(
    series_title: str,
    index: LibraryIndex = Depends(get_index),
    service: LibraryService = Depends(get_library_service),
) -> dict:
    from urllib.parse import unquote

    title = unquote(series_title)
    eps = [ep for ep in index.all() if ep.kind == "episode" and (ep.series_title or ep.title) == title]
    if not eps:
        raise HTTPException(status_code=404, detail="Show not found")

    eps.sort(key=lambda e: (e.season or 0, e.episode or 0))
    metas = {ep.media_id: service.builder.load(ep.media_id) for ep in eps}
    show_meta = next((m for m in metas.values() if m is not None), None)
    artwork = _artwork(show_meta)

    show: dict = {
        "series_title": title,
        "tmdb_id": show_meta.tmdb_id if show_meta else None,
        "year": show_meta.year if show_meta else None,
        "rating": show_meta.rating if show_meta else None,
        "tagline": show_meta.tagline if show_meta else None,
        "status": show_meta.status if show_meta else None,
        "overview": show_meta.overview if show_meta else None,
        "genres": show_meta.genres if show_meta else [],
        "networks": show_meta.networks if show_meta else [],
        "creators": show_meta.creators if show_meta else [],
        "first_air_date": show_meta.first_air_date if show_meta else None,
        "last_air_date": show_meta.last_air_date if show_meta else None,
        "number_of_seasons": show_meta.number_of_seasons if show_meta else None,
        "number_of_episodes": show_meta.number_of_episodes if show_meta else None,
        "artwork": artwork,
        "artwork_urls": _artwork_urls(show_meta, eps[0].media_id),
    }

    # Fetch all seasons/episodes from TMDB if available, merge with local files
    seasons: dict[int, dict] = {}
    if show_meta and show_meta.tmdb_id:
        try:
            tmdb = get_tmdb()
            seasons_range = show_meta.number_of_seasons or max(
                (m.season for m in metas.values() if m is not None and m.season), default=1
            )
            for season_num in range(1, seasons_range + 1):
                season_data = await tmdb.season_details(show_meta.tmdb_id, season_num)
                season_eps = []
                for tmdb_ep in season_data.get("episodes", []):
                    ep_num = tmdb_ep.get("episode_number")
                    local = next(
                        (e for e in eps if e.season == season_num and e.episode == ep_num),
                        None,
                    )
                    local_meta = metas[local.media_id] if local else None
                    season_eps.append(
                        {
                            "episode_number": ep_num,
                            "title": tmdb_ep.get("name"),
                            "overview": tmdb_ep.get("overview"),
                            "air_date": tmdb_ep.get("air_date"),
                            "rating": tmdb_ep.get("vote_average"),
                            "runtime": tmdb_ep.get("runtime"),
                            "still": f"{'/api/items/' + local.media_id + '/artwork/still'}" if local_meta and local_meta.artwork.still else None,
                            "has_file": local is not None,
                            "optimized": local is not None
                            and local_meta is not None
                            and bool(local_meta.optimization.path)
                            and Path(local_meta.optimization.path, "master.m3u8").is_file(),
                            "media_id": local.media_id if local else None,
                            "local_title": local_meta.title if local_meta else None,
                        }
                    )
                if season_eps:
                    seasons[season_num] = {
                        "season_number": season_num,
                        "name": season_data.get("name") or f"Season {season_num}",
                        "episodes": season_eps,
                    }
        except Exception as exc:
            from app.utils.logging import logger

            logger.warning("TMDB season fetch failed for {}: {}", title, exc)

    # Fallback: only local episodes
    if not seasons:
        for season_num in sorted({e.season for e in eps if e.season is not None}):
            season_eps = []
            for e in eps:
                if e.season == season_num:
                    local_meta = metas[e.media_id]
                    season_eps.append(
                        {
                            "episode_number": e.episode,
                            "title": local_meta.title if local_meta else e.title,
                            "overview": local_meta.overview if local_meta else None,
                            "air_date": local_meta.air_date if local_meta else None,
                            "rating": local_meta.rating if local_meta else None,
                            "runtime": local_meta.runtime if local_meta else None,
                            "still": f"/api/items/{e.media_id}/artwork/still" if local_meta and local_meta.artwork.still else None,
                            "has_file": True,
                            "optimized": bool(local_meta.optimization.path)
                            and Path(local_meta.optimization.path, "master.m3u8").is_file()
                            if local_meta
                            else False,
                            "media_id": e.media_id,
                            "local_title": local_meta.title if local_meta else None,
                        }
                    )
            season_eps.sort(key=lambda x: x["episode_number"] or 0)
            seasons[season_num] = {
                "season_number": season_num,
                "name": f"Season {season_num}",
                "episodes": season_eps,
            }

    show["seasons"] = [seasons[k] for k in sorted(seasons.keys())]
    return show
