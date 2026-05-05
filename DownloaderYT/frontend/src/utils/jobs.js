export function flattenJobItems(jobs = []) {
  return jobs.flatMap((job) =>
    (job.items || []).map((item) => ({
      ...item,
      job,
      job_id: item.job_id || job.id,
      displayTitle: item.title || inferTitleFromUrl(item.source_url),
    })),
  );
}

export function inferTitleFromUrl(url) {
  if (!url) return "Video de YouTube";
  try {
    const parsed = new URL(url);
    return parsed.searchParams.get("v") ? `Video ${parsed.searchParams.get("v")}` : parsed.hostname;
  } catch {
    return "Video de YouTube";
  }
}

export function splitUrls(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}
