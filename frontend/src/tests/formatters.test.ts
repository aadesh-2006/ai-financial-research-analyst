import { describe, it, expect } from "vitest";
import {
  formatCurrency,
  formatDate,
  formatMultiple,
  formatNumber,
  formatPercent,
  formatRawPercent,
} from "../utils/formatters";

describe("Financial Presentation Formatters", () => {
  describe("formatCurrency", () => {
    it("formats trillions, billions, and millions in compact mode", () => {
      expect(formatCurrency(3_300_000_000_000, "USD", true)).toBe("$3.30T");
      expect(formatCurrency(105_000_000_000, "USD", true)).toBe("$105.00B");
      expect(formatCurrency(25_400_000, "USD", true)).toBe("$25.40M");
    });

    it("formats standard prices cleanly", () => {
      expect(formatCurrency(95.01, "USD", true)).toBe("$95.01");
      expect(formatCurrency(220, "USD", false)).toBe("$220.00");
    });

    it("handles negative values with clean minus sign", () => {
      expect(formatCurrency(-25_400_000, "USD", true)).toBe("-$25.40M");
      expect(formatCurrency(-12.5, "USD", false)).toBe("-$12.50");
    });

    it("safely handles null, undefined, and NaN", () => {
      expect(formatCurrency(null)).toBe("—");
      expect(formatCurrency(undefined)).toBe("—");
      expect(formatCurrency(NaN)).toBe("—");
    });
  });

  describe("formatPercent", () => {
    it("converts decimal ratios to percentage strings", () => {
      expect(formatPercent(0.08, 1)).toBe("8.0%");
      expect(formatPercent(0.312, 1)).toBe("31.2%");
      expect(formatPercent(-0.043, 1)).toBe("-4.3%");
    });

    it("includes plus sign when showSign is true", () => {
      expect(formatPercent(0.08, 1, true)).toBe("+8.0%");
      expect(formatPercent(-0.043, 1, true)).toBe("-4.3%");
    });

    it("safely handles null and undefined", () => {
      expect(formatPercent(null)).toBe("—");
      expect(formatPercent(undefined)).toBe("—");
    });
  });

  describe("formatRawPercent", () => {
    it("formats numbers already on a 0-100 scale", () => {
      expect(formatRawPercent(8.5, 1)).toBe("8.5%");
      expect(formatRawPercent(8.5, 1, true)).toBe("+8.5%");
      expect(formatRawPercent(-4.3, 1)).toBe("-4.3%");
    });
  });

  describe("formatMultiple", () => {
    it("formats valuation multiples with default 2 decimals and suffix", () => {
      expect(formatMultiple(32.5)).toBe("32.50x");
      expect(formatMultiple(1.75, "x")).toBe("1.75x");
    });

    it("returns N/A for null and undefined", () => {
      expect(formatMultiple(null)).toBe("N/A");
      expect(formatMultiple(undefined)).toBe("N/A");
    });
  });

  describe("formatDate", () => {
    it("formats ISO timestamps into readable dates", () => {
      const formatted = formatDate("2026-09-01T12:00:00Z");
      expect(formatted).toContain("2026");
    });

    it("returns dash for null or undefined", () => {
      expect(formatDate(null)).toBe("—");
      expect(formatDate(undefined)).toBe("—");
    });
  });

  describe("formatNumber", () => {
    it("formats numbers with comma separators", () => {
      expect(formatNumber(15_000_000_000)).toBe("15,000,000,000");
    });

    it("returns dash for null", () => {
      expect(formatNumber(null)).toBe("—");
    });
  });
});