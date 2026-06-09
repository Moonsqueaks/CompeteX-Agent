import { getDefaultApiBaseUrl } from "../api";

const RAW_ASSET_PREFIX = "/assets/raw/";
const RAW_DATA_PREFIX = "data/raw/";

export function resolveBackendAssetUrl(value: string | null | undefined) {
  const path = value?.trim();
  if (!path) {
    return null;
  }

  if (/^(blob:|data:|https?:\/\/)/i.test(path)) {
    return path;
  }

  if (path.startsWith(RAW_ASSET_PREFIX)) {
    return `${getDefaultApiBaseUrl()}${path}`;
  }

  if (path.startsWith(RAW_DATA_PREFIX)) {
    const rawPath = path.slice(RAW_DATA_PREFIX.length);
    return `${getDefaultApiBaseUrl()}${RAW_ASSET_PREFIX}${encodePathSegments(rawPath)}`;
  }

  return path;
}

function encodePathSegments(path: string) {
  return path
    .split("/")
    .filter((segment) => segment.length > 0)
    .map((segment) => encodeURIComponent(segment))
    .join("/");
}
