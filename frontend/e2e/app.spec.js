import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const profile = {
  id: "a9f35a3f-7dc6-45aa-8e62-eaf59fa247b9",
  email: "user@example.com",
  displayName: "Test User",
  avatarUrl: null,
};

async function expectNoAccessibilityViolations(page) {
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
}

test("redirects unauthenticated users to the login screen", async ({ page }) => {
  await page.route("**/api/auth/me", (route) => route.fulfill({ status: 401 }));
  await page.goto("/");

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("button", { name: "Sign in with Google" })).toBeVisible();
  await expectNoAccessibilityViolations(page);
});

test("renders a fallback page for unknown routes", async ({ page }) => {
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(profile),
    }),
  );
  await page.goto("/missing");

  await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
  await expectNoAccessibilityViolations(page);
});

test("streams an authenticated answer", async ({ page }) => {
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(profile),
    }),
  );
  await page.route("**/api/conversations", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ conversations: [] }),
      });
    }
    return route.continue();
  });
  await page.route("**/api/chat/stream", (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: [
        'data: {"type":"start","conversation_id":"conversation-1"}',
        "",
        'data: {"type":"sources","sources":[]}',
        "",
        'data: {"type":"token","token":"Maintain an accurate asset inventory."}',
        "",
        'data: {"type":"done","message_id":"message-1"}',
        "",
      ].join("\n"),
    }),
  );

  await page.goto("/");
  await expect(page.getByRole("dialog", { name: "Welcome" })).toBeVisible();
  await page.getByRole("button", { name: "Skip tour" }).click();
  await page
    .getByRole("button", {
      name: "What are the first steps to establish an asset inventory?",
    })
    .click();

  await expect(page.getByText("Maintain an accurate asset inventory.")).toBeVisible();
  await expectNoAccessibilityViolations(page);
});
