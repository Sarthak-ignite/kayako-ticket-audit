import Link from "next/link";
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";

function TicketIcon() {
  return (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 6v.75m0 3v.75m0 3v.75m0 3V18m-9-5.25h5.25M7.5 15h3M3.375 5.25c-.621 0-1.125.504-1.125 1.125v3.026a2.999 2.999 0 0 1 0 5.198v3.026c0 .621.504 1.125 1.125 1.125h17.25c.621 0 1.125-.504 1.125-1.125v-3.026a2.999 2.999 0 0 1 0-5.198V6.375c0-.621-.504-1.125-1.125-1.125H3.375Z" />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg className="h-4 w-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
    </svg>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  href,
  variant = "primary",
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  href: string;
  variant?: "primary" | "secondary";
}) {
  const baseStyles = "group relative overflow-hidden rounded-2xl border p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl";
  const variantStyles = variant === "primary"
    ? "border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 dark:border-blue-900/50 dark:from-blue-950/40 dark:to-indigo-950/30"
    : "border-zinc-200 bg-gradient-to-br from-zinc-50 to-white dark:border-zinc-800 dark:from-zinc-900 dark:to-zinc-950";

  const iconStyles = variant === "primary"
    ? "bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400"
    : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400";

  return (
    <Link href={href} className={`${baseStyles} ${variantStyles}`}>
      <div className={`mb-4 inline-flex rounded-xl p-3 ${iconStyles}`}>
        {icon}
      </div>
      <h3 className="mb-2 text-lg font-semibold text-zinc-900 dark:text-zinc-50">{title}</h3>
      <p className="mb-4 text-sm text-zinc-600 dark:text-zinc-400">{description}</p>
      <div className="flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400">
        <span>Explore</span>
        <ArrowIcon />
      </div>
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
    </Link>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 text-zinc-900 dark:from-zinc-950 dark:to-black dark:text-zinc-50">
      <div className="mx-auto flex max-w-4xl flex-col gap-8 p-8">
        <header className="flex items-center justify-between">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-500" />
              Phase 0 POC
            </div>
            <h1 className="text-3xl font-bold tracking-tight">Ticket Review Dashboard</h1>
            <p className="mt-2 text-zinc-600 dark:text-zinc-400">
              AI-powered analysis of support ticket quality patterns and service metrics.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <SignedIn>
              <UserButton />
            </SignedIn>
          </div>
        </header>

        <SignedOut>
          <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-lg dark:border-zinc-800 dark:bg-zinc-950">
            <div className="relative p-8">
              <div className="absolute right-0 top-0 h-64 w-64 -translate-y-1/2 translate-x-1/2 rounded-full bg-gradient-to-br from-blue-500/10 to-purple-500/10 blur-3xl" />
              <div className="relative">
                <h2 className="text-xl font-semibold">Welcome</h2>
                <p className="mt-2 text-zinc-600 dark:text-zinc-400">
                  Sign in to access the ticket analysis dashboard, view detected patterns, and explore service quality metrics.
                </p>
                <div className="mt-6 flex gap-3">
                  <Link
                    className="group inline-flex items-center gap-2 rounded-xl bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white transition-all hover:bg-zinc-800 hover:shadow-lg dark:bg-zinc-50 dark:text-black dark:hover:bg-zinc-200"
                    href="/sign-in"
                  >
                    Sign in
                    <ArrowIcon />
                  </Link>
                  <Link
                    className="rounded-xl border border-zinc-300 px-5 py-2.5 text-sm font-medium transition-all hover:border-zinc-400 hover:bg-zinc-50 dark:border-zinc-700 dark:hover:border-zinc-600 dark:hover:bg-zinc-900"
                    href="/sign-up"
                  >
                    Create account
                  </Link>
                </div>
              </div>
            </div>
          </section>
        </SignedOut>

        <SignedIn>
          <section className="overflow-hidden rounded-2xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-teal-50 p-4 dark:border-emerald-900/50 dark:from-emerald-950/30 dark:to-teal-950/20">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-emerald-100 p-2 dark:bg-emerald-900/50">
                <svg className="h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
              </div>
              <p className="text-sm text-emerald-800 dark:text-emerald-200">
                <span className="font-medium">Signed in successfully.</span> Explore tickets or view aggregate analytics below.
              </p>
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2">
            <FeatureCard
              icon={<TicketIcon />}
              title="Browse Tickets"
              description="Search, filter, and review individual support tickets with detected quality patterns and AI reasoning."
              href="/tickets"
              variant="primary"
            />
            <FeatureCard
              icon={<ChartIcon />}
              title="Analytics Dashboard"
              description="View aggregate metrics, pattern distributions, heatmaps, and product performance across all tickets."
              href="/analytics"
              variant="secondary"
            />
          </section>

          <section className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Detection Patterns
            </h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="flex items-center gap-3 rounded-xl border border-purple-200 bg-purple-50 p-3 dark:border-purple-900/50 dark:bg-purple-950/30">
                <span className="h-2 w-2 rounded-full bg-purple-500" />
                <span className="text-sm font-medium text-purple-700 dark:text-purple-300">AI Quality Failures</span>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-orange-200 bg-orange-50 p-3 dark:border-orange-900/50 dark:bg-orange-950/30">
                <span className="h-2 w-2 rounded-full bg-orange-500" />
                <span className="text-sm font-medium text-orange-700 dark:text-orange-300">AI Wall / Looping</span>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-blue-200 bg-blue-50 p-3 dark:border-blue-900/50 dark:bg-blue-950/30">
                <span className="h-2 w-2 rounded-full bg-blue-500" />
                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">Ignoring Context</span>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-900/50 dark:bg-amber-950/30">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                <span className="text-sm font-medium text-amber-700 dark:text-amber-300">Response Delays</span>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 p-3 dark:border-rose-900/50 dark:bg-rose-950/30">
                <span className="h-2 w-2 rounded-full bg-rose-500" />
                <span className="text-sm font-medium text-rose-700 dark:text-rose-300">Premature Closure</span>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-3 dark:border-red-900/50 dark:bg-red-950/30">
                <span className="h-2 w-2 rounded-full bg-red-500" />
                <span className="text-sm font-medium text-red-700 dark:text-red-300">P1/SEV1 Mishandling</span>
              </div>
            </div>
          </section>
        </SignedIn>

        <footer className="text-center text-xs text-zinc-500 dark:text-zinc-500">
          Kayako Ticket Audit System | Phase 0 Proof of Concept
        </footer>
      </div>
    </main>
  );
}
