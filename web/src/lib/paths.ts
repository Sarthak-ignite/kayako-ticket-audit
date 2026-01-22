import path from "node:path";

/**
 * The Next.js app lives in `web/`, while data files live in the repo root under `data/`.
 * In local/dev, `process.cwd()` will be the `web/` directory.
 */
export function getRepoRoot(): string {
  return process.env.REPO_ROOT
    ? path.resolve(process.env.REPO_ROOT)
    : path.resolve(process.cwd(), "..");
}

export function repoPath(...parts: string[]): string {
  return path.join(getRepoRoot(), ...parts);
}


