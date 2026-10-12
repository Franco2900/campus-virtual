import { del, get, patch, post } from "../../api/client.js";

export function listMyCourses() {
  return get("/api/courses/mine");
}

export function listStudents(courseId) {
  return get(`/api/courses/${courseId}/students`);
}

export function enrollStudent(courseId, studentId) {
  return post(`/api/courses/${courseId}/students`, { student_id: studentId });
}

export function setEnrollmentActive(courseId, studentId, active) {
  return patch(`/api/courses/${courseId}/students/${studentId}`, { active });
}

export function removeEnrollment(courseId, studentId) {
  return del(`/api/courses/${courseId}/students/${studentId}`);
}
