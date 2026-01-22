import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

import { getDataset } from "@/lib/datasets";
import { queryTickets } from "@/lib/data";
import { OUR_PATTERNS, type PatternId } from "@/lib/types";

export async function GET(req: Request) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const url = new URL(req.url);
  const datasetId = url.searchParams.get("dataset") || "v6_sample";
  const dataset = getDataset(datasetId);

  const q = url.searchParams.get("q") || undefined;
  const vertical = url.searchParams.get("vertical") || undefined;
  const product = url.searchParams.get("product") || undefined;
  const status = url.searchParams.get("status") || undefined;
  const source = url.searchParams.get("source") || undefined;
  const onlySev1 = (url.searchParams.get("onlySev1") || "").toLowerCase() === "true";

  const patternsParam = url.searchParams.getAll("pattern");
  const patterns = patternsParam
    .filter((p) => (OUR_PATTERNS as readonly string[]).includes(p))
    .map((p) => p as PatternId);

  const sortParam = url.searchParams.get("sort") || "patterns_desc";
  const validSorts = ["updated_desc", "created_desc", "patterns_desc"] as const;
  const sort = validSorts.includes(sortParam as typeof validSorts[number])
    ? (sortParam as typeof validSorts[number])
    : "patterns_desc";

  const offsetRaw = Number.parseInt(url.searchParams.get("offset") || "0", 10);
  const limitRaw = Number.parseInt(url.searchParams.get("limit") || "50", 10);
  const offset = Number.isFinite(offsetRaw) && offsetRaw >= 0 ? offsetRaw : 0;
  const limit = Number.isFinite(limitRaw) && limitRaw >= 1 && limitRaw <= 200 ? limitRaw : 50;

  const { total, items } = await queryTickets(dataset, {
    datasetId,
    q,
    vertical,
    product,
    status,
    source,
    onlySev1,
    patterns,
    sort,
    offset,
    limit,
  });

  return NextResponse.json({
    dataset: dataset.id,
    total,
    items: items.map((t) => ({
      ticketId: t.ticketId,
      vertical: t.vertical,
      product: t.product,
      status: t.status,
      priority: t.priority,
      isSev1: t.isSev1,
      source: t.source,
      predictedLabels: t.predictedLabels,
      detectedCount: t.detectedCount,
    })),
  });
}


