"""Pydantic models for API request/response bodies."""

from pydantic import BaseModel, Field


class VideoUploadResponse(BaseModel):
    blob_key: str
    file_name: str
    size: int
    video_url: str


class VideoAssetResponse(BaseModel):
    id: str
    asset_name: str
    blob_video_url: str
    blob_audio_url: str | None = None
    frame_count: int
    duration: int
    audio_transcription: str | None = None
    audio_summary: str | None = None
    video_summary: str | None = None


class FrameSummaryResponse(BaseModel):
    id: str
    frame_id: int
    asset_name: str
    url: str
    summary: str
    blob_frame_key: str | None = None
    frame_url: str | None = None


class VideoProcessingResult(BaseModel):
    job_id: str
    file_name: str
    status: str
    asset: VideoAssetResponse | None = None
    frame_summaries: list[FrameSummaryResponse] = []


class SearchRequest(BaseModel):
    query: str
    vector_store_type: str = "DocumentDB"
    limit: int = Field(default=3, ge=1, le=20)


class SearchResultItem(BaseModel):
    frame_id: int | None = None
    asset_name: str
    summary: str
    similarity_score: float | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    video_url: str | None = None
    asset_info: dict | None = None


class BlobItem(BaseModel):
    name: str
    size: int | None = None
    content_type: str | None = None
    last_modified: str | None = None


class BlobListResponse(BaseModel):
    container: str
    blobs: list[BlobItem]


class VideoAssetDetailResponse(BaseModel):
    """Full video asset metadata from the database."""
    asset: dict
    video_url: str | None = None


class FrameUrlResponse(BaseModel):
    frame_id: int
    url: str


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    backends: dict[str, bool] = {}
