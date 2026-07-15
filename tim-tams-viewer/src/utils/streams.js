/**
 * Fetches all stream metadata by loading a static manifest file.
 * The manifest is generated at build time and lists all available stream files.
 */

// Use a relative path so it works regardless of the Vite base path
const MANIFEST_URL = './data/streams-manifest.json';

/**
 * Fetches the manifest of available stream files.
 */
async function loadManifest() {
  const response = await fetch(MANIFEST_URL);
  if (!response.ok) {
    throw new Error(`Failed to load streams manifest: ${response.status}`);
  }
  return response.json();
}

/**
 * Returns an array of { date, time, fileUrl } for all available streams,
 * sorted by date descending.
 */
export async function getAvailableStreams() {
  const filenames = await loadManifest();
  const results = [];

  for (const filename of filenames) {
    const match = filename.match(/^timestamps_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.json$/);
    if (match) {
      const [, date, time] = match;
      results.push({ date, time, file: `./data/streams/${filename}` });
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
  const response = await fetch(filePath);
  if (!response.ok) {
    throw new Error(`Failed to fetch stream data: ${response.status}`);
  }
  return response.json();
}

/**
 * Returns a list of unique dates that have stream data, sorted descending.
 */
export async function getAvailableDates() {
  const streams = await getAvailableStreams();
  const dateSet = new Set(streams.map((s) => s.date));
  return Array.from(dateSet).sort((a, b) => b.localeCompare(a));
}
