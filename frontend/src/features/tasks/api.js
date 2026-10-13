import { get, patch, post, put } from "../../api/client.js";

export function listMyCourses() {
  return get("/api/courses/mine");
}

export function listTasks(courseId) {
  return get(`/api/courses/${courseId}/tasks`);
}

export function getTask(courseId, taskId) {
  return get(`/api/courses/${courseId}/tasks/${taskId}`);
}

export function createTask(courseId, payload) {
  return post(`/api/courses/${courseId}/tasks`, payload);
}

export function updateTask(courseId, taskId, payload) {
  return put(`/api/courses/${courseId}/tasks/${taskId}`, payload);
}

export function setTaskActive(courseId, taskId, active) {
  return patch(`/api/courses/${courseId}/tasks/${taskId}`, { active });
}
