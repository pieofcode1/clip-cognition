"""Video upload, analysis, and detail endpoints."""

import asyncio
import logging
import os
import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from api.dependencies import get_storage_helper
from api.models import (
    FrameSummaryResponse,
    VideoAssetResponse,
    VideoProcessingResult,
    VideoUploadResponse,
)
from core.schema import VectorStoreType
from core.video_processor import VideoProcessingAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/videos", tags=["videos"])


class _UploadedVideoFile:
    """Adapter so VideoProcessingAgent can consume FastAPI UploadFile as a file-like object."""

    def __init__(self, data: bytes, filename: str) -> None:
        self._data = data
        self.name = filename

    def getvalue(self) -> bytes:
        return self._data


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """Stream a video file to Azure Blob Storage and return a preview URL.

    This is step 1 of the two-step workflow: upload → preview → analyze.
    """
    if file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a video.")

    filename = file.filename or "video.mp4"
    blob_key = f"raw_files/video/{filename}"

    # Stream directly to blob storage without loading entire file into memory
    def _upload():
        storage = get_storage_helper()
        storage.upload_blob_from_stream(file.file, blob_key, file.content_type or "video/mp4")
        video_url = storage.generate_blob_sas_token(blob_key)
        return video_url

    video_url = await asyncio.to_thread(_upload)

    # Get file size from the underlying SpooledTemporaryFile
    try:
        size = file.file.seek(0, 2)
    except Exception:
        size = 0

    return VideoUploadResponse(
        blob_key=blob_key,
        file_name=filename,
        size=size,
        video_url=video_url,
    )


@router.post("/analyze", response_model=VideoProcessingResult)
async def analyze_video(
    file: UploadFile = File(None),
    blob_key: Annotated[str | None, Form()] = None,
    file_name: Annotated[str | None, Form()] = None,
    vector_store_type: Annotated[str, Form()] = VectorStoreType.CosmosNoSQL.value,
    fps: Annotated[int, Form(ge=1, le=30)] = 5,
    system_prompt: Annotated[str | None, Form()] = None,
    frame_analysis_prompt: Annotated[str | None, Form()] = None,
):
    """Run the full processing pipeline on a video.

    Accepts either:
    - ``blob_key`` + ``file_name`` for a video already uploaded to blob storage (two-step flow)
    - ``file`` for a direct upload (legacy one-step flow)
    """
    if blob_key:
        # Two-step flow: video already in blob storage — download bytes for the pipeline
        def _download():
            storage = get_storage_helper()
            blob_client = storage.container_client.get_blob_client(blob_key)
            return blob_client.download_blob().readall()

        data = await asyncio.to_thread(_download)
        filename = file_name or blob_key.rsplit("/", 1)[-1]
    elif file and file.filename:
        if file.content_type and not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be a video.")
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file.")
        filename = file.filename or "video.mp4"
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or blob_key.")

    video_file = _UploadedVideoFile(data, filename)

    try:
        agent = VideoProcessingAgent(
            video_file,
            vector_store_type=vector_store_type,
            fps=fps,
            system_prompt=system_prompt or None,
            frame_analysis_prompt=frame_analysis_prompt or None,
        )

        # Run heavy processing in a thread so we don't block the event loop
        def _run_pipeline():
            agent.process_video()
            storage = get_storage_helper()
            summaries = []
            for summary in agent.summarize_video():
                # Derive the blob key so we can generate a SAS URL
                blob_key_frame = f"{agent.blob_key_video_frame}/{summary.frame_id}.png"
                try:
                    sas_url = storage.generate_blob_sas_token(blob_key_frame)
                except Exception:
                    sas_url = summary.url
                summaries.append(
                    FrameSummaryResponse(
                        id=summary.id,
                        frame_id=summary.frame_id,
                        asset_name=summary.asset_name,
                        url=summary.url,
                        summary=summary.summary,
                        blob_frame_key=blob_key_frame,
                        frame_url=sas_url,
                    )
                )
            return summaries

        frame_summaries: list[FrameSummaryResponse] = await asyncio.to_thread(_run_pipeline)

        asset = VideoAssetResponse(
            id=agent.id,
            asset_name=agent.video_file_name,
            blob_video_url=agent.blob_url_video or "",
            blob_audio_url=agent.blob_url_audio,
            frame_count=len(agent.video_frames),
            duration=agent.fps * len(agent.video_frames),
            audio_transcription=agent.audio_transcription,
            audio_summary=agent.audio_summary,
            video_summary=agent.video_summary,
        )

        return VideoProcessingResult(
            job_id=agent.id,
            file_name=agent.video_file_name,
            status="complete",
            asset=asset,
            frame_summaries=frame_summaries,
        )
    except Exception:
        logger.exception("Video processing failed")
        raise HTTPException(status_code=500, detail="Video processing failed.")
