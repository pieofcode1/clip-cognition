"""Video processing agent: frame extraction, audio transcription, summarization, and vector storage."""

import base64
import logging
import os
import uuid

import cv2
import numpy as np
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from moviepy import VideoFileClip
from openai import AzureOpenAI

from core.az_documentdb_util import AzDocumentDBClient
from core.cosmos_util import CosmosUtil
from core.embedding_agent import AzureOpenAIEmbeddingsAgent
from core.prompts import (
    AUDIO_SUMMARY_SYSTEM_PROMPT,
    VIDEO_FRAME_ANALYSIS_SYSTEM_PROMPT,
    VIDEO_FRAME_ANALYSIS_USER_PROMPT,
)
from core.schema import MediaAssetInfo, VideoFrameSummary, VectorStoreType
from core.storage_helper import StorageHelper

np.set_printoptions(precision=16)
logger = logging.getLogger(__name__)


class VideoProcessingAgent:
    """Processes uploaded videos: extracts frames, transcribes audio, generates summaries, and stores results."""

    def __init__(self, video_file, vector_store_type: str, fps: int = 5, system_prompt: str | None = None, frame_analysis_prompt: str | None = None) -> None:
        self.vector_store_type = vector_store_type
        self.id = str(uuid.uuid4())
        self.video_data = video_file.getvalue()
        self.is_complete = False
        self.fps = fps
        self.system_prompt = system_prompt
        self.frame_analysis_prompt = frame_analysis_prompt
        self.video_file_name = video_file.name

        # Blob storage keys
        self.blob_key_video = f"raw_files/video/{self.video_file_name}"
        self.blob_key_video_frame = f"raw_files/frames/{self.video_file_name}"
        self.blob_key_audio = f"raw_files/audio/{os.path.splitext(self.video_file_name)[0]}.mp3"

        # State
        self.blob_url_video: str | None = None
        self.blob_url_audio: str | None = None
        self.blob_url_audio_with_sas: str | None = None
        self.blob_url_frames: list[str] = []
        self.video_frames: list[str] = []
        self.audio_transcription: str | None = None
        self.audio_summary: str | None = None
        self.video_summary: str | None = None
        self.temp_folder = "./temp/"

        # Initialize backends
        self._init_vector_store(vector_store_type)
        self._init_storage_helper()
        self._init_openai_clients()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------

    def _init_vector_store(self, vector_store_type: str) -> None:
        if vector_store_type == VectorStoreType.CosmosNoSQL.value or vector_store_type == VectorStoreType.CosmosNoSQL:
            logger.info("Initializing CosmosDB as vector store")
            self.cosmos_util = CosmosUtil(
                database=os.environ["AZURE_COSMOS_DB_DATABASE_NAME"],
                containers=[
                    os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"],
                    os.environ["AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"],
                ],
                embedding_agent=AzureOpenAIEmbeddingsAgent(),
            )
        elif vector_store_type == VectorStoreType.AzureDocumentDB.value or vector_store_type == VectorStoreType.AzureDocumentDB:
            logger.info("Initializing DocumentDB as vector store")
            conn_str = os.environ.get("MONGODB_CONNECTION_STRING", "")
            if not conn_str or "<user>" in conn_str or "<password>" in conn_str:
                raise ValueError(
                    "MONGODB_CONNECTION_STRING is not configured or still contains placeholders. "
                    "Run 'azd up' to provision DocumentDB and populate the connection string."
                )
            self.documentdb_client = AzDocumentDBClient(
                conn_str,
                os.environ.get("MONGODB_DB_NAME", "ClipCognition"),
                embedding_agent=AzureOpenAIEmbeddingsAgent(),
            )
            self.documentdb_client.ping()
        else:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")

    def _init_storage_helper(self) -> None:
        self.storage_helper = StorageHelper(os.environ["AZURE_STORAGE_CONTAINER_NAME"])

    def _init_openai_clients(self) -> None:
        api_version = os.environ["AZURE_OPENAI_API_VERSION"]
        client_id = os.environ["USER_ASSIGNED_ID_CLIENT_ID"]
        credential = DefaultAzureCredential(managed_identity_client_id=client_id)
        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

        self.gpt4o_deployment_name = os.environ["AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME"]
        self.whisper_deployment_name = os.environ["AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME"]
        self.embedding_deployment_name = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"]

        self.aoai_client_gpt4o = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_COMPLETION_DEPLOYMENT_ENDPOINT"],
            azure_ad_token_provider=token_provider,
            api_version=api_version,
        )
        self.aoai_client_whisper = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_WHISPER_DEPLOYMENT_ENDPOINT"],
            azure_ad_token_provider=token_provider,
            api_version=api_version,
        )
        self.aoai_client_embedding = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ENDPOINT"],
            azure_ad_token_provider=token_provider,
            api_version=api_version,
        )

    # ------------------------------------------------------------------
    # Blob helpers
    # ------------------------------------------------------------------

    def upload_blob_from_stream(self, data, key: str, mime_type: str | None = None) -> str:
        return self.storage_helper.upload_blob_from_stream(data, key, mime_type)

    def upload_blob_from_file(self, file_path: str, key: str, mime_type: str | None = None) -> str:
        return self.storage_helper.upload_blob_with_key(file_path, key, mime_type)

    def get_video_frame_sas_url(self, frame_id: int) -> str:
        return self.storage_helper.generate_blob_sas_token(f"{self.blob_key_video_frame}/{frame_id}.png")

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _insert_video_asset(self, video_asset_dict: dict) -> None:
        container_name = os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"]
        if self.vector_store_type in (VectorStoreType.CosmosNoSQL.value, VectorStoreType.CosmosNoSQL):
            self.cosmos_util.upsert_items(container_name, video_asset_dict)
        elif self.vector_store_type in (VectorStoreType.AzureDocumentDB.value, VectorStoreType.AzureDocumentDB):
            self.documentdb_client.insert(container_name, video_asset_dict)

    def _insert_video_frame_asset(self, video_asset_frame_dict: dict) -> None:
        container_name = os.environ["AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"]
        if self.vector_store_type in (VectorStoreType.CosmosNoSQL.value, VectorStoreType.CosmosNoSQL):
            self.cosmos_util.upsert_items(container_name, video_asset_frame_dict)
        elif self.vector_store_type in (VectorStoreType.AzureDocumentDB.value, VectorStoreType.AzureDocumentDB):
            self.documentdb_client.insert(container_name, video_asset_frame_dict)

    # ------------------------------------------------------------------
    # Embedding helper
    # ------------------------------------------------------------------

    def vectorize(self, text: str) -> list[float] | None:
        response = self.aoai_client_embedding.embeddings.create(input=text, model=self.embedding_deployment_name, dimensions=1536)
        return response.data[0].embedding if response and response.data else None

    # ------------------------------------------------------------------
    # Core processing pipeline
    # ------------------------------------------------------------------

    def process_video(self) -> None:
        """Run the full video processing pipeline: upload, extract frames, transcribe audio, store results."""
        # Upload video to blob storage
        self.blob_url_video = self.upload_blob_from_stream(self.video_data, self.blob_key_video, "video/mp4")
        video_link = self.storage_helper.generate_blob_sas_token(self.blob_key_video)
        logger.info("Uploaded video to blob storage: %s", self.blob_url_video)

        # Extract frames
        self._extract_frames(video_link)
        logger.info("Extracted %d frames", len(self.video_frames))

        # Extract and process audio
        self._process_audio(video_link)

        # Upload frames to blob storage
        self._upload_video_frames()

        # Store video asset metadata
        video_asset = MediaAssetInfo(
            id=self.id,
            asset_name=self.video_file_name,
            blob_video_key=self.blob_key_video,
            blob_audio_key=self.blob_key_audio,
            blob_video_url=self.blob_url_video,
            blob_audio_url=self.blob_url_audio,
            frame_offset=self.fps,
            frame_count=len(self.video_frames),
            duration=self.fps * len(self.video_frames),
            total_frames=len(self.video_frames),
            audio_transcription=self.audio_transcription,
            audio_summary=self.audio_summary,
            audio_summary_vector=self.vectorize(self.audio_summary) if self.audio_summary else [],
            video_summary=self.video_summary,
            video_summary_vector=self.vectorize(self.video_summary) if self.video_summary else [],
        )
        self._insert_video_asset(video_asset.model_dump())
        logger.info("Video processing completed for %s", self.video_file_name)
        self.is_complete = True

    def _extract_frames(self, video_link: str) -> None:
        video = cv2.VideoCapture(video_link)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)
        frames_to_skip = int(fps * self.fps)
        curr_frame = 0

        while curr_frame < total_frames - 1:
            video.set(cv2.CAP_PROP_POS_FRAMES, curr_frame)
            success, frame = video.read()
            if not success:
                break
            _, buffer = cv2.imencode(".jpg", frame)
            self.video_frames.append(base64.b64encode(buffer).decode("utf-8"))
            curr_frame += frames_to_skip
        video.release()

    def _process_audio(self, video_link: str) -> None:
        clip = VideoFileClip(video_link)
        if clip.audio is None:
            logger.info("No audio track found in the video.")
            clip.close()
            return

        audio_path = os.path.join(self.temp_folder, self.blob_key_audio)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        clip.audio.write_audiofile(audio_path, bitrate="32k")
        clip.audio.close()
        clip.close()

        absolute_path = os.path.abspath(audio_path)
        self.blob_url_audio = self.upload_blob_from_file(absolute_path, self.blob_key_audio, "audio/mp3")
        self.blob_url_audio_with_sas = self.storage_helper.generate_blob_sas_token(self.blob_key_audio)
        logger.info("Uploaded audio to %s", self.blob_url_audio)

        self._summarize_audio(absolute_path)

    def _upload_video_frames(self) -> None:
        for idx, frame in enumerate(self.video_frames):
            frame_name = f"{self.blob_key_video_frame}/{idx * self.fps}.png"
            url = self.upload_blob_from_stream(base64.b64decode(frame), frame_name, "image/png")
            self.blob_url_frames.append(url)

    def _summarize_audio(self, audio_path: str) -> None:
        logger.info("Transcribing audio...")
        with open(audio_path, "rb") as audio_file:
            transcription = self.aoai_client_whisper.audio.transcriptions.create(
                model=self.whisper_deployment_name,
                file=audio_file,
            )
        self.audio_transcription = transcription.text
        logger.info("Audio transcription complete (%d chars).", len(self.audio_transcription))

        response = self.aoai_client_gpt4o.chat.completions.create(
            model=self.gpt4o_deployment_name,
            messages=[
                {"role": "system", "content": AUDIO_SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": [{"type": "text", "text": f"The audio transcription is: {transcription.text}"}]},
            ],
            temperature=0,
        )
        self.audio_summary = response.choices[0].message.content
        logger.info("Audio summary generated.")

    def summarize_video(self):
        """Yield frame-by-frame summaries using GPT-4o vision. Stores each frame summary in the vector store."""
        logger.info("Summarizing %d frames...", len(self.video_frames))
        previous_context = ""

        for index, frame in enumerate(self.video_frames):
            frame_url = self.blob_url_frames[index]
            frame_key = f"{self.blob_key_video_frame}/{index * self.fps}.png"
            frame_summary = VideoFrameSummary(
                id=str(uuid.uuid4()),
                frame_id=index * self.fps,
                asset_name=self.video_file_name,
                url=frame_url,
                blob_frame_key=frame_key,
            )

            system_prompt = self.system_prompt or (VIDEO_FRAME_ANALYSIS_SYSTEM_PROMPT % previous_context)
            user_prompt = self.frame_analysis_prompt or VIDEO_FRAME_ANALYSIS_USER_PROMPT

            response = self.aoai_client_gpt4o.chat.completions.create(
                model=self.gpt4o_deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpg;base64,{frame}", "detail": "low"}},
                        ],
                    },
                ],
                temperature=0,
            )

            previous_context = response.choices[0].message.content
            frame_summary.summary = previous_context
            frame_summary.token_usage = response.usage
            frame_summary.deployment_name = response.model
            frame_summary.summary_vector = self.vectorize(previous_context)

            self._insert_video_frame_asset(frame_summary.model_dump())
            logger.debug("Frame %d summarized.", frame_summary.frame_id)
            yield frame_summary
