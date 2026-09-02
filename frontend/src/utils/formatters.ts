/**
 * Safe, null-aware financial presentation formatters.
 * Never outputs NaN, undefined, or [object Object].
 */

export function formatCurrency(
  val: number | null | undefined,
  currency: string = "USD",
  compact: boolean = true
): string {
  if (val === null || val === undefined || isNaN(val)) {
    return "—";
  }

  const symbol = currency === "USD" ? "$" : `${currency} `;
  const isNegative = val < 0;
  const absVal = Math.abs(val);

  if (compact) {
    if (absVal >= 1e12) {
      return `${isNegative ? "-" : ""}${symbol}${(absVal / 1e12).toFixed(2)}T`;
    }
    if (absVal >= 1e9) {
      return `${isNegative ? "-" : ""}${symbol}${(absVal / 1e9).toFixed(2)}B`;
    }
    if (absVal >= 1e6) {
      return `${isNegative ? "-" : ""}${symbol}${(absVal / 1e6).toFixed(2)}M`;
    }
  }

  return `${isNegative ? "-" : ""}${symbol}${absVal.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatPercent(
  val: number | null | undefined,
  decimals: number = 1,
  showSign: boolean = false
): string {
  if (val === null || val === undefined || isNaN(val)) {
    return "—";
  }

  const pct = val * 100;
  const formatted = pct.toFixed(decimals);
  if (showSign && pct > 0) {
    return `+${formatted}%`;
  }
  return `${formatted}%`;
}

export function formatRawPercent(
  val: number | null | undefined,
  decimals: number = 1,
  showSign: boolean = false
): string {
  if (val === null || val === undefined || isNaN(val)) {
    return "—";
  }

  const formatted = val.toFixed(decimals);
  if (showSign && val > 0) {
    return `+${formatted}%`;
  }
  return `${formatted}%`;
}

export function formatMultiple(
  val: number | null | undefined,
  suffix: string = "x"
): string {
  if (val === null || val === undefined || isNaN(val)) {
    return "N/A";
  }
  return `${val.toFixed(2)}${suffix}`;
}

export function formatDate(val: string | null | undefined): string {
  if (!val) return "—";
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return val;
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return val;
  }
}

export function formatNumber(
  val: number | null | undefined,
  decimals: number = 0
): string {
  if (val === null || val === undefined || isNaN(val)) {
    return "—";
  }
  return val.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}