import type { BoardData } from "@/lib/kanban";

const AUTH_HEADERS = {
  "X-Username": "user",
  "X-Password": "password",
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AIChatResponse = {
  reply: string;
  mutationApplied: boolean;
  board: BoardData | null;
};

const parseErrorMessage = async (response: Response): Promise<string> => {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }
  } catch {
    // Fallback for non-JSON error bodies.
  }
  return `Request failed with status ${response.status}.`;
};

export const sendAIChat = async (
  conversation: ChatMessage[],
  board: BoardData,
  userMessage: string
): Promise<AIChatResponse> => {
  const response = await fetch("/api/ai/chat", {
    method: "POST",
    headers: {
      ...AUTH_HEADERS,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      conversation,
      board,
      userMessage,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return (await response.json()) as AIChatResponse;
};
