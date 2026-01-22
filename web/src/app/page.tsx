import Link from "next/link";
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";

export default function Home() {
  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-black dark:text-zinc-50">
      <div className="mx-auto flex max-w-4xl flex-col gap-8 p-8">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Ticket Review Dashboard</h1>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Review detected patterns and evidence across the Phase 0 sample.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <SignedIn>
              <UserButton />
            </SignedIn>
          </div>
        </header>

        <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <SignedOut>
            <p className="text-sm text-zinc-700 dark:text-zinc-300">
              Please sign in to view tickets and transcripts.
            </p>
            <div className="mt-4 flex gap-3">
              <Link
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-black dark:hover:bg-zinc-200"
                href="/sign-in"
              >
                Sign in
              </Link>
              <Link
                className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
                href="/sign-up"
              >
                Sign up
              </Link>
            </div>
          </SignedOut>

          <SignedIn>
            <p className="text-sm text-zinc-700 dark:text-zinc-300">
              You&apos;re signed in. View individual tickets or access aggregate analytics.
            </p>
            <div className="mt-4 flex gap-3">
              <Link
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-black dark:hover:bg-zinc-200"
                href="/tickets"
              >
                Browse Tickets
              </Link>
              <Link
                className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
                href="/analytics"
              >
                Analytics Dashboard
              </Link>
            </div>
          </SignedIn>
        </section>
      </div>
    </main>
  );
}
