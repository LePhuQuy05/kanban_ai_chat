"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { createInitialBoardData, type BoardData } from "@/lib/kanban";
import { fetchBoard, updateBoard } from "@/lib/boardApi";

const USERNAME = "user";
const PASSWORD = "password";

export default function Home() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [board, setBoard] = useState<BoardData>(() => createInitialBoardData());
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
    setIsLoadingBoard(false);
    setIsSavingBoard(false);
    setBoard(createInitialBoardData());
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
      <KanbanBoard board={board} onBoardChange={handleBoardChange} />
    </>
  );
}
