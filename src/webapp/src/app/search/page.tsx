"use client";

import { useState } from "react";
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

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const res = await vectorSearch(query, vectorStoreType, limit);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  };

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
      {result && (
        <div className="row">
          {/* Left: result list */}
          <div className={result.video_url || result.asset_info ? "col-lg-7" : "col-12"}>
            {result.results.length === 0 ? (
              <div className="text-center py-5 text-muted">
                <i className="bi bi-search fs-1"></i>
                <p className="mt-2">No matching results for &ldquo;{result.query}&rdquo;</p>
              </div>
            ) : (
              <div className="d-flex flex-column gap-3">
                <p className="text-muted small mb-0">
                  {result.results.length} result{result.results.length !== 1 ? "s" : ""} for &ldquo;{result.query}&rdquo;
                </p>
                {result.results.map((r, i) => (
                  <div key={i} className="card search-result-card">
                    <div className="card-body">
                      <div className="d-flex justify-content-between align-items-start mb-1">
                        <h6 className="mb-0">
                          <i className="bi bi-film me-1 text-muted"></i>
                          {r.asset_name}
                          {r.frame_id !== null && (
                            <span className="text-muted ms-2 small">Frame {r.frame_id}</span>
                          )}
                        </h6>
                        {r.similarity_score !== null && (
                          <span
                            className={`badge similarity-badge ${
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
          </div>

          {/* Right: top video context */}
          {(result.video_url || result.asset_info) && (
            <div className="col-lg-5">
              <div className="card">
                <div className="card-header bg-white">
                  <h6 className="mb-0">
                    <i className="bi bi-play-circle me-1"></i> Top Match Context
                  </h6>
                </div>
                <div className="card-body">
                  {result.video_url && (
                    <video className="video-player w-100 mb-3" controls src={result.video_url} />
                  )}
                  {result.asset_info && (() => {
                    const info = result.asset_info as Record<string, string | number | null>;
                    return (
                      <dl className="row mb-0 small">
                        {info.asset_name && (
                          <>
                            <dt className="col-sm-4 text-muted">Asset</dt>
                            <dd className="col-sm-8">{String(info.asset_name)}</dd>
                          </>
                        )}
                        {info.frame_count && (
                          <>
                            <dt className="col-sm-4 text-muted">Frames</dt>
                            <dd className="col-sm-8">{String(info.frame_count)}</dd>
                          </>
                        )}
                        {info.video_summary && (
                          <>
                            <dt className="col-sm-4 text-muted">Summary</dt>
                            <dd className="col-sm-8"><ReactMarkdown>{String(info.video_summary)}</ReactMarkdown></dd>
                          </>
                        )}
                      </dl>
                    );
                  })()}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
