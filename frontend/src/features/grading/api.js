import { get, put } from "../../api/client.js";

export function listMyCourses() {
  return get("/api/courses/mine");
}

export function listTasks(courseId) {
  return get(`/api/courses/${courseId}/tasks`);
}

export function getSubmissions(courseId, taskId) {
  return get(`/api/courses/${courseId}/tasks/${taskId}/submissions`);
}

export function gradeSubmission(courseId, taskId, studentId, data) {
  return put(`/api/courses/${courseId}/tasks/${taskId}/submissions/${studentId}/grade`, data);
}
