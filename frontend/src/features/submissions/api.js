import { del, get, post, put } from "../../api/client.js";

export function listMyCourses() {
  return get("/api/courses/mine");
}

export function listTasks(courseId) {
  return get(`/api/courses/${courseId}/tasks`);
}

export function createSubmission(courseId, taskId, payload) {
  return post(`/api/courses/${courseId}/tasks/${taskId}/submission`, payload);
}

export function updateSubmission(courseId, taskId, payload) {
  return put(`/api/courses/${courseId}/tasks/${taskId}/submission`, payload);
}

export function deleteSubmission(courseId, taskId) {
  return del(`/api/courses/${courseId}/tasks/${taskId}/submission`);
}
