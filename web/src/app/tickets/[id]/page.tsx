import Link from "next/link";
import { UserButton } from "@clerk/nextjs";

import { getDataset } from "@/lib/datasets";
import { loadTicketDetail } from "@/lib/data";
import { TranscriptViewer } from "@/components/TranscriptViewer";
import { HardMetricsSection } from "@/components/HardMetricsSection";
import { LLMPatternsSection } from "@/components/LLMPatternsSection";

export default async function TicketDetailPage(props: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await props.params;
  const ticketId = Number.parseInt(id, 10);
  const sp = await props.searchParams;
  const datasetId = (sp.dataset as string) || "v6_sample";
  const dataset = getDataset(datasetId);

  const detail = await loadTicketDetail(dataset, ticketId);
  const summary = detail.summary || {};
  const result = detail.result;
  const transcript = detail.transcript || [];
  const hardMetrics = detail.hardMetrics;

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-black dark:text-zinc-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 p-8">
        {/* Header */}
        <header className="flex items-start justify-between gap-4">
          <div>
            <div className="text-sm text-zinc-600 dark:text-zinc-400">
              <Link
                className="underline hover:text-zinc-900 dark:hover:text-zinc-200"
                href={`/tickets?dataset=${dataset.id}`}
              >
                Tickets
              </Link>{" "}
              / {ticketId}
            </div>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight">
              Ticket {ticketId}
            </h1>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Dataset: <span className="font-medium">{dataset.label}</span>
              {result?._model ? (
                <>
                  {" "}
                  • Model:{" "}
                  <span className="font-medium">{String(result._model)}</span>
                </>
              ) : null}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              className="text-sm underline text-zinc-700 hover:text-zinc-900 dark:text-zinc-300"
              href="/"
            >
              Home
            </Link>
            <UserButton />
          </div>
        </header>

        {/* Basic Info Cards */}
        <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Product
            </div>
            <div className="mt-1 text-sm font-medium">
              {summary.Product || "-"}
            </div>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Status
            </div>
            <div className="mt-1 text-sm font-medium">
              {summary.Status || "-"}
            </div>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Priority
            </div>
            <div className="mt-1 text-sm font-medium">
              {summary.Priority || "-"}
              {String(summary.isSev1 || "").trim() === "1" && (
                <span className="ml-2 rounded bg-red-100 px-1.5 py-0.5 text-xs font-semibold text-red-700 dark:bg-red-900/50 dark:text-red-300">
                  SEV1
                </span>
              )}
            </div>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Vertical
            </div>
            <div className="mt-1 text-sm font-medium">
              {summary.vertical || summary.Brand || "-"}
            </div>
          </div>
        </section>

        {/* Hard Metrics Section */}
        <HardMetricsSection metrics={hardMetrics} />

        {/* LLM Patterns Section */}
        <LLMPatternsSection result={result} />

        {/* Transcript Viewer */}
        <TranscriptViewer transcript={transcript} />
      </div>
    </main>
  );
}
