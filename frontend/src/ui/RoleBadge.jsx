import { getRoleMeta } from "./roles.js";

export default function RoleBadge({ role, showLabel = true, className = "" }) {
  const meta = getRoleMeta(role);
  return (
    <span
      className={`role-chip ${className}`.trim()}
      style={{ color: meta.color, background: meta.soft }}
      data-testid={`role-badge-${role}`}
    >
      <i className={`bi ${meta.icon}`} aria-hidden="true" />
      {showLabel && meta.label}
    </span>
  );
}
