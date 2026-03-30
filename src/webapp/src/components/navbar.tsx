"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSettings } from "@/lib/settings-context";
import type { VectorStoreType } from "@/lib/types";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "bi-speedometer2" },
  { href: "/analyze", label: "Video Analysis", icon: "bi-camera-video" },
  { href: "/search", label: "Semantic Search", icon: "bi-search" },
];

export function Navbar() {
  const pathname = usePathname();
  const { vectorStoreType, setVectorStoreType, health, mounted } = useSettings();

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark px-3">
      <Link className="navbar-brand d-flex align-items-center gap-2" href="/">
        <i className="bi bi-play-circle-fill fs-4"></i>
        ClipCognition
      </Link>

      <button
        className="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#mainNav"
      >
        <span className="navbar-toggler-icon"></span>
      </button>

      <div className="collapse navbar-collapse" id="mainNav">
        <ul className="navbar-nav me-auto">
          {NAV_ITEMS.map((item) => (
            <li className="nav-item" key={item.href}>
              <Link
                className={`nav-link${mounted && pathname === item.href ? " active" : ""}`}
                href={item.href}
              >
                <i className={`bi ${item.icon} me-1`}></i>
                {item.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="d-flex align-items-center gap-3">
          {/* Backend health indicators */}
          {mounted && health && (
            <div className="d-flex gap-3">
              <span className="backend-indicator text-light">
                <span className={`dot ${health.backends.cosmosdb_nosql ? "healthy" : "unhealthy"}`}></span>
                CosmosDB
              </span>
              <span className="backend-indicator text-light">
                <span className={`dot ${health.backends.azure_documentdb ? "healthy" : "unhealthy"}`}></span>
                DocumentDB
              </span>
            </div>
          )}

          {/* Global vector store selector */}
          <select
            className="form-select form-select-sm bg-dark text-light border-secondary"
            style={{ width: "auto" }}
            value={vectorStoreType}
            onChange={(e) => setVectorStoreType(e.target.value as VectorStoreType)}
          >
            <option value="DocumentDB">DocumentDB</option>
            <option value="CosmosDB">CosmosDB</option>
          </select>
        </div>
      </div>
    </nav>
  );
}
