"""Semantic vector search endpoints."""

import logging
import os

from fastapi import APIRouter, HTTPException

from api.dependencies import get_search_agent, get_storage_helper
from api.models import SearchRequest, SearchResponse, SearchResultItem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def vector_search(body: SearchRequest):
    """Perform semantic vector search across video frame summaries."""
    try:
        agent = get_search_agent(body.vector_store_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    frames_container = os.environ["AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"]
    projection = ["id", "frame_id", "asset_name", "summary"]

    raw_results = agent.perform_vector_search(
        collection_name=frames_container,
        query=body.query,
        attr_name="summary_vector",
        projection=projection,
        limit=body.limit,
    )

    if not raw_results:
        return SearchResponse(query=body.query, results=[])

    results = [
        SearchResultItem(
            frame_id=r.get("frame_id"),
            asset_name=r.get("asset_name", ""),
            summary=r.get("summary", ""),
            similarity_score=r.get("similarityScore") or r.get("SimilarityScore"),
        )
        for r in raw_results
    ]

    # Fetch video asset info for the top result
    video_url: str | None = None
    asset_info: dict | None = None
    top_asset_name = results[0].asset_name
    if top_asset_name:
        assets_container = os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"]
        asset_list = agent.perform_search(assets_container, filter={"asset_name": top_asset_name}, limit=1)
        if asset_list:
            storage = get_storage_helper()
            video_url = storage.generate_blob_sas_token(asset_list[0]["blob_video_key"])
            # Strip internal fields
            keys_to_remove = {
                "_id", "_rid", "_self", "_etag", "_attachments", "_ts",
                "video_summary_vector", "audio_summary_vector",
            }
            asset_info = {k: v for k, v in asset_list[0].items() if k not in keys_to_remove}

    return SearchResponse(
        query=body.query,
        results=results,
        video_url=video_url,
        asset_info=asset_info,
    )
