"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { useSettings } from "@/lib/settings-context";

export default function HomePage() {
  const { health, mounted } = useSettings();
  const [archTab, setArchTab] = useState<"media" | "data">("data");

  return (
    <>
      {/* ── Hero Section ── */}
      <section className="hero-section rounded-4 mb-5 p-5 text-center">
        <span className="badge bg-primary bg-opacity-10 text-primary mb-3 px-3 py-2">
          <i className="bi bi-lightning-charge-fill me-1"></i>
          Powered by Azure AI
        </span>
        <h1 className="display-5 fw-bold mb-3">
          <i className="bi bi-play-circle-fill text-primary me-2"></i>
          ClipCognition
        </h1>
        <p className="lead text-muted mb-4 mx-auto" style={{ maxWidth: "700px" }}>
          Intelligent Video Analytics &mdash; upload videos, extract frames,
          transcribe audio, generate AI summaries, and search across your
          entire video library using semantic similarity.
        </p>
        <div className="d-flex gap-3 flex-wrap justify-content-center">
          <Link href="/analyze" className="btn btn-primary btn-lg px-4">
            <i className="bi bi-cloud-arrow-up me-2"></i>
            Analyze a Video
          </Link>
          <Link href="/search" className="btn btn-outline-secondary btn-lg px-4">
            <i className="bi bi-search me-2"></i>
            Semantic Search
          </Link>
          <Link href="/dashboard" className="btn btn-outline-dark btn-lg px-4">
            <i className="bi bi-speedometer2 me-2"></i>
            Dashboard
          </Link>
        </div>
      </section>

      {/* ── Capability Cards ── */}
      <section className="card mb-5 p-4">
        <h3 className="text-center mb-2">How It Works</h3>
        <p className="text-center text-muted mb-4">Three steps from raw video to semantic search</p>
        <div className="row g-4">
          <div className="col-md-4">
            <div className="card feature-card h-100 text-center p-4">
              <div className="feature-icon bg-primary bg-opacity-10 text-primary mx-auto mb-3">
                <i className="bi bi-cloud-arrow-up-fill fs-3"></i>
              </div>
              <h5>1. Upload &amp; Analyze</h5>
              <p className="text-muted mb-0">
                Upload a video file. ClipCognition extracts frames at your
                chosen interval, transcribes audio with Whisper, and generates
                GPT-4o summaries for every frame.
              </p>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card feature-card h-100 text-center p-4">
              <div className="feature-icon bg-success bg-opacity-10 text-success mx-auto mb-3">
                <i className="bi bi-database-fill-gear fs-3"></i>
              </div>
              <h5>2. Store &amp; Index</h5>
              <p className="text-muted mb-0">
                Summaries and vector embeddings are persisted in Azure Cosmos DB
                (NoSQL or DocumentDB) with vector indexing. Media files are stored
                in Azure Blob Storage.
              </p>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card feature-card h-100 text-center p-4">
              <div className="feature-icon bg-warning bg-opacity-10 text-warning mx-auto mb-3">
                <i className="bi bi-search-heart-fill fs-3"></i>
              </div>
              <h5>3. Search &amp; Discover</h5>
              <p className="text-muted mb-0">
                Ask natural-language questions across your video library.
                Semantic vector search returns the most relevant frames and
                plays the source video.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Tech Stack ── */}
      <section className="mb-5">
        <div className="row g-4">
          <div className="col-lg-4">
            <h3 className="mb-3">Technology Stack</h3>
            <p className="text-muted mb-4">
              Built on Azure&apos;s enterprise-grade AI and data platform
            </p>
            <ul className="list-unstyled tech-list">
              <li>
                <i className="bi bi-stars text-primary me-2"></i>
                <strong>Azure OpenAI</strong>{" \u2014 GPT-4o vision & Whisper"}
              </li>
              <li>
                <i className="bi bi-database text-primary me-2"></i>
                <strong>CosmosDB</strong>{" \u2014 Operational + vector store"}
              </li>
              <li>
                <i className="bi bi-hdd-stack text-primary me-2"></i>
                <strong>DocumentDB</strong>{" \u2014 MongoDB-compatible vectors"}
              </li>
              <li>
                <i className="bi bi-cloud text-primary me-2"></i>
                <strong>Azure Blob Storage</strong>{" \u2014 Video & frame media"}
              </li>
              <li>
                <i className="bi bi-code-slash text-primary me-2"></i>
                <strong>FastAPI + Next.js</strong>{" \u2014 Modern full-stack"}
              </li>
              <li>
                <i className="bi bi-shield-lock text-primary me-2"></i>
                <strong>Managed Identity</strong>{" \u2014 Passwordless RBAC"}
              </li>
            </ul>

            {/* Live backend status */}
            {mounted && health && (
              <div className="card bg-light border-0 p-3 mt-3">
                <h6 className="mb-2"><i className="bi bi-activity me-1"></i> Backend Status</h6>
                <div className="d-flex gap-4">
                  <span className="backend-indicator">
                    <span className={`dot ${health.backends.cosmosdb_nosql ? "healthy" : "unhealthy"}`}></span>
                    CosmosDB
                  </span>
                  <span className="backend-indicator">
                    <span className={`dot ${health.backends.azure_documentdb ? "healthy" : "unhealthy"}`}></span>
                    DocumentDB
                  </span>
                </div>
                <small className="text-muted mt-1 d-block">v{health.version}</small>
              </div>
            )}
          </div>
          <div className="col-lg-8">
            <div className="card">
              <div className="card-header bg-white">
                <ul className="nav nav-tabs card-header-tabs">
                  <li className="nav-item">
                    <button
                      className={`nav-link ${archTab === "data" ? "active" : ""}`}
                      onClick={() => setArchTab("data")}
                    >
                      DocumentDB
                    </button>
                  </li>
                  <li className="nav-item">
                    <button
                      className={`nav-link ${archTab === "media" ? "active" : ""}`}
                      onClick={() => setArchTab("media")}
                    >
                      Cosmos DB
                    </button>
                  </li>
                </ul>
              </div>
              <div className="card-body text-center p-4">
                <Image
                  src={archTab === "media" ? "/arch_cosmosdb.png" : "/arch_docdb.png"}
                  alt={archTab === "media" ? "Media RAG with Cosmos DB" : "Media RAG with DocumentDB"}
                  width={800}
                  height={500}
                  className="img-fluid rounded"
                />
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
