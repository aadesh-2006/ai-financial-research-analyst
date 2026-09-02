import "@testing-library/jest-dom";

// Mock ResizeObserver for Recharts responsive containers in jsdom environment
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};