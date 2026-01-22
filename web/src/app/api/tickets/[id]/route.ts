import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

import { getDataset } from "@/lib/datasets";
import { loadTicketDetail } from "@/lib/data";

export async function GET(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await ctx.params;
  const ticketId = Number.parseInt(id, 10);
  if (!Number.isFinite(ticketId) || ticketId <= 0) {
    return NextResponse.json({ error: "Invalid ticket id" }, { status: 400 });
  }

  const url = new URL(req.url);
  const datasetId = url.searchParams.get("dataset") || "v6_sample";
  const dataset = getDataset(datasetId);

  const detail = await loadTicketDetail(dataset, ticketId);
  return NextResponse.json(detail);
}


