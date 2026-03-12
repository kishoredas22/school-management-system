const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const dateFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

export function formatCurrency(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return currencyFormatter.format(0);
  }
  return currencyFormatter.format(Number(value));
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "Not set";
  }
  return dateFormatter.format(new Date(value));
}

export function formatEnumLabel(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function fullName(firstName: string, lastName?: string | null): string {
  return `${firstName} ${lastName || ""}`.trim();
}

export function monthOptions() {
  return Array.from({ length: 12 }, (_, index) => {
    const month = index + 1;
    return {
      value: month,
      label: new Intl.DateTimeFormat("en", { month: "long" }).format(new Date(2026, index, 1)),
    };
  });
}
