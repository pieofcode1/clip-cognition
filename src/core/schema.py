"""Pydantic models and enums for the ClipCognition application."""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, field_validator


class VectorStoreType(str, Enum):
    CosmosNoSQL = "CosmosDB NoSQL"
    AzureDocumentDB = "Azure DocumentDB"


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: float | None = None


class MediaAssetInfo(BaseModel):
    id: str
    asset_name: str
    blob_video_key: str
    blob_audio_key: Optional[str] = None
    blob_video_url: str
    blob_audio_url: Optional[str] = None
    frame_offset: int
    frame_count: int
    duration: int
    total_frames: int
    audio_transcription: Optional[str] = None
    audio_summary: Optional[str] = None
    audio_summary_vector: Optional[List[float]] = None
    video_summary: Optional[str] = None
    video_summary_vector: Optional[List[float]] = None
    created_at: str = ""

    def model_post_init(self, __context) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now().isoformat())


class VideoFrameSummary(BaseModel):
    id: str
    frame_id: int
    asset_name: str
    url: str
    blob_frame_key: str = ""
    summary: str = ""
    summary_vector: List = []
    token_usage: TokenUsage | None = None
    deployment_name: str | None = None
    created_at: str = ""

    def model_post_init(self, __context) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now().isoformat())

    @field_validator("summary_vector")
    @classmethod
    def convert_tuple_to_list(cls, v):
        if isinstance(v, tuple):
            return list(v)
        return v


class VectorSearchItem(BaseModel):
    similarity_score: float
    document: dict


class VectorSearchResult(BaseModel):
    items: List[VectorSearchItem]
