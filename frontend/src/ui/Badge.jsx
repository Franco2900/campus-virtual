const TONES = {
  neutral: { color: "var(--campus-muted)", background: "var(--campus-surface-2)" },
  success: { color: "var(--campus-success)", background: "var(--campus-success-soft)" },
  warning: { color: "var(--campus-warning)", background: "var(--campus-warning-soft)" },
  danger: { color: "var(--campus-danger)", background: "var(--campus-danger-soft)" },
  brand: { color: "var(--campus-brand)", background: "var(--campus-brand-soft)" },
};

export default function Badge({ tone = "neutral", icon, children, className = "" }) {
  const style = TONES[tone] ?? TONES.neutral;
  return (
    <span className={`role-chip ${className}`.trim()} style={style}>
      {icon && <i className={`bi bi-${icon}`} aria-hidden="true" />}
      {children}
    </span>
  );
}
