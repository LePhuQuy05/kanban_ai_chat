import { createInitialBoardData } from "@/lib/kanban";
import { fetchBoard, updateBoard } from "@/lib/boardApi";

describe("boardApi", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetchBoard sends auth headers and returns board payload", async () => {
    const board = createInitialBoardData();
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(board), { status: 200 })
    );

    const result = await fetchBoard();

    expect(fetch).toHaveBeenCalledWith("/api/board", {
      method: "GET",
      headers: {
        "X-Username": "user",
        "X-Password": "password",
      },
    });
    expect(result.columns).toHaveLength(board.columns.length);
  });

  it("updateBoard sends payload and returns saved board", async () => {
    const board = createInitialBoardData();
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(board), { status: 200 })
    );

    const result = await updateBoard(board);

    expect(fetch).toHaveBeenCalledWith("/api/board", {
      method: "PUT",
      headers: {
        "X-Username": "user",
        "X-Password": "password",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(board),
    });
    expect(result.cards["card-1"]?.title).toBe(board.cards["card-1"]?.title);
  });

  it("surfaces backend detail for failed requests", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Invalid credentials." }), { status: 401 })
    );

    await expect(fetchBoard()).rejects.toThrow("Invalid credentials.");
  });
});
