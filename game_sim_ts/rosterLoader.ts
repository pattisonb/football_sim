import { RawLeagueData, RawTeamData } from "./types";

// Browser-friendly roster loader utilities. In a web app, you can either:
// - fetch JSON from a URL, or
// - pass a pre-parsed JS object (e.g., imported via bundler).

export async function fetchRosterFromUrl(url: string): Promise<RawTeamData[]> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch roster json: ${res.status}`);
  const data = (await res.json()) as RawLeagueData;
  return data.teams;
}

export function parseRosterObject(obj: RawLeagueData): RawTeamData[] {
  return obj.teams;
}


