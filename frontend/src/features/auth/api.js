import { post } from "../../api/client.js";

export function registerUser({ firstName, lastName, email, password }) {
  return post("/api/auth/register", {
    first_name: firstName,
    last_name: lastName,
    email,
    password,
  });
}
