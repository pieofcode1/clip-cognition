"use client";

import { useSettings } from "@/lib/settings-context";
import { UploadTab } from "./upload-tab";

export function AnalyzeContent() {
  const { vectorStoreType } = useSettings();

  return (
    <>
      <div className="page-header">
        <h2 className="mb-1">Video Analysis</h2>
        <p className="text-muted mb-0">
          Upload and analyze videos with Azure AI &middot;{" "}
          <span className="fw-semibold">{vectorStoreType}</span>
        </p>
      </div>

      <UploadTab />
    </>
  );
}
