import { formatDueDate } from "../../api/dates.js";

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

export { formatDueDate };
