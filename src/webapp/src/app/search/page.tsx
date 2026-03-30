"use client";

import { useState, useRef, useEffect } from "react";
import { useSettings } from "@/lib/settings-context";
import { vectorSearch } from "@/lib/api";
import type { SearchResponse } from "@/lib/types";
import ReactMarkdown from "react-markdown";

export default function SearchPage() {
  const { vectorStoreType } = useSettings();
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(5);
  const [searching, setSearching] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"video" | "frames">("video");
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    setActiveTab("video");
    try {
      const res = await vectorSearch(query, vectorStoreType, limit);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  };

  // Seek to playback offset when video is ready
  useEffect(() => {
    const video = videoRef.current;
    if (!video || result?.playback_offset == null) return;
    const seekToOffset = () => {
      video.currentTime = result.playback_offset!;
    };
    video.addEventListener("loadedmetadata", seekToOffset);
    return () => video.removeEventListener("loadedmetadata", seekToOffset);
  }, [result?.video_url, result?.playback_offset]);

  return (
    <>
      <div className="page-header">
        <h2 className="mb-1">Semantic Search</h2>
        <p className="text-muted mb-0">
          Search across all video frame summaries using natural language &middot;{" "}
          <span className="fw-semibold">{vectorStoreType}</span>
        </p>
      </div>

      {/* Search form */}
      <div className="card mb-4">
        <div className="card-body">
          <form onSubmit={handleSearch}>
            <div className="row g-2 align-items-end">
              <div className="col">
                <label className="form-label small">Search query</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Describe what you're looking for..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <div className="col-auto">
                <label className="form-label small">Results</label>
                <input
                  type="number"
                  className="form-control"
                  style={{ width: 70 }}
                  min={1}
                  max={20}
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                />
              </div>
              <div className="col-auto">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={searching || !query.trim()}
                >
                  {searching ? (
                    <span className="spinner-border spinner-border-sm me-1"></span>
                  ) : (
                    <i className="bi bi-search me-1"></i>
                  )}
                  Search
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* Results */}
      {result && result.results.length > 0 && (
        <>
          <p className="text-muted small mb-3">
            {result.results.length} result{result.results.length !== 1 ? "s" : ""} for &ldquo;{result.query}&rdquo;
          </p>

          {/* Tabs */}
          <ul className="nav nav-tabs mb-3">
            <li className="nav-item">
              <button
                className={`nav-link ${activeTab === "video" ? "active" : ""}`}
                onClick={() => setActiveTab("video")}
              >
                <i className="bi bi-play-circle me-1"></i> Video Playback
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link ${activeTab === "frames" ? "active" : ""}`}
                onClick={() => setActiveTab("frames")}
              >
                <i className="bi bi-grid-3x2-gap me-1"></i> Matching Frames
                <span className="badge bg-secondary ms-1">{result.results.length}</span>
              </button>
            </li>
          </ul>

          {/* Tab 1: Video Playback */}
          {activeTab === "video" && (
            <div className="row">
              <div className="col-lg-8">
                {result.video_url ? (
                  <div className="card">
                    <div className="card-body p-2">
                      <video
                        ref={videoRef}
                        className="video-player w-100"
                        controls
                        src={result.video_url}
                      />
                    </div>
                    {result.playback_offset != null && (
                      <div className="card-footer bg-white small text-muted">
                        <i className="bi bi-skip-forward me-1"></i>
                        Playing from {formatTimestamp(result.playback_offset)} &mdash; closest match at Frame {result.results[0].frame_id}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="card">
                    <div className="card-body text-center py-5 text-muted">
                      <i className="bi bi-camera-video-off fs-1"></i>
                      <p className="mt-2 mb-0">Video not available for this asset</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="col-lg-4">
                {/* Top match info */}
                <div className="card mb-3">
                  <div className="card-header bg-white">
                    <h6 className="mb-0">
                      <i className="bi bi-bullseye me-1"></i> Top Match
                    </h6>
                  </div>
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <span className="fw-semibold small">{result.results[0].asset_name}</span>
                      {result.results[0].similarity_score != null && (
                        <span
                          className={`badge ${
                            result.results[0].similarity_score >= 0.8
                              ? "bg-success"
                              : result.results[0].similarity_score >= 0.6
                              ? "bg-warning text-dark"
                              : "bg-secondary"
                          }`}
                        >
                          {(result.results[0].similarity_score * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                    {result.results[0].frame_id != null && (
                      <p className="small text-muted mb-2">
                        <i className="bi bi-film me-1"></i> Frame {result.results[0].frame_id}
                        {result.playback_offset != null && (
                          <> &middot; {formatTimestamp(result.playback_offset)}</>
                        )}
                      </p>
                    )}
                    <div className="small"><ReactMarkdown>{result.results[0].summary}</ReactMarkdown></div>
                  </div>
                </div>

                {/* Asset info */}
                {result.asset_info && (() => {
                  const info = result.asset_info as Record<string, string | number | null>;
                  return (
                    <div className="card">
                      <div className="card-header bg-white">
                        <h6 className="mb-0">
                          <i className="bi bi-info-circle me-1"></i> Asset Info
                        </h6>
                      </div>
                      <div className="card-body">
                        <dl className="row mb-0 small">
                          {info.frame_count != null && (
                            <>
                              <dt className="col-sm-5 text-muted">Frames</dt>
                              <dd className="col-sm-7">{String(info.frame_count)}</dd>
                            </>
                          )}
                          {info.duration != null && (
                            <>
                              <dt className="col-sm-5 text-muted">Duration</dt>
                              <dd className="col-sm-7">{formatTimestamp(Number(info.duration))}</dd>
                            </>
                          )}
                          {info.frame_offset != null && (
                            <>
                              <dt className="col-sm-5 text-muted">Frame interval</dt>
                              <dd className="col-sm-7">{String(info.frame_offset)}s</dd>
                            </>
                          )}
                        </dl>
                        {info.video_summary && (
                          <div className="mt-2 pt-2 border-top small">
                            <ReactMarkdown>{String(info.video_summary)}</ReactMarkdown>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          )}

          {/* Tab 2: Matching Frames */}
          {activeTab === "frames" && (
            <div className="d-flex flex-column gap-3">
              {result.results.map((r, i) => (
                <div key={i} className="card search-result-card">
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-start mb-1">
                      <h6 className="mb-0">
                        <i className="bi bi-film me-1 text-muted"></i>
                        {r.asset_name}
                        {r.frame_id != null && (
                          <span className="text-muted ms-2 small">Frame {r.frame_id}</span>
                        )}
                      </h6>
                      {r.similarity_score != null && (
                        <span
                          className={`badge ${
                            r.similarity_score >= 0.8
                              ? "bg-success"
                              : r.similarity_score >= 0.6
                              ? "bg-warning text-dark"
                              : "bg-secondary"
                          }`}
                        >
                          {(r.similarity_score * 100).toFixed(1)}% match
                        </span>
                      )}
                    </div>
                    <div className="mb-0 small text-muted"><ReactMarkdown>{r.summary}</ReactMarkdown></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* No results */}
      {result && result.results.length === 0 && (
        <div className="text-center py-5 text-muted">
          <i className="bi bi-search fs-1"></i>
          <p className="mt-2">No matching results for &ldquo;{result.query}&rdquo;</p>
        </div>
      )}
    </>
  );
}

function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
