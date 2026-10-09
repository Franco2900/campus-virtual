const NETWORK_ERROR_MESSAGE = "No se pudo conectar con el servidor.";
const DEFAULT_ERROR_MESSAGE = "Ocurrió un error inesperado. Intentá nuevamente.";

function buildOptions(method, body) {
  if (body === undefined) {
    return { method };
  }
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

async function readJson(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function request(method, path, body) {
  let response;
  try {
    response = await fetch(path, buildOptions(method, body));
  } catch {
    throw new Error(NETWORK_ERROR_MESSAGE);
  }

  const data = await readJson(response);

  if (!response.ok) {
    const message =
      data && typeof data.error === "string" && data.error
        ? data.error
        : DEFAULT_ERROR_MESSAGE;
    throw new Error(message);
  }

  return data;
}

export function post(path, body) {
  return request("POST", path, body);
}

export function get(path) {
  return request("GET", path);
}
