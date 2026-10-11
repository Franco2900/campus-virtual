const BRAND = "brand";
const SOFT = "soft";

export default function Button({ variant = BRAND, icon, className = "", children, ...props }) {
  let variantClass = `btn-${variant}`;
  if (variant === BRAND) {
    variantClass = "btn-brand";
  } else if (variant === SOFT) {
    variantClass = "btn-soft";
  }

  return (
    <button
      type="button"
      className={`btn ${variantClass} d-inline-flex align-items-center justify-content-center gap-2 ${className}`.trim()}
      {...props}
    >
      {icon && <i className={`bi bi-${icon}`} aria-hidden="true" />}
      {children}
    </button>
  );
}
