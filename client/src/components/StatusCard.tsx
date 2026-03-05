import { type ReactElement } from "react";

type StatusCardProps = {
  label: string;
  value: string;
  tone?: "default" | "success" | "error";
};

function StatusCard({ label, value, tone = "default" }: StatusCardProps): ReactElement {
  return (
    <div className={`status-card tone-${tone}`}>
      <p className="status-label">{label}</p>
      <p className="status-value">{value}</p>
    </div>
  );
}

export default StatusCard;
