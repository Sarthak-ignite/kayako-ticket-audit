import path from "node:path";

/**
 * The Next.js app lives in `web/`, while data files live in the repo root under `data/`.
 * - Local dev: process.cwd() is `web/`, so we go up one level
 * - Vercel: process.cwd() is the repo root (since we build from root via vercel.json)
 */
export function getRepoRoot(): string {
  if (process.env.REPO_ROOT) {
    return path.resolve(process.env.REPO_ROOT);
  }

  // On Vercel, cwd is the repo root; locally (in web/), we need to go up one level
  const cwd = process.cwd();
  if (cwd.endsWith("/web") || cwd.endsWith("\\web")) {
    return path.resolve(cwd, "..");
  }
  return cwd;
}

export function repoPath(...parts: string[]): string {
  return path.join(getRepoRoot(), ...parts);
}


