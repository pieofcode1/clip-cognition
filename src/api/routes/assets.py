"""Endpoints for browsing stored video assets, frames, and blobs."""

import logging
import os

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import get_search_agent, get_storage_helper
from api.models import (
    BlobItem,
    BlobListResponse,
    FrameUrlResponse,
    VideoAssetDetailResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/videos", summary="List all processed video assets")
def list_video_assets(
    vector_store_type: str = Query(default="DocumentDB"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Return metadata for all video assets stored in the database."""
    try:
        agent = get_search_agent(vector_store_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to initialise search agent")
        raise HTTPException(status_code=503, detail=f"Search agent unavailable: {exc}")

    try:
        container = os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"]
        items = agent.perform_search(container, filter={}, limit=limit)
    except Exception as exc:
        logger.exception("Failed to query video assets")
        raise HTTPException(status_code=502, detail=f"Database query failed: {exc}")

    # Strip large vector fields and non-serialisable MongoDB fields from the listing
    vector_keys = {"video_summary_vector", "audio_summary_vector", "_rid", "_self", "_etag", "_attachments", "_ts", "_id"}
    cleaned = [{k: (str(v) if k == "_id" else v) for k, v in item.items() if k not in vector_keys} for item in items]
    return cleaned


@router.get("/videos/{asset_id}", response_model=VideoAssetDetailResponse, summary="Get a single video asset")
def get_video_asset(
    asset_id: str,
    vector_store_type: str = Query(default="DocumentDB"),
):
    """Fetch full metadata for a video asset by its ID, including a fresh SAS URL for playback."""
    try:
        agent = get_search_agent(vector_store_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to initialise search agent")
        raise HTTPException(status_code=503, detail=f"Search agent unavailable: {exc}")

    try:
        container = os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"]
        results = agent.perform_search(container, filter={"id": asset_id}, limit=1)
    except Exception as exc:
        logger.exception("Failed to query video asset %s", asset_id)
        raise HTTPException(status_code=502, detail=f"Database query failed: {exc}")

    if not results:
        raise HTTPException(status_code=404, detail="Video asset not found.")

    asset = results[0]
    vector_keys = {"video_summary_vector", "audio_summary_vector", "_rid", "_self", "_etag", "_attachments", "_ts", "_id"}
    cleaned = {k: v for k, v in asset.items() if k not in vector_keys}

    video_url = None
    blob_key = asset.get("blob_video_key")
    if blob_key:
        try:
            storage = get_storage_helper()
            video_url = storage.generate_blob_sas_token(blob_key)
        except Exception as exc:
            logger.warning("Could not generate SAS URL for %s: %s", blob_key, exc)

    return VideoAssetDetailResponse(asset=cleaned, video_url=video_url)


@router.get("/videos/{asset_id}/frames", summary="List frames for a video asset")
def list_video_frames(
    asset_id: str,
    vector_store_type: str = Query(default="DocumentDB"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return frame summaries for a given video asset, including SAS URLs for each frame image."""
    try:
        agent = get_search_agent(vector_store_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to initialise search agent")
        raise HTTPException(status_code=503, detail=f"Search agent unavailable: {exc}")

    try:
        frames_container = os.environ["AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"]
        assets_container = os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"]
        assets = agent.perform_search(assets_container, filter={"id": asset_id}, limit=1)
    except Exception as exc:
        logger.exception("Failed to query asset %s", asset_id)
        raise HTTPException(status_code=502, detail=f"Database query failed: {exc}")

    if not assets:
        raise HTTPException(status_code=404, detail="Video asset not found.")

    asset_name = assets[0].get("asset_name", "")
    try:
        frame_items = agent.perform_search(frames_container, filter={"asset_name": asset_name}, limit=limit)
    except Exception as exc:
        logger.exception("Failed to query frames for %s", asset_name)
        raise HTTPException(status_code=502, detail=f"Frame query failed: {exc}")

    vector_keys = {"summary_vector", "_rid", "_self", "_etag", "_attachments", "_ts", "_id"}
    result = []
    storage = None
    for frame in frame_items:
        cleaned = {k: v for k, v in frame.items() if k not in vector_keys}
        blob_key = frame.get("blob_frame_key")
        # For legacy data without blob_frame_key, derive it from the raw URL
        if not blob_key:
            raw_url = frame.get("url", "")
            if "/raw_files/" in raw_url:
                blob_key = "raw_files/" + raw_url.split("/raw_files/", 1)[1].split("?")[0]
                cleaned["blob_frame_key"] = blob_key
        if blob_key:
            try:
                if storage is None:
                    storage = get_storage_helper()
                cleaned["frame_url"] = storage.generate_blob_sas_token(blob_key)
            except Exception as exc:
                logger.warning("Could not generate SAS URL for frame %s: %s", blob_key, exc)
        result.append(cleaned)

    return result


@router.get("/frames/{blob_key:path}/url", response_model=FrameUrlResponse, summary="Get a SAS URL for a frame")
def get_frame_url(blob_key: str, frame_id: int = Query(default=0)):
    """Generate a time-limited SAS URL for a specific frame blob."""
    try:
        storage = get_storage_helper()
        url = storage.generate_blob_sas_token(blob_key)
    except Exception as exc:
        logger.exception("Failed to generate SAS URL for %s", blob_key)
        raise HTTPException(status_code=502, detail=f"Storage unavailable: {exc}")
    return FrameUrlResponse(frame_id=frame_id, url=url)


@router.get("/blobs", response_model=BlobListResponse, summary="List all blobs in storage")
def list_blobs():
    """List all blobs in the configured storage container."""
    try:
        storage = get_storage_helper()
        blobs = []
        for blob in storage.list_blobs():
            blobs.append(
                BlobItem(
                    name=blob.name,
                    size=blob.size,
                    content_type=blob.content_settings.content_type if blob.content_settings else None,
                    last_modified=blob.last_modified.isoformat() if blob.last_modified else None,
                )
            )
        return BlobListResponse(container=storage.container_client.container_name, blobs=blobs)
    except Exception as exc:
        logger.exception("Failed to list blobs")
        raise HTTPException(status_code=502, detail=f"Storage unavailable: {exc}")
