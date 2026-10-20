import { del, get, postForm } from "../../api/client.js";

export function getSources() {
  return get("/api/knowledge/sources");
}

export function createSource(formData) {
  return postForm("/api/knowledge/sources", formData);
}

export function deleteSource(id) {
  return del(`/api/knowledge/sources/${id}`);
}
