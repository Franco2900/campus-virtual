import { get, patch, post, put } from "../../api/client.js";

export function listCourses() {
  return get("/api/courses");
}

export function getCourse(id) {
  return get(`/api/courses/${id}`);
}

export function createCourse({ name, code, description }) {
  return post("/api/courses", { name, code, description });
}

export function updateCourse(id, { name, code, description }) {
  return put(`/api/courses/${id}`, { name, code, description });
}

export function setCourseActive(id, active) {
  return patch(`/api/courses/${id}`, { active });
}
