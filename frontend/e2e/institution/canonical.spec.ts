import { test, expect } from "@playwright/test";
import { execSync } from "child_process";
import * as fs from "fs";
import { createZip } from "../helpers/zip";
import { login } from "../helpers/auth";

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "admin@ferry.local";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin";
const MAINTAINER_EMAIL =
  process.env.MAINTAINER_EMAIL || "maintainer@ferry.local";
const MAINTAINER_PASSWORD = process.env.MAINTAINER_PASSWORD || "maintainer";

const ANALYSIS_CODE = `\
import pandas as pd
df = pd.read_csv("/data/demo-surveillance/demo.csv")
summary = df.describe()
summary.to_csv("/output/summary.csv")
print(f"Complete. Processed {len(df)} rows.")
`;

test("Canonical Workflow", async ({ page }) => {
  test.setTimeout(600_000);
  const TS = Date.now();
  const researcherEmail = `researcher-can-${TS}@test.local`;
  const moderatorEmail = `moderator-can-${TS}@test.local`;
  const projectName = `Canonical ${TS}`;
  const analysisName = `Analysis ${TS}`;

  // ===================================================================
  // 1. ADMINISTRATOR — publish terms, create users
  // ===================================================================
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  await expect(page.getByTestId("header-user-name")).toHaveText("Administrator");

  await page.request.post("/api/admin/terms/platform", {
    data: { version: TS.toString(), title: "FERRY Platform Terms", content: "## Terms\n\nBy using this platform you agree." },
  });
  await page.request.post("/api/admin/users", {
    data: { email: researcherEmail, display_name: "Canonical Researcher", password: "testpass123", roles: ["researcher"] },
  });
  await page.request.post("/api/admin/users", {
    data: { email: moderatorEmail, display_name: "Canonical Moderator", password: "testpass123", roles: ["moderator"] },
  });
  await page.getByRole("button", { name: "Sign out" }).click();

  // ===================================================================
  // 2. MAINTAINER — create project, add members, attach resource
  // ===================================================================
  await login(page, MAINTAINER_EMAIL, MAINTAINER_PASSWORD);
  await expect(page.getByTestId("header-user-name")).toHaveText("Maintainer");

  await page.getByRole("link", { name: "Projects" }).click();
  await page.getByRole("button", { name: "Create Project" }).click();
  await page.getByPlaceholder("Project name").fill(projectName);
  await page.getByPlaceholder("Optional description").fill("Canonical workflow project");
  await page.getByRole("dialog").getByRole("button", { name: "Create" }).click();
  await page.getByText(projectName).click();
  await page.waitForURL(/\/projects\//);

  const projectId = page.url().match(/\/projects\/([^/]+)/)?.[1];
  if (!projectId) throw new Error("Could not extract project ID");

  // Add members via the search UI
  await page.getByRole("link", { name: "Members" }).click();
  // Wait for member/user data to finish loading — the page renders either
  // the member list table or "No members yet." when both API calls complete.
  await expect(
    page.getByText("No members yet.").or(page.locator("table"))
  ).toBeVisible({ timeout: 15000 });
  await page.getByPlaceholder("Search by name or email...").fill(researcherEmail);
  await page.getByText(researcherEmail).click();
  await page.getByRole("button", { name: "Add Member" }).click();
  await expect(page.getByText(researcherEmail)).toBeVisible();

  await page.getByPlaceholder("Search by name or email...").fill(moderatorEmail);
  await page.getByText(moderatorEmail).click();
  await page.getByRole("button", { name: "Add Member" }).click();
  await expect(page.getByText(moderatorEmail)).toBeVisible();

  await page.getByRole("link", { name: "Resources", exact: true }).click();
  await expect(page.getByText("Configure Resources")).toBeVisible();
  await page.locator("tr").filter({ hasText: "demo-surveillance" }).getByRole("button", { name: "Attach" }).click();
  await page.getByRole("button", { name: "Accept & Continue" }).click();
  await expect(page.getByText("demo-surveillance")).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();

  // Accept platform + resource terms for the researcher
  await page.request.post("/api/auth/login", { data: { email: researcherEmail, password: "testpass123" } });
  await page.request.post("/api/terms/platform/accept").catch(() => {});
  const resReq = await page.request.get("/api/resources");
  if (resReq.ok()) {
    const resources = await resReq.json();
    const resource = resources.find((r: any) => r.identifier === "demo-surveillance");
    if (resource) await page.request.post(`/api/terms/resources/${resource.id}/accept`).catch(() => {});
  }

  // ===================================================================
  // 3. RESEARCHER — create bundle, validate, submit
  // ===================================================================
  await login(page, researcherEmail, "testpass123");
  await page.getByRole("link", { name: "Projects" }).click();
  await page.getByText(projectName).click();
  await page.getByRole("link", { name: "Analysis" }).click();
  await page.getByRole("button", { name: "New Draft Bundle" }).click();
  await page.waitForURL(/\/projects\/[^/]+\/analysis\/[^/]+$/);
  await page.locator('input[type="text"]').first().fill(analysisName);

  const zipBuffer = createZip([
    { name: "run.py", content: ANALYSIS_CODE },
    { name: "requirements.txt", content: "" },
  ]);
  await page.getByRole("button", { name: "Upload ZIP" }).click();
  await page.locator('input[type="file"]').setInputFiles({ name: "bundle.zip", mimeType: "application/zip", buffer: zipBuffer });
  await page.getByLabel("Environment").selectOption({ label: "Python 3.13" });
  await page.locator("#edit-version-exec").fill("1.0.0");
  await page.waitForTimeout(1000);
  const entrypointSelect = page.locator("select").filter({ has: page.locator('option[value="run.py"]') }).first();
  if (await entrypointSelect.isVisible()) await entrypointSelect.selectOption("run.py");
  await page.getByLabel("Interpreter").selectOption("Python");
  await page.getByText("(demo-surveillance)").click();

  await page.getByRole("button", { name: "Run Validation" }).click();
  await expect(page.locator(".card").filter({ hasText: "Validation Run" }).getByText(/completed/)).toBeVisible({ timeout: 180_000 });

  await page.getByRole("button", { name: "Save and Close" }).click();
  await page.waitForURL(/\/projects\/[^/]+\/analysis$/);
  await page.getByText(analysisName).click();
  await page.waitForURL(/\/projects\/[^/]+\/analysis\/[^/]+$/);
  await page.getByRole("button", { name: "Submit for Review" }).click();
  await expect(page.getByText("Submitted")).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();

  // ===================================================================
  // 4. MODERATOR — review and approve bundle
  // ===================================================================
  await login(page, moderatorEmail, "testpass123");
  await page.getByRole("link", { name: "Review", exact: true }).click();
  await page.getByRole("navigation", { name: "Review tabs" }).getByRole("link", { name: "Analyses" }).click();
  await expect(page.getByText("Analysis Operations")).toBeVisible();

  const bundleRow = page.locator("tr").filter({ hasText: analysisName }).first();
  await expect(bundleRow).toBeVisible({ timeout: 15_000 });
  await bundleRow.getByRole("button", { name: "Inspect" }).click();
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await page.getByRole("button", { name: "Approve Analysis", exact: true }).click();

  await page.getByRole("button", { name: "Approved", exact: true }).click();
  await expect(page.locator("tr").filter({ hasText: analysisName }).first().getByText("Approved for Execution")).toBeVisible({ timeout: 10_000 });
  await page.getByRole("button", { name: "Close" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();

  // ===================================================================
  // 5. RESEARCHER — run approved analysis
  // ===================================================================
  await login(page, researcherEmail, "testpass123");
  await page.getByRole("link", { name: "Projects" }).click();
  await page.getByText(projectName).click();
  await page.getByRole("link", { name: "Analysis" }).click();
  await page.getByText(analysisName).click();
  await page.waitForURL(/\/projects\/[^/]+\/analysis\/[^/]+$/);
  await page.getByRole("button", { name: "Run Analysis" }).click();
  await expect(page.locator("tr").filter({ hasText: analysisName }).first().getByText("completed")).toBeVisible({ timeout: 180_000 });
  await page.getByRole("button", { name: "Sign out" }).click();

  // ===================================================================
  // 6. MODERATOR — approve output, verify audit
  // ===================================================================
  await login(page, moderatorEmail, "testpass123");
  await page.getByRole("link", { name: "Review", exact: true }).click();
  await page.getByRole("navigation", { name: "Review tabs" }).getByRole("link", { name: "Outputs" }).click();

  const setRow = page.locator("tr").filter({ hasText: analysisName }).first();
  await expect(setRow).toBeVisible({ timeout: 30_000 });
  await setRow.getByRole("button", { name: "Inspect" }).click();
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await page.getByRole("button", { name: "Approve Output Set", exact: true }).click();
  await expect(setRow.getByText("Approved")).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();

  // ===================================================================
  // 6b. MODERATOR — release output set via API
  // ===================================================================
  await page.request.post("/api/auth/login", { data: { email: moderatorEmail, password: "testpass123" } });
  await page.request.post("/api/terms/platform/accept");
  const modSetsResp = await page.request.get("/api/admin/output-sets");
  const modSets = modSetsResp.ok() ? await modSetsResp.json() : [];
  const targetSet = modSets.find(
    (s: any) => s.execution_request_name?.includes(analysisName) && s.status === "approved",
  );
  if (!targetSet) throw new Error("Output set not found for release");
  const releaseResp = await page.request.post(`/api/admin/output-sets/${targetSet.id}/release`);
  if (!releaseResp.ok()) throw new Error(`Release failed: ${await releaseResp.text()}`);

  // ===================================================================
  // 7. RESEARCHER — download released outputs
  // ===================================================================
  await login(page, researcherEmail, "testpass123");
  await page.getByRole("link", { name: "Projects" }).click();
  await page.getByText(projectName).click();
  await page.getByRole("link", { name: "Outputs" }).click();

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("link", { name: "Download All" }).click(),
  ]);

  expect(download.suggestedFilename()).toMatch(/\.zip$/);
  const downloadPath = await download.path();
  expect(downloadPath).not.toBeNull();
  if (downloadPath) {
    const stats = fs.statSync(downloadPath);
    expect(stats.size).toBeGreaterThan(0);
    const listing = execSync(`unzip -l "${downloadPath}"`, { encoding: "utf-8" });
    expect(listing).toContain("summary.csv");
    expect(listing).toContain("execution_metadata.json");
  }

  await page.getByRole("button", { name: "Sign out" }).click();
});
