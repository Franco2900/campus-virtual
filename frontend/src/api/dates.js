const TIMEZONE_SUFFIX = /(?:Z|[+-]\d{2}:?\d{2})$/;

export function parseServerDate(value) {
  if (!value) {
    return null;
  }
  const source = TIMEZONE_SUFFIX.test(value) ? value : `${value}Z`;
  const date = new Date(source);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDueDate(value) {
  const date = parseServerDate(value);
  if (!date) {
    return "—";
  }
  return date.toLocaleString("es-AR", { dateStyle: "medium", timeStyle: "short" });
}

export function isoToLocalInput(value) {
  const date = parseServerDate(value);
  if (!date) {
    return "";
  }
  const pad = (part) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
