"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { createInitialBoardData, type BoardData } from "@/lib/kanban";
import { sendAIChat, type ChatMessage } from "@/lib/aiChatApi";
import { fetchBoard, updateBoard } from "@/lib/boardApi";

const USERNAME = "user";
const PASSWORD = "password";

export default function Home() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [board, setBoard] = useState<BoardData>(() => createInitialBoardData());
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Ask me to create, move, or update cards and I can apply changes for you.",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [chatError, setChatError] = useState("");
  const [isLoadingBoard, setIsLoadingBoard] = useState(false);
  const [isSavingBoard, setIsSavingBoard] = useState(false);
  const [boardError, setBoardError] = useState("");
  const latestSaveRequestId = useRef(0);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    let isCancelled = false;
    const loadBoard = async () => {
      setIsLoadingBoard(true);
      setBoardError("");
      try {
        const loadedBoard = await fetchBoard();
        if (!isCancelled) {
          setBoard(loadedBoard);
        }
      } catch (loadError) {
        if (!isCancelled) {
          setBoardError(
            loadError instanceof Error ? loadError.message : "Unable to load board."
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoadingBoard(false);
        }
      }
    };

    void loadBoard();

    return () => {
      isCancelled = true;
    };
  }, [isAuthenticated]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (username === USERNAME && password === PASSWORD) {
      setIsAuthenticated(true);
      setError("");
      return;
    }
    setError("Invalid credentials");
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUsername("");
    setPassword("");
    setError("");
    setBoardError("");
    setChatError("");
    setChatInput("");
    setChatMessages([
      {
        role: "assistant",
        content: "Ask me to create, move, or update cards and I can apply changes for you.",
      },
    ]);
    setIsSendingChat(false);
    setIsLoadingBoard(false);
    setIsSavingBoard(false);
    setBoard(createInitialBoardData());
  };

  const handleChatSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!chatInput.trim() || isSendingChat) {
      return;
    }

    const userMessage = chatInput.trim();
    const nextConversation = [...chatMessages, { role: "user" as const, content: userMessage }];
    setChatMessages(nextConversation);
    setChatInput("");
    setChatError("");
    setIsSendingChat(true);

    try {
      const response = await sendAIChat(chatMessages, board, userMessage);
      setChatMessages((previous) => [
        ...previous,
        { role: "assistant", content: response.reply },
      ]);
      if (response.mutationApplied && response.board) {
        latestSaveRequestId.current += 1;
        setIsSavingBoard(false);
        setBoard(response.board);
      }
    } catch (sendError) {
      setChatError(sendError instanceof Error ? sendError.message : "Unable to send chat.");
    } finally {
      setIsSendingChat(false);
    }
  };

  const handleBoardChange = (
    nextBoard: BoardData | ((previous: BoardData) => BoardData)
  ) => {
    setBoard((previous) => {
      const resolvedBoard =
        typeof nextBoard === "function" ? nextBoard(previous) : nextBoard;

      setIsSavingBoard(true);
      setBoardError("");
      const requestId = latestSaveRequestId.current + 1;
      latestSaveRequestId.current = requestId;
      void updateBoard(resolvedBoard)
        .then(() => undefined)
        .catch((saveError) => {
          if (requestId === latestSaveRequestId.current) {
            setBoardError(
              saveError instanceof Error ? saveError.message : "Unable to save board."
            );
          }
        })
        .finally(() => {
          if (requestId === latestSaveRequestId.current) {
            setIsSavingBoard(false);
          }
        });

      return resolvedBoard;
    });
  };

  if (!isAuthenticated) {
    return (
      <main className="mx-auto flex min-h-screen max-w-lg items-center px-6">
        <section className="w-full rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <h1 className="font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Sign in
          </h1>
          <p className="mt-3 text-sm text-[var(--gray-text)]">
            Use the demo credentials to access your board.
          </p>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block text-sm font-semibold text-[var(--navy-dark)]">
              Username
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] px-3 py-2 outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="username"
              />
            </label>
            <label className="block text-sm font-semibold text-[var(--navy-dark)]">
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] px-3 py-2 outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="current-password"
              />
            </label>
            {error ? (
              <p role="alert" className="text-sm font-semibold text-red-600">
                {error}
              </p>
            ) : null}
            <button
              type="submit"
              className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
            >
              Sign in
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <>
      <div className="mx-auto w-full max-w-[1500px] px-6 pt-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="min-h-6">
            {isLoadingBoard ? (
              <p className="text-sm font-semibold text-[var(--gray-text)]">Loading board...</p>
            ) : null}
            {!isLoadingBoard && isSavingBoard ? (
              <p className="text-sm font-semibold text-[var(--gray-text)]">Saving changes...</p>
            ) : null}
            {boardError ? (
              <p role="alert" className="text-sm font-semibold text-red-600">
                {boardError}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--navy-dark)] transition hover:bg-[var(--surface)]"
          >
            Log out
          </button>
        </div>
      </div>
      <div className="mx-auto flex w-full max-w-[1920px] flex-col gap-6 px-6 pb-8 xl:flex-row xl:items-start">
        <div className="min-w-0 flex-1">
          <KanbanBoard board={board} onBoardChange={handleBoardChange} />
        </div>
        <aside className="w-full rounded-3xl border border-[var(--stroke)] bg-white p-5 shadow-[var(--shadow)] xl:sticky xl:top-6 xl:w-[360px]">
          <h2 className="font-display text-2xl font-semibold text-[var(--navy-dark)]">
            AI Assistant
          </h2>
          <p className="mt-2 text-sm text-[var(--gray-text)]">
            Describe board updates in natural language.
          </p>
          <div
            className="mt-4 flex max-h-[360px] flex-col gap-3 overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-3"
            data-testid="chat-thread"
          >
            {chatMessages.map((message, index) => (
              <article
                key={`${message.role}-${index}`}
                className={
                  message.role === "user"
                    ? "ml-8 rounded-2xl bg-[var(--primary-blue)] px-3 py-2 text-sm text-white"
                    : "mr-8 rounded-2xl bg-white px-3 py-2 text-sm text-[var(--navy-dark)]"
                }
              >
                {message.content}
              </article>
            ))}
          </div>
          <form className="mt-4 space-y-3" onSubmit={handleChatSubmit}>
            <label className="block text-sm font-semibold text-[var(--navy-dark)]">
              Message
              <textarea
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                rows={3}
                className="mt-2 w-full resize-none rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                placeholder="Move card 1 to Review and rename Discovery to Planning."
              />
            </label>
            {chatError ? (
              <p role="alert" className="text-sm font-semibold text-red-600">
                {chatError}
              </p>
            ) : null}
            <button
              type="submit"
              disabled={isSendingChat || !chatInput.trim()}
              className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold uppercase tracking-wide text-white transition enabled:hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSendingChat ? "Sending..." : "Send"}
            </button>
          </form>
        </aside>
      </div>
    </>
  );
}
