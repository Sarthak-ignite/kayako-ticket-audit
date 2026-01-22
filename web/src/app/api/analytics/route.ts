import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

import { getDataset } from "@/lib/datasets";
import { computeAnalytics } from "@/lib/analytics";

export async function GET(req: Request) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const url = new URL(req.url);
  const datasetId = url.searchParams.get("dataset") || "v6_sample";
  const dataset = getDataset(datasetId);

  const analytics = await computeAnalytics(dataset);

  return NextResponse.json({
    dataset: dataset.id,
    ...analytics,
  });
}
