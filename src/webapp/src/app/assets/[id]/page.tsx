"use client";

import { use } from "react";
import { AssetDetailTab } from "@/app/analyze/asset-detail-tab";

interface Props {
  params: Promise<{ id: string }>;
}

export default function AssetDetailPage({ params }: Props) {
  const { id } = use(params);

  return (
    <>
      <div className="page-header">
        <h2 className="mb-1">Asset Details</h2>
      </div>
      <AssetDetailTab assetId={id} />
    </>
  );
}
