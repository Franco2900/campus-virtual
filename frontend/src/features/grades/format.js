export function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  const number = Number(value);
  if (Number.isNaN(number)) {
    return "—";
  }
  return number.toFixed(2);
}

export function formatDueDate(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("es-AR", { dateStyle: "medium", timeStyle: "short" });
}
