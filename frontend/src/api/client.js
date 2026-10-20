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
      data && typeof data.error === "string" && data.error ? data.error : DEFAULT_ERROR_MESSAGE;
    throw new Error(message);
  }

  return data;
}

async function formRequest(path, formData) {
  let response;
  try {
    // Sin Content-Type manual: el browser agrega el boundary del multipart.
    response = await fetch(path, { method: "POST", body: formData });
  } catch {
    throw new Error(NETWORK_ERROR_MESSAGE);
  }

  const data = await readJson(response);

  if (!response.ok) {
    const message =
      data && typeof data.error === "string" && data.error ? data.error : DEFAULT_ERROR_MESSAGE;
    throw new Error(message);
  }

  return data;
}

export function post(path, body) {
  return request("POST", path, body);
}

export function postForm(path, formData) {
  return formRequest(path, formData);
}

export function put(path, body) {
  return request("PUT", path, body);
}

export function patch(path, body) {
  return request("PATCH", path, body);
}

export function get(path) {
  return request("GET", path);
}

export function del(path) {
  return request("DELETE", path);
}
