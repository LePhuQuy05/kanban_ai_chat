import { expect, test, type Page } from "@playwright/test";

const login = async (page: Page) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
};

test("loads the kanban board", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await login(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("requires auth and supports logout", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /kanban studio/i })).toHaveCount(0);

  await login(page);
  await expect(page.getByRole("button", { name: /log out/i })).toBeVisible();
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
});

test("keeps board changes after logout and next login", async ({ page }) => {
  await login(page);
  const backlogColumn = page.locator('[data-testid="column-col-backlog"]');
  await backlogColumn.getByRole("button", { name: /add a card/i }).click();
  await backlogColumn.getByPlaceholder("Card title").fill("Test Card");
  await backlogColumn.getByPlaceholder("Details").fill("Should still be here after login.");
  await backlogColumn.getByRole("button", { name: /add card/i }).click();
  await expect(backlogColumn.getByText("Test Card")).toBeVisible();

  const secondColumn = page.locator('[data-testid="column-col-discovery"]');
  const card = backlogColumn
    .locator('[data-testid^="card-"]')
    .filter({ hasText: "Test Card" })
    .first();
  const cardBox = await card.boundingBox();
  const secondColumnBox = await secondColumn.boundingBox();
  if (!cardBox || !secondColumnBox) {
    throw new Error("Unable to resolve drag coordinates for persistence test.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    secondColumnBox.x + secondColumnBox.width / 2,
    secondColumnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(secondColumn.getByText("Test Card")).toBeVisible();

  const thirdColumnTitle = page
    .locator('[data-testid="column-col-progress"]')
    .getByLabel("Column title");
  await thirdColumnTitle.fill("Done");
  await expect(thirdColumnTitle).toHaveValue("Done");

  await page.getByRole("button", { name: /log out/i }).click();
  await login(page);

  await expect(page.locator('[data-testid="column-col-discovery"]')).toContainText(
    "Test Card"
  );
  await expect(
    page.locator('[data-testid="column-col-progress"]').getByLabel("Column title")
  ).toHaveValue("Done");
});
