import { Link } from "react-router-dom";

import Card from "./Card.jsx";

export default function StatCard({
  icon,
  value,
  label,
  detail,
  color = "var(--campus-brand)",
  soft = "var(--campus-brand-soft)",
  to,
  testId,
}) {
  const details = detail ? (Array.isArray(detail) ? detail : [detail]) : [];

  const body = (
    <>
      <span className="campus-stat__icon" style={{ color, background: soft }} aria-hidden="true">
        <i className={`bi ${icon}`} />
      </span>
      <div>
        <div className="campus-stat__value">{value}</div>
        <div className="campus-stat__label">{label}</div>
        {details.map((line) => (
          <div className="campus-stat__detail" key={line}>
            {line}
          </div>
        ))}
      </div>
    </>
  );

  if (!to) {
    return (
      <Card className="campus-stat h-100" data-testid={testId}>
        {body}
      </Card>
    );
  }

  return (
    <Link to={to} className="campus-stat-link" data-testid={testId}>
      <Card className="campus-stat h-100">{body}</Card>
    </Link>
  );
}
