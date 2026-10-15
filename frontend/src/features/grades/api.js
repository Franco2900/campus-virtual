import { get } from "../../api/client.js";

export function listMyCourses() {
  return get("/api/courses/mine");
}

export function getGrades(courseId) {
  return get(`/api/courses/${courseId}/grades`);
}
