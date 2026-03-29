"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSettings } from "@/lib/settings-context";
import { uploadVideo, analyzeBlob } from "@/lib/api";
import type { VideoUploadResponse } from "@/lib/types";

type Phase = "select" | "uploading" | "preview" | "analyzing";

export function UploadTab() {
  const { vectorStoreType } = useSettings();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<(() => void) | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [fps, setFps] = useState(5);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [framePrompt, setFramePrompt] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [phase, setPhase] = useState<Phase>("select");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedInfo, setUploadedInfo] = useState<VideoUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  // Elapsed timer while analyzing
  useEffect(() => {
    if (phase !== "analyzing") return;
    setElapsed(0);
    const t = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [phase]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.type.startsWith("video/")) {
      setFile(droppedFile);
    }
  }, []);

  const handleFileSelect = useCallback((f: File | null) => {
    setFile(f);
    setPhase("select");
    setUploadedInfo(null);
    setError(null);
  }, []);

  // Phase 1: Upload to Azure Blob Storage
  const handleUpload = async () => {
    if (!file) return;
    setPhase("uploading");
    setUploadProgress(0);
    setError(null);
    setUploadedInfo(null);

    try {
      const { promise, abort } = uploadVideo(file, (pct) => setUploadProgress(pct));
      abortRef.current = abort;
      const info = await promise;
      abortRef.current = null;
      setUploadedInfo(info);
      setPhase("preview");
    } catch (e: unknown) {
      abortRef.current = null;
      setError(e instanceof Error ? e.message : "Upload failed");
      setPhase("select");
    }
  };

  // Phase 2: Analyze the already-uploaded video
  const handleAnalyze = async () => {
    if (!uploadedInfo) return;
    setPhase("analyzing");
    setError(null);

    try {
      const res = await analyzeBlob(
        uploadedInfo.blob_key,
        uploadedInfo.file_name,
        vectorStoreType,
        fps,
        systemPrompt || undefined,
        framePrompt || undefined
      );
      // Navigate to the asset detail page
      if (res.asset?.id) {
        router.push(`/assets/${res.asset.id}`);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed");
      setPhase("preview"); // let user retry
    }
  };

  const handleReset = () => {
    setFile(null);
    setPhase("select");
    setUploadProgress(0);
    setUploadedInfo(null);
    setError(null);
  };

  return (
    <div className="row">
      <div className="col-lg-8">
        {/* Error banner */}
        {error && (
          <div className="alert alert-danger d-flex align-items-center mb-3">
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            {error}
          </div>
        )}

        {/* ── Phase: Analyzing banner ── */}
        {phase === "analyzing" && (
          <div className="alert alert-info d-flex align-items-center mb-3">
            <span className="spinner-border spinner-border-sm me-2"></span>
            <div>
              <strong>Analyzing video</strong>{" \u2014 "}
              extracting frames, transcribing audio, generating AI summaries.
              This may take several minutes.
              <span className="ms-2 badge bg-info text-dark">
                {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")}
              </span>
            </div>
          </div>
        )}

        {/* ── Phase: Select & Upload zone ── */}
        {(phase === "select" || phase === "uploading") && (
          <>
            <div
              className={`upload-zone mb-3 ${dragging ? "dragging" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                className="d-none"
                onChange={(e) => handleFileSelect(e.target.files?.[0] ?? null)}
              />
              {file ? (
                <div>
                  <i className="bi bi-file-earmark-play fs-1 text-primary"></i>
                  <p className="mt-2 mb-0 fw-medium">{file.name}</p>
                  <p className="text-muted small">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                </div>
              ) : (
                <div>
                  <i className="bi bi-cloud-arrow-up fs-1 text-muted"></i>
                  <p className="mt-2 mb-0">Drag &amp; drop a video here, or click to browse</p>
                  <p className="text-muted small">Supported formats: MP4, MKV, AVI, MOV</p>
                </div>
              )}
            </div>

            {/* Upload progress bar */}
            {phase === "uploading" && (
              <div className="mb-3">
                <div className="d-flex justify-content-between small mb-1">
                  <span>Uploading to Azure Storage...</span>
                  <span className="fw-semibold">{uploadProgress}%</span>
                </div>
                <div className="progress" style={{ height: 8 }}>
                  <div
                    className="progress-bar progress-bar-striped progress-bar-animated"
                    role="progressbar"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Upload button */}
            <div className="d-flex justify-content-end mb-3">
              <button
                className="btn btn-primary"
                disabled={!file || phase === "uploading"}
                onClick={handleUpload}
              >
                {phase === "uploading" ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Uploading...
                  </>
                ) : (
                  <>
                    <i className="bi bi-cloud-arrow-up me-1"></i> Upload Video
                  </>
                )}
              </button>
            </div>
          </>
        )}

        {/* ── Phase: Preview ── */}
        {(phase === "preview" || phase === "analyzing") && uploadedInfo && (
          <div className="card mb-3">
            <div className="card-header bg-white d-flex justify-content-between align-items-center">
              <h5 className="mb-0">
                <i className="bi bi-check-circle-fill text-success me-2"></i>
                Upload Complete
              </h5>
              <button className="btn btn-sm btn-outline-secondary" onClick={handleReset}>
                <i className="bi bi-arrow-repeat me-1"></i> New Video
              </button>
            </div>
            <div className="card-body">
              <div className="row g-3 mb-3">
                <div className="col-sm-6">
                  <span className="text-muted small">File</span>
                  <p className="fw-medium mb-0">{uploadedInfo.file_name}</p>
                </div>
                <div className="col-sm-6">
                  <span className="text-muted small">Size</span>
                  <p className="fw-medium mb-0">{(uploadedInfo.size / 1024 / 1024).toFixed(1)} MB</p>
                </div>
              </div>

              {/* Video preview */}
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <video
                src={uploadedInfo.video_url}
                controls
                className="w-100 rounded mb-3"
                style={{ maxHeight: 400, background: "#000" }}
              />

              {/* Settings + Analyze */}
              <div className="card bg-light border-0 mb-0">
                <div className="card-body">
                  <div className="row g-3 align-items-end">
                    <div className="col-auto">
                      <label className="form-label small">Frames per second</label>
                      <input
                        type="number"
                        className="form-control form-control-sm"
                        style={{ width: 80 }}
                        min={1}
                        max={30}
                        value={fps}
                        onChange={(e) => setFps(Number(e.target.value))}
                        disabled={phase === "analyzing"}
                      />
                    </div>
                    <div className="col-auto">
                      <button
                        className="btn btn-sm btn-outline-secondary"
                        onClick={() => setShowAdvanced(!showAdvanced)}
                      >
                        <i className={`bi ${showAdvanced ? "bi-chevron-up" : "bi-chevron-down"} me-1`}></i>
                        Advanced
                      </button>
                    </div>
                    <div className="col-auto ms-auto">
                      <button
                        className="btn btn-primary btn-lg"
                        disabled={phase === "analyzing"}
                        onClick={handleAnalyze}
                      >
                        {phase === "analyzing" ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-2"></span>
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <i className="bi bi-play-fill me-1"></i> Analyze Video
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                  {showAdvanced && (
                    <div className="row g-3 mt-2">
                      <div className="col-md-6">
                        <label className="form-label small">System Prompt</label>
                        <textarea
                          className="form-control form-control-sm"
                          rows={3}
                          placeholder="Override the default system prompt..."
                          value={systemPrompt}
                          onChange={(e) => setSystemPrompt(e.target.value)}
                          disabled={phase === "analyzing"}
                        />
                      </div>
                      <div className="col-md-6">
                        <label className="form-label small">Frame Analysis Prompt</label>
                        <textarea
                          className="form-control form-control-sm"
                          rows={3}
                          placeholder="Custom prompt for frame-level analysis..."
                          value={framePrompt}
                          onChange={(e) => setFramePrompt(e.target.value)}
                          disabled={phase === "analyzing"}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="col-lg-4">
        <div className="card">
          <div className="card-body">
            <h6><i className="bi bi-info-circle me-1"></i> How it works</h6>
            <ol className="small text-muted ps-3">
              <li><strong>Upload</strong> a video file to Azure Storage</li>
              <li><strong>Preview</strong> the video and configure settings</li>
              <li>Click <strong>Analyze</strong> to start AI processing</li>
              <li>Frames are extracted at the configured FPS</li>
              <li>Each frame is analyzed by Azure OpenAI GPT-4o</li>
              <li>Audio is transcribed with Whisper</li>
              <li>Summaries and embeddings are stored in <strong>{vectorStoreType}</strong></li>
              <li>Results are available for semantic search</li>
            </ol>
          </div>
        </div>

        {/* Steps indicator */}
        <div className="card mt-3">
          <div className="card-body">
            <h6 className="mb-3"><i className="bi bi-list-check me-1"></i> Progress</h6>
            <div className="d-flex flex-column gap-2">
              {(() => {
                const steps: Array<{ label: string; state: "active" | "done" | "pending" }> = [
                  {
                    label: "Upload to Azure",
                    state: phase === "select" || phase === "uploading" ? "active" : "done",
                  },
                  {
                    label: "Preview & Configure",
                    state: phase === "preview" ? "active" : phase === "analyzing" ? "done" : "pending",
                  },
                  {
                    label: "AI Analysis",
                    state: phase === "analyzing" ? "active" : "pending",
                  },
                ];
                return steps.map((s) => (
                  <div
                    key={s.label}
                    className={`d-flex align-items-center gap-2 ${
                      s.state === "active" ? "text-primary fw-semibold" : s.state === "done" ? "text-success" : "text-muted"
                    }`}
                  >
                    <i className={`bi ${
                      s.state === "done" ? "bi-check-circle-fill" : s.state === "active" ? "bi-arrow-repeat" : "bi-circle"
                    }`}></i>
                    <span>{s.label}</span>
                  </div>
                ));
              })()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
