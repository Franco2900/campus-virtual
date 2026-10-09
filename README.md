# Campus Virtual

Sistema web de gestión académica (campus virtual) con tres roles —Estudiante, Profesor y Administrador— y un asistente conversacional integrado.

Trabajo Práctico Integrador — Curso IA (UNLa) — Grupo 12.

## Vista previa

> PENDIENTE DE DEFINIR: capturas de la aplicación una vez implementada.

## Características

- Registro y autenticación de usuarios (CU-01, CU-02).
- Gestión de cursos, usuarios e inscripciones (CU-03, CU-04, CU-05).
- Gestión de tareas, entregas y correcciones (CU-06, CU-07, CU-08).
- Consulta de calificaciones y filtrado de usuarios (CU-09, CU-10).
- Chatbot asistente integrado con LangChain + Ollama.

## Tecnologías

| Área | Tecnología |
|------|-----------|
| Backend | Python + Flask |
| Frontend | React + Vite (Node) |
| Base de datos | SQLite |
| ORM | SQLAlchemy |
| Chatbot | LangChain + Ollama (local) |

Las versiones exactas están en `casos_de_uso.md` y en `AGENTS.md`.

## Requisitos previos

> PENDIENTE DE DEFINIR: versiones mínimas verificadas (Python, Node, pip/npm).

## Instalación

> PENDIENTE DE DEFINIR: pasos reales cuando exista el código (Fase 6).

## Ejecución

> PENDIENTE DE DEFINIR.

## Testing

> PENDIENTE DE DEFINIR.

## Estructura

```
/
├── AGENTS.md          # instrucciones para agentes de IA
├── README.md          # este archivo
├── opencode.json      # configuración de proyecto (MCP, permisos)
├── casos_de_uso.md    # especificación de los 10 casos de uso
├── decisiones.md      # registro de decisiones
├── errores.md         # bitácora de errores
├── progreso.md        # control de progreso
├── prompts_log.md     # auditoría de prompts
├── tiempos.md         # medición de tiempos
├── backend/           # API Flask (PENDIENTE DE DEFINIR)
└── frontend/          # SPA React (PENDIENTE DE DEFINIR)
```

## API

> PENDIENTE DE DEFINIR: tabla de endpoints cuando exista el backend.

## Configuración

> PENDIENTE DE DEFINIR: variables de entorno (por ejemplo, ruta de la base, secretos de sesión, configuración de Ollama).

## Servidores MCP (Model Context Protocol)

El desarrollo se apoya en tres servidores MCP. La configuración vive en `opencode.json` (proyecto) y en la config global de opencode (`~/.config/opencode/opencode.jsonc`).

| Servidor | Tipo | Origen | Rol en el desarrollo |
|----------|------|--------|----------------------|
| `engram` | Memoria (local) | Config global | Memoria persistente del proyecto: decisiones, gotchas y estado que sobreviven entre sesiones y a la compactación de contexto. |
| `context7` | Documentación (remoto/externo) | Config global | Documentación actualizada de Flask, SQLAlchemy, React, Vite, LangChain y Ollama; reduce APIs alucinadas por el modelo. Es el MCP externo requerido por la consigna. |
| `filesystem` | Filesystem (local) | `opencode.json` (proyecto) | Acceso a archivos acotado por allowlist a la carpeta del proyecto. Valor demostrativo del protocolo; opencode ya dispone de acceso a archivos nativo. |

- **Terminal:** se resuelve con la herramienta nativa de opencode (no se usa un MCP de terminal, por no existir un servidor oficial maduro).
- **Comando del MCP filesystem:** `cmd /c npx -y @modelcontextprotocol/server-filesystem "<ruta del proyecto>"`.
- **Portabilidad:** la ruta del MCP filesystem es específica de esta máquina. Para correr en otra máquina hay que ajustarla.

## Roadmap

- Migración a openspec (gestión spec-driven).
- Plugin de medición automática de tiempos.
- Integración completa del chatbot.
- Tests automatizados de backend y frontend.

## Licencia

> PENDIENTE DE DEFINIR.

## Contacto

- Figueroa, Franco Ariel — franco2900@gmail.com — GitHub: Franco2900
