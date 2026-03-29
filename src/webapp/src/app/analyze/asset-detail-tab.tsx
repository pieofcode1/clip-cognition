"use client";

import { useEffect, useState } from "react";
import { useSettings } from "@/lib/settings-context";
import { getVideoAsset, listVideoFrames } from "@/lib/api";
import type { VideoAssetDetail, FrameSummary } from "@/lib/types";
import { FrameGallery } from "@/components/frame-gallery";
import ReactMarkdown from "react-markdown";

interface Props {
  assetId: string;
}

export function AssetDetailTab({ assetId }: Props) {
  const { vectorStoreType } = useSettings();
  const [detail, setDetail] = useState<VideoAssetDetail | null>(null);
  const [frames, setFrames] = useState<FrameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getVideoAsset(assetId, vectorStoreType),
      listVideoFrames(assetId, vectorStoreType),
    ])
      .then(([d, f]) => {
        setDetail(d);
        setFrames(f);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [assetId, vectorStoreType]);

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status"></div>
      </div>
    );
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  if (!detail) {
    return <div className="alert alert-warning">Asset not found.</div>;
  }

  const asset = detail.asset as Record<string, string | number | null>;

  return (
    <div className="row">
      {/* Video player + metadata */}
      <div className="col-lg-6 mb-4">
        {detail.video_url ? (
          <video
            className="video-player w-100 mb-3"
            controls
            src={detail.video_url}
          />
        ) : (
          <div className="bg-dark text-white text-center py-5 rounded mb-3">
            <i className="bi bi-film fs-1"></i>
            <p className="mt-2">Video preview unavailable</p>
          </div>
        )}

        <h4>{String(asset.asset_name ?? "Untitled")}</h4>

        <div className="row g-2 mb-3">
          <div className="col-auto">
            <span className="badge bg-primary">
              <i className="bi bi-grid-3x3 me-1"></i>
              {String(asset.frame_count ?? 0)} frames
            </span>
          </div>
          <div className="col-auto">
            <span className="badge bg-secondary">
              <i className="bi bi-clock me-1"></i>
              {String(asset.duration ?? 0)}s
            </span>
          </div>
        </div>

        {asset.video_summary && (
          <div className="mb-3">
            <h6>Video Summary</h6>
            <div className="text-muted markdown-content">
              <ReactMarkdown>{String(asset.video_summary)}</ReactMarkdown>
            </div>
          </div>
        )}

        {asset.audio_summary && (
          <div className="mb-3">
            <h6>Audio Summary</h6>
            <div className="text-muted markdown-content">
              <ReactMarkdown>{String(asset.audio_summary)}</ReactMarkdown>
            </div>
          </div>
        )}

        {asset.audio_transcription && (
          <div className="mb-3">
            <h6>Transcription</h6>
            <div className="bg-light p-3 rounded small" style={{ maxHeight: 200, overflow: "auto" }}>
              {String(asset.audio_transcription)}
            </div>
          </div>
        )}
      </div>

      {/* Frames */}
      <div className="col-lg-6">
        <h5 className="mb-3">
          Frames <span className="badge bg-secondary">{frames.length}</span>
        </h5>
        <FrameGallery
          frames={frames}
          blobFolderPath={asset.asset_name ? `raw_files/frames/${String(asset.asset_name)}` : undefined}
        />
      </div>
    </div>
  );
}
