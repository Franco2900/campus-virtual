import { del, get, post } from "../../api/client.js";

export function getHistory() {
  return get("/api/chat/messages");
}

export function sendMessage(content) {
  return post("/api/chat/messages", { content });
}

export function deleteHistory() {
  return del("/api/chat/messages");
}
