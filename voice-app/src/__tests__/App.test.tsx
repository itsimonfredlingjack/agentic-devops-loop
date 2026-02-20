import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { usePipelineStore } from "../stores/pipelineStore";

// Mock the WebSocket module to prevent actual connections during render
vi.mock("../lib/ws", () => ({
  connectWebSocket: vi.fn(),
  disconnectWebSocket: vi.fn(),
}));

// Mock useMicLevel to avoid Tauri API calls
vi.mock("../hooks/useMicLevel", () => ({
  useMicLevel: () => [],
}));

// Mock @tauri-apps/api/core invoke
vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(),
}));

describe("App", () => {
  beforeEach(() => {
    // Reset store to known state before each test
    usePipelineStore.setState({
      status: "idle",
      transcription: "",
      log: [],
      serverUrl: "http://localhost:8000",
      clarification: null,
      loopEvents: [],
      toasts: [],
      processingStep: "",
      pendingSamples: null,
      ticketResult: null,
      wsConnected: false,
    });
  });

  it("should render the app header", async () => {
    // Dynamic import to ensure mocks are in place
    const { default: App } = await import("../App");
    render(<App />);
    expect(screen.getByText("Agentic DevOps Voice")).toBeInTheDocument();
  });

  it("should render the record button in idle state", async () => {
    const { default: App } = await import("../App");
    render(<App />);
    expect(
      screen.getByRole("button", { name: "Start recording" }),
    ).toBeInTheDocument();
  });

  it("should render the transcription card", async () => {
    const { default: App } = await import("../App");
    render(<App />);
    expect(screen.getByText("Transcription")).toBeInTheDocument();
  });

  it("should show idle hint", async () => {
    const { default: App } = await import("../App");
    render(<App />);
    expect(screen.getByText("Press Space to record")).toBeInTheDocument();
  });

  it("should render settings button", async () => {
    const { default: App } = await import("../App");
    render(<App />);
    expect(
      screen.getByRole("button", { name: "Settings" }),
    ).toBeInTheDocument();
  });

  it("should render pipeline log", async () => {
    const { default: App } = await import("../App");
    render(<App />);
    expect(
      screen.getByRole("button", { name: /Pipeline Log/i }),
    ).toBeInTheDocument();
  });

  it("should show transcription text when store has transcription", async () => {
    usePipelineStore.setState({ transcription: "Hello from voice" });
    const { default: App } = await import("../App");
    render(<App />);
    expect(screen.getByText("Hello from voice")).toBeInTheDocument();
  });

  it("should render success card when status is done with ticket result", async () => {
    usePipelineStore.setState({
      status: "done",
      ticketResult: {
        key: "DEV-99",
        url: "https://jira.example.com/DEV-99",
        summary: "Test ticket",
      },
    });
    const { default: App } = await import("../App");
    render(<App />);
    expect(screen.getByText("Ticket Created")).toBeInTheDocument();
    expect(screen.getByText("DEV-99")).toBeInTheDocument();
  });
});
