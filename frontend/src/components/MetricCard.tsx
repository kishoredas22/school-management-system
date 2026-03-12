export function MetricCard({
  label,
  value,
  detail,
  tone = "sand",
}: {
  label: string;
  value: string;
  detail: string;
  tone?: "sand" | "mint" | "ink" | "coral";
}) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}
