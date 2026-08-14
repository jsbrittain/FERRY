import { test, expect } from "@playwright/test";
import { login } from "../helpers/auth";

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "admin@ferry.local";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin";

test("Administrator Acceptance", async ({ page }) => {
  const TS = Date.now();
  const researcherEmail = `researcher-${TS}@test.local`;
  const researcherName = `Alice R ${TS}`;
  const moderatorEmail = `moderator-${TS}@test.local`;
  const moderatorName = `Bob M ${TS}`;
  const newPassword = `newpass-${TS}`;

  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  await expect(page.getByTestId("header-user-name")).toHaveText(
    "Administrator",
  );

  // ---------------------------------------------------------------
  // 1. Platform Terms — publish via Admin UI
  // ---------------------------------------------------------------
  await page.getByRole("link", { name: "Admin" }).click();
  await page
    .getByRole("navigation", { name: "Admin tabs" })
    .getByRole("link", { name: "Terms" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Terms of Service \u2014 Published Versions" }),
  ).toBeVisible();

  // Fill and submit the platform terms publish form
  await page
    .locator('input[placeholder="Version (e.g., 1.0.0)"]')
    .first()
    .fill(TS.toString());
  await page.locator('input[placeholder="Title"]').first().fill("Platform Terms");
  await page
    .locator('textarea[placeholder="Terms content (Markdown)"]')
    .fill("## Terms\n\nAccept to continue.");
  await page.getByRole("button", { name: "Publish Platform Terms" }).click();
  await expect(page.getByText(/Platform terms published/)).toBeVisible();

  // ---------------------------------------------------------------
  // 2. User Management — create a Researcher
  // ---------------------------------------------------------------
  await page
    .getByRole("navigation", { name: "Admin tabs" })
    .getByRole("link", { name: "Users" })
    .click();
  await expect(page.getByRole("heading", { name: "Users" })).toBeVisible();

  // Open the create form
  await page.getByRole("button", { name: "Create User" }).click();

  // Fill form fields
  await page.getByPlaceholder("user@institution.org").fill(researcherEmail);
  await page.getByPlaceholder("Jane Researcher").fill(researcherName);
  await page.getByPlaceholder("Initial password").fill("initialpass123");

  // Researcher role is checked by default — submit
  await page.getByRole("button", { name: "Create User" }).click();

  // Verify the new researcher appears in the user list
  await expect(page.getByText(researcherEmail)).toBeVisible();
  await expect(page.getByText(researcherName)).toBeVisible();

  // ---------------------------------------------------------------
  // 3. User Management — create a Moderator
  // ---------------------------------------------------------------
  await page.getByRole("button", { name: "Create User" }).click();

  await page.getByPlaceholder("user@institution.org").fill(moderatorEmail);
  await page.getByPlaceholder("Jane Researcher").fill(moderatorName);
  await page.getByPlaceholder("Initial password").fill("initialpass456");

  // Uncheck default Researcher, check Moderator
  await page.getByRole("checkbox", { name: /Researcher/ }).uncheck();
  await page.getByRole("checkbox", { name: /Moderator/ }).check();

  await page.getByRole("button", { name: "Create User" }).click();

  // Verify the moderator appears in the user list
  await expect(page.getByText(moderatorEmail)).toBeVisible();
  await expect(page.getByText(moderatorName)).toBeVisible();

  // ---------------------------------------------------------------
  // 4. Role Assignment — edit a user's roles
  // ---------------------------------------------------------------
  // Find the researcher row and click Edit
  const researcherRow = page
    .locator("tr")
    .filter({ hasText: researcherName });
  await researcherRow.getByRole("button", { name: "Edit" }).click();

  // Add Moderator role to the researcher
  await page.getByRole("checkbox", { name: /Moderator/ }).check();

  // Save
  await page.getByRole("button", { name: "Save" }).click();

  // Verify the update persisted (Moderator badge appears on the researcher row)
  await expect(
    researcherRow.getByText("Moderator"),
  ).toBeVisible();

  // ---------------------------------------------------------------
  // 5. Password Reset — reset the moderator's password
  // ---------------------------------------------------------------
  const moderatorRow = page
    .locator("tr")
    .filter({ hasText: moderatorEmail });
  await moderatorRow.getByRole("button", { name: "Edit" }).click();

  // Open password reset form
  await expect(async () => {
    await page.getByRole("button", { name: "Reset Password" }).click();
  }).toPass({ timeout: 500 });

  // Enter new password
  await page.getByPlaceholder("Minimum 8 characters").fill(newPassword);

  // Save
  await page.getByRole("button", { name: "Save" }).click();

  // ---------------------------------------------------------------
  // 6. Sign out
  // ---------------------------------------------------------------
  await page.getByRole("button", { name: "Sign out" }).click();
});
