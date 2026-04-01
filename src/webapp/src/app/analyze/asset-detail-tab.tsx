"use client";

import { useEffect, useState } from "react";
import { useSettings } from "@/lib/settings-context";
import { getVideoAsset, listVideoFrames } from "@/lib/api";
import type { VideoAssetDetail, FrameSummary } from "@/lib/types";
import { frameImageUrl } from "@/lib/types";
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
    <>
      {/* Row 1: Asset details + Video player */}
      <div className="row mb-4">
        {/* Asset details card */}
        <div className="col-lg-5 mb-3 mb-lg-0">
          <div className="card h-100">
            <div className="card-header bg-white">
              <h5 className="mb-0">
                <i className="bi bi-camera-video me-2"></i>
                {String(asset.asset_name ?? "Untitled")}
              </h5>
            </div>
            <div className="card-body">
              <dl className="row mb-3">
                {asset.id != null && (
                  <>
                    <dt className="col-sm-4 text-muted">ID</dt>
                    <dd className="col-sm-8 text-break"><code className="small">{String(asset.id)}</code></dd>
                  </>
                )}
                <dt className="col-sm-4 text-muted">Frames</dt>
                <dd className="col-sm-8">{String(asset.frame_count ?? 0)}</dd>
                <dt className="col-sm-4 text-muted">Duration</dt>
                <dd className="col-sm-8">{String(asset.duration ?? 0)}s</dd>
                {asset.frame_offset != null && (
                  <>
                    <dt className="col-sm-4 text-muted">Frame interval</dt>
                    <dd className="col-sm-8">{String(asset.frame_offset)}s</dd>
                  </>
                )}
                {asset.blob_video_key != null && (
                  <>
                    <dt className="col-sm-4 text-muted">Video path</dt>
                    <dd className="col-sm-8 text-break"><code className="small">{String(asset.blob_video_key)}</code></dd>
                  </>
                )}
                {asset.blob_audio_key != null && (
                  <>
                    <dt className="col-sm-4 text-muted">Audio path</dt>
                    <dd className="col-sm-8 text-break"><code className="small">{String(asset.blob_audio_key)}</code></dd>
                  </>
                )}
                <dt className="col-sm-4 text-muted">Has audio</dt>
                <dd className="col-sm-8">
                  {asset.blob_audio_key ? (
                    <span className="badge bg-success"><i className="bi bi-volume-up me-1"></i>Yes</span>
                  ) : (
                    <span className="badge bg-secondary"><i className="bi bi-volume-mute me-1"></i>No</span>
                  )}
                </dd>
                {asset.created_at != null && (
                  <>
                    <dt className="col-sm-4 text-muted">Created</dt>
                    <dd className="col-sm-8">{String(asset.created_at)}</dd>
                  </>
                )}
              </dl>

              {asset.video_summary && (
                <div className="mb-3">
                  <h6 className="mb-1">Video Summary</h6>
                  <div className="text-muted small markdown-content">
                    <ReactMarkdown>{String(asset.video_summary)}</ReactMarkdown>
                  </div>
                </div>
              )}

              {asset.audio_summary && (
                <div className="mb-3">
                  <h6 className="mb-1">Audio Summary</h6>
                  <div className="text-muted small markdown-content">
                    <ReactMarkdown>{String(asset.audio_summary)}</ReactMarkdown>
                  </div>
                </div>
              )}

              {asset.audio_transcription && (
                <div>
                  <h6 className="mb-1">Transcription</h6>
                  <div
                    className="bg-light p-2 rounded small"
                    style={{ maxHeight: 160, overflow: "auto" }}
                  >
                    {String(asset.audio_transcription)}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Video player */}
        <div className="col-lg-7">
          <div className="card h-100">
            <div className="card-body p-2 d-flex align-items-center justify-content-center">
              {detail.video_url ? (
                <video
                  className="video-player w-100 rounded"
                  controls
                  src={detail.video_url}
                />
              ) : (
                <div className="text-center py-5 text-muted">
                  <i className="bi bi-film fs-1"></i>
                  <p className="mt-2 mb-0">Video preview unavailable</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Frames heading */}
      <h5 className="mb-3">
        <i className="bi bi-grid-3x2-gap me-2"></i>
        Frames <span className="badge bg-secondary">{frames.length}</span>
      </h5>

      {frames.length === 0 ? (
        <p className="text-muted small">
          <i className="bi bi-info-circle me-1"></i>
          No frames available.
        </p>
      ) : (
        <div className="d-flex flex-column gap-3">
          {frames.map((f) => {
            const imgUrl = frameImageUrl(f);
            return (
              <div key={f.id} className="card">
                <div className="card-body">
                  <div className="row g-3">
                    {/* Frame thumbnail + label */}
                    <div className="col-md-3">
                      {imgUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={imgUrl}
                          alt={`Frame ${f.frame_id}`}
                          className="w-100 rounded"
                          style={{ objectFit: "cover", maxHeight: 200, background: "#f8f9fa" }}
                        />
                      ) : (
                        <div
                          className="d-flex align-items-center justify-content-center bg-light rounded"
                          style={{ height: 160 }}
                        >
                          <i className="bi bi-image text-muted fs-2"></i>
                        </div>
                      )}
                      <div className="mt-2 text-center">
                        <span className="fw-semibold small">Frame {f.frame_id}</span>
                        {f.blob_frame_key && (
                          <div className="text-muted small text-truncate" title={f.blob_frame_key}>
                            <i className="bi bi-file-image me-1"></i>
                            {f.blob_frame_key.split("/").pop()}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Frame summary */}
                    <div className="col-md-9">
                      <div className="text-muted small markdown-content">
                        {f.summary ? (
                          <ReactMarkdown>{f.summary}</ReactMarkdown>
                        ) : (
                          <p className="mb-0">No description available.</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
