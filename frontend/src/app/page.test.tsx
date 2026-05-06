import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "@/app/page";
import { createInitialBoardData, type BoardData } from "@/lib/kanban";

const deferredResponse = () => {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((resolver) => {
    resolve = resolver;
  });
  return { promise, resolve };
};

const login = async () => {
  await userEvent.type(screen.getByLabelText(/username/i), "user");
  await userEvent.type(screen.getByLabelText(/password/i), "password");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
};

describe("Home auth gate", () => {
  let serverBoard: BoardData;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    serverBoard = createInitialBoardData();
    fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (!url.endsWith("/api/board")) {
        return new Response(JSON.stringify({ detail: "Not found" }), { status: 404 });
      }

      if ((init?.method ?? "GET").toUpperCase() === "GET") {
        return new Response(JSON.stringify(serverBoard), { status: 200 });
      }

      const payload = JSON.parse((init?.body as string) ?? "{}") as BoardData;
      serverBoard = payload;
      return new Response(JSON.stringify(serverBoard), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows login form first and hides board", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: /kanban studio/i })
    ).not.toBeInTheDocument();
  });

  it("rejects invalid credentials", async () => {
    render(<Home />);
    await userEvent.type(screen.getByLabelText(/username/i), "wrong");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/invalid credentials/i);
  });

  it("signs in and allows logout", async () => {
    render(<Home />);
    await login();

    expect(screen.getByRole("heading", { name: /kanban studio/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
  });

  it("loads the board from API after login", async () => {
    serverBoard = {
      ...serverBoard,
      columns: serverBoard.columns.map((column) =>
        column.id === "col-progress" ? { ...column, title: "Done" } : column
      ),
    };

    render(<Home />);
    await login();

    expect(
      within(screen.getByTestId("column-col-progress")).getByLabelText("Column title")
    ).toHaveValue("Done");
  });

  it("writes board changes through the board API", async () => {
    render(<Home />);
    await login();

    const backlogColumn = screen.getByTestId("column-col-backlog");
    await userEvent.click(
      within(backlogColumn).getByRole("button", { name: /add a card/i })
    );
    await userEvent.type(
      within(backlogColumn).getByPlaceholderText(/card title/i),
      "Test Card"
    );
    await userEvent.type(
      within(backlogColumn).getByPlaceholderText(/details/i),
      "Persists to backend"
    );
    await userEvent.click(
      within(backlogColumn).getByRole("button", { name: /add card/i })
    );

    expect(serverBoard.columns[0]?.cardIds).toHaveLength(3);
    expect(Object.values(serverBoard.cards ?? {})).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Test Card",
          details: "Persists to backend",
        }),
      ])
    );
  });

  it("keeps board changes after logout and next login", async () => {
    render(<Home />);
    await login();

    const backlogColumn = screen.getByTestId("column-col-backlog");
    await userEvent.click(
      within(backlogColumn).getByRole("button", { name: /add a card/i })
    );
    await userEvent.type(
      within(backlogColumn).getByPlaceholderText(/card title/i),
      "Saved card"
    );
    await userEvent.type(
      within(backlogColumn).getByPlaceholderText(/details/i),
      "Persists in backend"
    );
    await userEvent.click(
      within(backlogColumn).getByRole("button", { name: /add card/i })
    );

    expect(within(backlogColumn).getByText("Saved card")).toBeInTheDocument();

    const progressColumn = screen.getByTestId("column-col-progress");
    const progressTitle = within(progressColumn).getByLabelText("Column title");
    await userEvent.clear(progressTitle);
    await userEvent.type(progressTitle, "Done");

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    await login();

    expect(screen.getByTestId("column-col-backlog")).toHaveTextContent("Saved card");
    expect(
      within(screen.getByTestId("column-col-progress")).getByLabelText("Column title")
    ).toHaveValue("Done");
  });

  it("shows load error when board fetch fails", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Load failed." }), { status: 500 })
    );

    render(<Home />);
    await login();

    expect(await screen.findByRole("alert")).toHaveTextContent(/load failed/i);
  });

  it("shows save status and handles save errors", async () => {
    fetchMock.mockImplementationOnce(
      async () => new Response(JSON.stringify(serverBoard), { status: 200 })
    );
    fetchMock.mockImplementationOnce(
      async () => new Response(JSON.stringify({ detail: "Save failed." }), { status: 500 })
    );

    render(<Home />);
    await login();

    const backlogColumn = screen.getByTestId("column-col-backlog");
    await userEvent.click(within(backlogColumn).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(backlogColumn).getByPlaceholderText(/card title/i), "Failure Card");
    await userEvent.click(within(backlogColumn).getByRole("button", { name: /add card/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/save failed/i);
  });

  it("keeps the latest board state when save responses return out of order", async () => {
    const firstSave = deferredResponse();
    const secondSave = deferredResponse();
    let saveCount = 0;

    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (!url.endsWith("/api/board")) {
        return new Response(JSON.stringify({ detail: "Not found" }), { status: 404 });
      }

      if ((init?.method ?? "GET").toUpperCase() === "GET") {
        return new Response(JSON.stringify(serverBoard), { status: 200 });
      }

      const payload = JSON.parse((init?.body as string) ?? "{}") as BoardData;
      saveCount += 1;
      if (saveCount === 1) {
        return firstSave.promise;
      }
      if (saveCount === 2) {
        return secondSave.promise;
      }
      return new Response(JSON.stringify(payload), { status: 200 });
    });

    render(<Home />);
    await login();

    const backlogColumn = screen.getByTestId("column-col-backlog");
    const discoveryColumn = screen.getByTestId("column-col-discovery");
    const discoveryTitle = within(discoveryColumn).getByLabelText("Column title");

    await userEvent.click(
      within(backlogColumn).getByRole("button", { name: /add a card/i })
    );
    await userEvent.type(
      within(backlogColumn).getByPlaceholderText(/card title/i),
      "First Save Card"
    );
    await userEvent.click(
      within(backlogColumn).getByRole("button", { name: /add card/i })
    );

    await userEvent.clear(discoveryTitle);
    await userEvent.type(discoveryTitle, "Second Save Title");

    secondSave.resolve(
      new Response(
        JSON.stringify({
          ...serverBoard,
          columns: serverBoard.columns.map((column) =>
            column.id === "col-discovery"
              ? { ...column, title: "Second Save Title" }
              : column
          ),
        }),
        { status: 200 }
      )
    );
    firstSave.resolve(new Response(JSON.stringify(serverBoard), { status: 200 }));

    expect(await screen.findByDisplayValue("Second Save Title")).toBeInTheDocument();
  });
});
