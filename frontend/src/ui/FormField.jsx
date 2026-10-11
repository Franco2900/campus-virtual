export default function FormField({ id, label, type = "text", hint, children, ...props }) {
  let control = null;
  if (children) {
    control = children;
  } else if (type === "textarea") {
    control = <textarea id={id} className="form-control" {...props} />;
  } else {
    control = <input id={id} type={type} className="form-control" {...props} />;
  }

  return (
    <div className="mb-3">
      <label htmlFor={id} className="form-label fw-semibold">
        {label}
      </label>
      {control}
      {hint && <div className="form-text">{hint}</div>}
    </div>
  );
}
