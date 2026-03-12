import { SCHOOL_NAME, SCHOOL_NAME_LOCAL } from "../branding";
import schoolLogo from "../assets/vsk-logo.webp";

export function SchoolBrand({
  compact = false,
  inverted = false,
  stacked = false,
  eyebrow,
  subtitle,
}: {
  compact?: boolean;
  inverted?: boolean;
  stacked?: boolean;
  eyebrow?: string;
  subtitle?: string;
}) {
  const className = ["school-brand", compact ? "is-compact" : "", inverted ? "is-inverted" : "", stacked ? "is-stacked" : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className}>
      <div className="school-brand-mark-shell">
        <img className="school-brand-mark" src={schoolLogo} alt={`${SCHOOL_NAME} logo`} />
      </div>
      <div className="school-brand-copy">
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{SCHOOL_NAME}</h1>
        <p className="school-brand-local">{SCHOOL_NAME_LOCAL}</p>
        {subtitle ? <p className="school-brand-meta">{subtitle}</p> : null}
      </div>
    </div>
  );
}
