import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TickerSearch } from "../components/dashboard/TickerSearch";

describe("TickerSearch Component", () => {
  it("renders search input, submit button, and quick-benchmark pills", () => {
    render(<TickerSearch onSearch={vi.fn()} isLoading={false} />);
    expect(screen.getByPlaceholderText(/Enter public stock ticker/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Analyze Company/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /AAPL/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /JPM/i })).toBeInTheDocument();
  });

  it("normalizes lowercase ticker to uppercase and calls onSearch", () => {
    const handleSearch = vi.fn();
    render(<TickerSearch onSearch={handleSearch} isLoading={false} />);

    const input = screen.getByPlaceholderText(/Enter public stock ticker/i);
    fireEvent.change(input, { target: { value: "aapl" } });
    fireEvent.submit(screen.getByRole("button", { name: /Analyze Company/i }));

    expect(handleSearch).toHaveBeenCalledWith("AAPL");
  });

  it("does not call onSearch when input is empty or whitespace", () => {
    const handleSearch = vi.fn();
    render(<TickerSearch onSearch={handleSearch} isLoading={false} />);

    const input = screen.getByPlaceholderText(/Enter public stock ticker/i);
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.submit(screen.getByRole("button", { name: /Analyze Company/i }));

    expect(handleSearch).not.toHaveBeenCalled();
  });

  it("triggers onSearch when quick benchmark pill is clicked", () => {
    const handleSearch = vi.fn();
    render(<TickerSearch onSearch={handleSearch} isLoading={false} />);

    const jpmButton = screen.getByRole("button", { name: /JPM/i });
    fireEvent.click(jpmButton);

    expect(handleSearch).toHaveBeenCalledWith("JPM");
  });

  it("disables input and shows loading state while analyzing", () => {
    render(<TickerSearch onSearch={vi.fn()} isLoading={true} />);
    expect(screen.getByPlaceholderText(/Enter public stock ticker/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: /Analyzing/i })).toBeDisabled();
  });
});