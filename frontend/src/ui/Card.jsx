export default function Card({ flat = false, className = "", children, ...props }) {
  const flatClass = flat ? "campus-card--flat" : "";
  return (
    <div className={`campus-card ${flatClass} ${className}`.trim()} {...props}>
      {children}
    </div>
  );
}
