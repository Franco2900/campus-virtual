export const ROLE_META = {
  student: {
    label: "Estudiante",
    icon: "bi-mortarboard-fill",
    color: "var(--role-student)",
    soft: "var(--role-student-soft)",
  },
  teacher: {
    label: "Profesor",
    icon: "bi-easel-fill",
    color: "var(--role-teacher)",
    soft: "var(--role-teacher-soft)",
  },
  admin: {
    label: "Administrador",
    icon: "bi-shield-lock-fill",
    color: "var(--role-admin)",
    soft: "var(--role-admin-soft)",
  },
};

export function getRoleMeta(role) {
  return (
    ROLE_META[role] ?? {
      label: role ?? "Usuario",
      icon: "bi-person-fill",
      color: "var(--campus-muted)",
      soft: "var(--campus-surface-2)",
    }
  );
}
