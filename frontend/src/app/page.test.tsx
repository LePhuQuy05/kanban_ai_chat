import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "@/app/page";
import {
  BOARD_STORAGE_KEY,
  createInitialBoardData,
  parseBoardData,
  type BoardData,
} from "@/lib/kanban";

const login = async () => {
  await userEvent.type(screen.getByLabelText(/username/i), "user");
  await userEvent.type(screen.getByLabelText(/password/i), "password");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
};

describe("Home auth gate", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  const saveBoard = (update: (board: BoardData) => BoardData) => {
    const board = update(createInitialBoardData());
    window.localStorage.setItem(BOARD_STORAGE_KEY, JSON.stringify(board));
    return board;
  };

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

  it("loads the saved board from localStorage after login", async () => {
    saveBoard((board) => ({
      ...board,
      columns: board.columns.map((column) =>
        column.id === "col-progress" ? { ...column, title: "Done" } : column
      ),
    }));

    render(<Home />);
    await login();

    expect(
      within(screen.getByTestId("column-col-progress")).getByLabelText("Column title")
    ).toHaveValue("Done");
  });

  it("writes board changes to localStorage", async () => {
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
      "Persists to storage"
    );
    await userEvent.click(
      within(backlogColumn).getByRole("button", { name: /add card/i })
    );

    const storedBoard = parseBoardData(window.localStorage.getItem(BOARD_STORAGE_KEY));
    expect(storedBoard?.columns[0]?.cardIds).toHaveLength(3);
    expect(Object.values(storedBoard?.cards ?? {})).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Test Card",
          details: "Persists to storage",
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
    await userEvent.type(within(backlogColumn).getByPlaceholderText(/card title/i), "Saved card");
    await userEvent.type(within(backlogColumn).getByPlaceholderText(/details/i), "Persists locally");
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
});
