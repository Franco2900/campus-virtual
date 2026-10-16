import { get, patch, post, put } from "../../api/client.js";

export function listUsers({ q, role, active } = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries({ q, role, active })) {
    if (value === undefined || value === null) continue;
    if (typeof value === "string" && value.trim() === "") continue;
    params.set(key, value);
  }
  const search = params.toString();
  return get(search ? `/api/users?${search}` : "/api/users");
}

export function getUser(id) {
  return get(`/api/users/${id}`);
}

export function updateUser(id, { first_name, last_name, email, role }) {
  return put(`/api/users/${id}`, { first_name, last_name, email, role });
}

export function setUserActive(id, active) {
  return patch(`/api/users/${id}`, { active });
}

export function resetUserPassword(id, password) {
  return post(`/api/users/${id}/password`, { password });
}
