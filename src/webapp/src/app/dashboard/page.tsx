"use client";

import { useEffect, useState } from "react";
import { useSettings } from "@/lib/settings-context";
import { listVideoAssets } from "@/lib/api";
import type { VideoAsset } from "@/lib/types";
import Link from "next/link";

export default function DashboardPage() {
  const { vectorStoreType, health } = useSettings();
  const [assets, setAssets] = useState<VideoAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listVideoAssets(vectorStoreType)
      .then(setAssets)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [vectorStoreType]);

  const totalFrames = assets.reduce((s, a) => s + (a.frame_count ?? 0), 0);

  return (
    <>
      <div className="page-header d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-1">Dashboard</h2>
          <p className="text-muted mb-0">
            Overview of processed video assets &middot;{" "}
            <span className="fw-semibold">{vectorStoreType}</span>
          </p>
        </div>
        <Link href="/analyze" className="btn btn-primary">
          <i className="bi bi-plus-lg me-1"></i> Analyze New
        </Link>
      </div>

      {/* Stat cards */}
      <div className="row g-3 mb-4">
        <div className="col-sm-6 col-lg-3">
          <div className="card h-100">
            <div className="card-body text-center">
              <div className="rounded-circle bg-primary bg-opacity-10 d-inline-flex align-items-center justify-content-center mb-2" style={{ width: 48, height: 48 }}>
                <i className="bi bi-camera-video-fill fs-5 text-primary"></i>
              </div>
              <div className="text-muted small text-uppercase mb-1">Video Assets</div>
              <div className="fs-2 fw-bold text-primary">{loading ? "..." : assets.length}</div>
            </div>
          </div>
        </div>
        <div className="col-sm-6 col-lg-3">
          <div className="card h-100">
            <div className="card-body text-center">
              <div className="rounded-circle bg-success bg-opacity-10 d-inline-flex align-items-center justify-content-center mb-2" style={{ width: 48, height: 48 }}>
                <i className="bi bi-grid-3x3-gap-fill fs-5 text-success"></i>
              </div>
              <div className="text-muted small text-uppercase mb-1">Total Frames</div>
              <div className="fs-2 fw-bold text-success">{loading ? "..." : totalFrames}</div>
            </div>
          </div>
        </div>
        <div className="col-sm-6 col-lg-3">
          <div className="card h-100">
            <div className="card-body text-center">
              <div className="rounded-circle bg-info bg-opacity-10 d-inline-flex align-items-center justify-content-center mb-2" style={{ width: 48, height: 48 }}>
                <i className="bi bi-database-fill fs-5 text-info"></i>
              </div>
              <div className="text-muted small text-uppercase mb-1">Cosmos NoSQL</div>
              <div className="fs-4 fw-bold">
                {health ? (
                  health.backends.cosmosdb_nosql ? (
                    <span className="badge bg-success"><i className="bi bi-check-lg me-1"></i>Online</span>
                  ) : (
                    <span className="badge bg-danger"><i className="bi bi-x-lg me-1"></i>Offline</span>
                  )
                ) : <span className="badge bg-secondary">...</span>}
              </div>
            </div>
          </div>
        </div>
        <div className="col-sm-6 col-lg-3">
          <div className="card h-100">
            <div className="card-body text-center">
              <div className="rounded-circle bg-warning bg-opacity-10 d-inline-flex align-items-center justify-content-center mb-2" style={{ width: 48, height: 48 }}>
                <i className="bi bi-hdd-stack-fill fs-5 text-warning"></i>
              </div>
              <div className="text-muted small text-uppercase mb-1">DocumentDB</div>
              <div className="fs-4 fw-bold">
                {health ? (
                  health.backends.azure_documentdb ? (
                    <span className="badge bg-success"><i className="bi bi-check-lg me-1"></i>Online</span>
                  ) : (
                    <span className="badge bg-danger"><i className="bi bi-x-lg me-1"></i>Offline</span>
                  )
                ) : <span className="badge bg-secondary">...</span>}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Video assets table */}
      <div className="card">
        <div className="card-body p-0">
          <h5 className="px-3 pt-3 pb-2 mb-0">Video Library</h5>
          {loading && (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" role="status"></div>
              <p className="mt-2 text-muted">Loading assets...</p>
            </div>
          )}
          {error && (
            <div className="alert alert-danger m-3">{error}</div>
          )}
          {!loading && !error && assets.length === 0 && (
            <div className="text-center py-5 text-muted">
              <i className="bi bi-film fs-1"></i>
              <p className="mt-2">No video assets found. Upload and analyze a video to get started.</p>
            </div>
          )}
          {!loading && !error && assets.length > 0 && (
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Name</th>
                    <th>Frames</th>
                    <th>Duration (s)</th>
                    <th>Audio Summary</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {assets.map((asset) => (
                    <tr key={asset.id}>
                      <td className="fw-medium">{asset.asset_name}</td>
                      <td>{asset.frame_count ?? "—"}</td>
                      <td>{asset.duration ?? "—"}</td>
                      <td className="text-truncate" style={{ maxWidth: 300 }}>
                        {asset.audio_summary
                          ? asset.audio_summary.slice(0, 120) + (asset.audio_summary.length > 120 ? "..." : "")
                          : "—"}
                      </td>
                      <td>
                        <Link
                          href={`/assets/${asset.id}`}
                          className="btn btn-outline-primary btn-sm"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
