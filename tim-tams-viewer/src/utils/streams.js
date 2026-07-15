/**
 * Fetches all stream metadata by listing the known timestamp files.
 * Since we can't directory-list at runtime, we scan the public/streams folder
 * by trying to fetch each file. Returns an array of { date, time, file }.
 */

const STREAMS_DIR = '/data/streams/';
const FILE_PREFIX = 'timestamps_';
const FILE_SUFFIX = '.json';

// We'll discover files by fetching a manifest-like approach:
// Since Vite doesn't expose directory listings, we use a trick:
// import.meta.glob to get all matching files at build time.

export const streamFiles = import.meta.glob('/data/streams/timestamps_*.json', {
  eager: false,
  query: '?url',
  import: 'default',
});

/**
 * Returns an array of { date, time, fileUrl } for all available streams,
 * sorted by date descending.
 */
export async function getAvailableStreams() {
  const entries = Object.entries(streamFiles);
  const results = [];

  for (const [path, _load] of entries) {
    // Extract date and time from filename: timestamps_2026-06-29_19-54-49.json
    const filename = path.split('/').pop();
    const match = filename.match(/^timestamps_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.json$/);
    if (match) {
      const [, date, time] = match;
      results.push({ date, time, file: path });
    }
  }

  // Sort by date descending, then time descending
  results.sort((a, b) => {
    const dateCompare = b.date.localeCompare(a.date);
    if (dateCompare !== 0) return dateCompare;
    return b.time.localeCompare(a.time);
  });

  return results;
}

/**
 * Fetches the full timestamp data for a given stream file path.
 */
export async function fetchStreamData(filePath) {
  const mod = await import(filePath);
  return mod.default;
}

/**
 * Returns a list of unique dates that have stream data, sorted descending.
 */
export async function getAvailableDates() {
  const streams = await getAvailableStreams();
  const dateSet = new Set(streams.map((s) => s.date));
  return Array.from(dateSet).sort((a, b) => b.localeCompare(a));
}
