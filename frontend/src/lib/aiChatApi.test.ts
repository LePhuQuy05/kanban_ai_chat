import { createInitialBoardData } from "@/lib/kanban";
import { sendAIChat, type ChatMessage } from "@/lib/aiChatApi";

describe("aiChatApi", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends conversation, board, and user message", async () => {
    const board = createInitialBoardData();
    const conversation: ChatMessage[] = [{ role: "assistant", content: "How can I help?" }];
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          reply: "Done.",
          mutationApplied: false,
          board: null,
        }),
        { status: 200 }
      )
    );

    const response = await sendAIChat(conversation, board, "Move one task.");

    expect(fetch).toHaveBeenCalledWith("/api/ai/chat", {
      method: "POST",
      headers: {
        "X-Username": "user",
        "X-Password": "password",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        conversation,
        board,
        userMessage: "Move one task.",
      }),
    });
    expect(response.reply).toBe("Done.");
  });

  it("throws API detail when chat request fails", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "OpenRouter request failed." }), { status: 502 })
    );

    await expect(
      sendAIChat([], createInitialBoardData(), "hello")
    ).rejects.toThrow("OpenRouter request failed.");
  });
});
