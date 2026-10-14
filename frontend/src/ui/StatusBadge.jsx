import Badge from "./Badge.jsx";

export default function StatusBadge({
  active,
  activeLabel = "Activo",
  inactiveLabel = "Inactivo",
}) {
  if (active) {
    return (
      <Badge tone="success" icon="check-circle-fill">
        {activeLabel}
      </Badge>
    );
  }
  return (
    <Badge tone="warning" icon="pause-circle-fill">
      {inactiveLabel}
    </Badge>
  );
}
