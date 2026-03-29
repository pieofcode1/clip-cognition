"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { FrameSummary } from "@/lib/types";
import { frameImageUrl } from "@/lib/types";

interface FrameGalleryProps {
  frames: FrameSummary[];
  /** Optional blob folder path shown as a link in the detail panel. */
  blobFolderPath?: string;
}

/**
 * Reusable frame gallery with a thumbnail grid and an expandable detail panel.
 *
 * Used by both the Upload "done" phase and the Asset Detail tab.
 */
export function FrameGallery({ frames, blobFolderPath }: FrameGalleryProps) {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const selected = selectedIdx !== null ? frames[selectedIdx] : null;

  if (frames.length === 0) {
    return (
      <p className="text-muted small">
        <i className="bi bi-info-circle me-1"></i>
        No frames available.
      </p>
    );
  }

  return (
    <div>
      {/* Detail panel — shown when a frame is selected */}
      {selected && (
        <div className="card mb-3 border-primary">
          <div className="card-header bg-primary bg-opacity-10 d-flex justify-content-between align-items-center">
            <h6 className="mb-0">
              <i className="bi bi-image me-1"></i>
              Frame {selected.frame_id}
              <span className="text-muted ms-2 small fw-normal">{selected.asset_name}</span>
            </h6>
            <button
              className="btn btn-sm btn-outline-secondary"
              onClick={() => setSelectedIdx(null)}
              aria-label="Close detail"
            >
              <i className="bi bi-x-lg"></i>
            </button>
          </div>
          <div className="card-body">
            <div className="row g-3">
              {/* Frame image */}
              <div className="col-md-6">
                {frameImageUrl(selected) ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={frameImageUrl(selected)}
                    alt={`Frame ${selected.frame_id}`}
                    className="w-100 rounded"
                    style={{ objectFit: "contain", maxHeight: 400, background: "#f8f9fa" }}
                  />
                ) : (
                  <div
                    className="d-flex align-items-center justify-content-center bg-light rounded"
                    style={{ height: 250 }}
                  >
                    <i className="bi bi-image text-muted fs-1"></i>
                  </div>
                )}
              </div>

              {/* Description + metadata */}
              <div className="col-md-6">
                <h6 className="mb-2">Description</h6>
                <div className="bg-light rounded p-3 mb-3 markdown-content" style={{ maxHeight: 280, overflow: "auto" }}>
                  {selected.summary ? (
                    <ReactMarkdown>{selected.summary}</ReactMarkdown>
                  ) : (
                    <p className="text-muted small mb-0">No description available.</p>
                  )}
                </div>

                {/* Metadata pills */}
                <div className="d-flex flex-wrap gap-2 mb-2">
                  <span className="badge bg-secondary">
                    <i className="bi bi-hash me-1"></i>Frame {selected.frame_id}
                  </span>
                  {selected.blob_frame_key && (
                    <span className="badge bg-info text-dark" title={selected.blob_frame_key}>
                      <i className="bi bi-cloud me-1"></i>
                      {selected.blob_frame_key.split("/").pop()}
                    </span>
                  )}
                </div>

                {/* Storage folder link */}
                {blobFolderPath && (
                  <div className="small text-muted mt-2">
                    <i className="bi bi-folder2-open me-1"></i>
                    Storage: <code className="user-select-all">{blobFolderPath}</code>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Prev / Next navigation */}
          <div className="card-footer bg-transparent d-flex justify-content-between">
            <button
              className="btn btn-sm btn-outline-primary"
              disabled={selectedIdx === 0}
              onClick={() => setSelectedIdx((selectedIdx ?? 0) - 1)}
            >
              <i className="bi bi-chevron-left me-1"></i>Previous
            </button>
            <span className="small text-muted align-self-center">
              {(selectedIdx ?? 0) + 1} / {frames.length}
            </span>
            <button
              className="btn btn-sm btn-outline-primary"
              disabled={selectedIdx === frames.length - 1}
              onClick={() => setSelectedIdx((selectedIdx ?? 0) + 1)}
            >
              Next<i className="bi bi-chevron-right ms-1"></i>
            </button>
          </div>
        </div>
      )}

      {/* Thumbnail grid */}
      <div className="frame-grid">
        {frames.map((f, idx) => {
          const imgUrl = frameImageUrl(f);
          const isSelected = idx === selectedIdx;
          return (
            <div
              key={f.id}
              className={`card frame-card cursor-pointer ${isSelected ? "border-primary shadow-sm" : ""}`}
              onClick={() => setSelectedIdx(idx === selectedIdx ? null : idx)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") setSelectedIdx(idx === selectedIdx ? null : idx);
              }}
            >
              {imgUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={imgUrl} alt={`Frame ${f.frame_id}`} />
              ) : (
                <div
                  className="d-flex align-items-center justify-content-center bg-light"
                  style={{ height: 160 }}
                >
                  <i className="bi bi-image text-muted fs-3"></i>
                </div>
              )}
              <div className="card-body p-2">
                <div className="d-flex justify-content-between align-items-center">
                  <small className="text-muted fw-medium">Frame {f.frame_id}</small>
                  {isSelected && <i className="bi bi-check-circle-fill text-primary small"></i>}
                </div>
                <p className="small mb-0 mt-1 text-truncate-2">{f.summary}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
