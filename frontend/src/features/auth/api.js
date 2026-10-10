import { get, post } from "../../api/client.js";

export function registerUser({ firstName, lastName, email, password }) {
  return post("/api/auth/register", {
    first_name: firstName,
    last_name: lastName,
    email,
    password,
  });
}

export function login({ email, password }) {
  return post("/api/auth/login", { email, password });
}

export function getMe() {
  return get("/api/auth/me");
}

export function logout() {
  return post("/api/auth/logout");
}