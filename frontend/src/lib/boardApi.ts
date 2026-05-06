import type { BoardData } from "@/lib/kanban";

const AUTH_HEADERS = {
  "X-Username": "user",
  "X-Password": "password",
};

const parseErrorMessage = async (response: Response): Promise<string> => {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }
  } catch {
    // Keep fallback message when response body is not JSON.
  }
  return `Request failed with status ${response.status}.`;
};

export const fetchBoard = async (): Promise<BoardData> => {
  const response = await fetch("/api/board", {
    method: "GET",
    headers: AUTH_HEADERS,
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return (await response.json()) as BoardData;
};

export const updateBoard = async (board: BoardData): Promise<BoardData> => {
  const response = await fetch("/api/board", {
    method: "PUT",
    headers: {
      ...AUTH_HEADERS,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(board),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return (await response.json()) as BoardData;
};
