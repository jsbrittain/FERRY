import { request, type APIRequestContext, type Download } from "@playwright/test";
import { execSync } from "child_process";
import * as fs from "fs";
import {
  ensureTermsPublished,
  RESEARCHER_EMAIL,
  RESOURCE_IDENTIFIER,
} from "./setup";

const BASE = process.env.PLAYWRIGHT_BASE_URL || "https://localhost";
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "admin@ferry.local";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin";
const MODERATOR_PASSWORD = "testpass123";
const MAINTAINER_EMAIL =
  process.env.MAINTAINER_EMAIL || "maintainer@ferry.local";
const MAINTAINER_PASSWORD = process.env.MAINTAINER_PASSWORD || "maintainer";
const RESEARCHER_PASSWORD = process.env.RESEARCHER_PASSWORD || "researcher";

async function createApiContext(
  email: string,
  password: string,
): Promise<APIRequestContext> {
  const ctx = await request.newContext({
    baseURL: BASE,
    ignoreHTTPSErrors: true,
  });
  const resp = await ctx.post("/api/auth/login", { data: { email, password } });
  if (!resp.ok()) throw new Error(`API login failed for ${email}: ${resp.status()}`);
  await ctx.post("/api/terms/platform/accept").catch(() => {});
  return ctx;
}

export async function provisionExecutionTestProject(
  ts: number,
): Promise<{ id: string; name: string; moderatorEmail: string }> {
  await ensureTermsPublished();
  const ctx = await createApiContext(MAINTAINER_EMAIL, MAINTAINER_PASSWORD);
  const name = `EE Test Project ${ts}`;

  const projResp = await ctx.post("/api/projects", {
    data: { name, description: "Execution environment acceptance test" },
  });
  if (!projResp.ok()) throw new Error(`Create project failed: ${await projResp.text()}`);
  const project = await projResp.json();

  const mResp = await ctx.post(`/api/projects/${project.id}/members`, {
    data: { email: RESEARCHER_EMAIL },
  });
  if (!mResp.ok()) throw new Error(`Add researcher failed: ${await mResp.text()}`);

  const resResp = await ctx.get("/api/resources");
  if (resResp.ok()) {
    const resources = await resResp.json();
    const resource = resources.find(
      (r: any) => r.identifier === RESOURCE_IDENTIFIER,
    );
    if (resource) {
      await ctx.post(`/api/terms/resources/${resource.id}/accept`).catch(() => {});
    }
  }

  const attResp = await ctx.post(`/api/projects/${project.id}/resources`, {
    data: { resource_identifiers: [RESOURCE_IDENTIFIER] },
  });
  if (!attResp.ok()) {
    throw new Error(`Attach resource failed: ${await attResp.text()}`);
  }

  await ctx.dispose();

  // Create a moderator user for bundle approval and add to project
  const moderatorEmail = `moderator-ee-${ts}@setup.local`;
  const adminCtx = await createApiContext(ADMIN_EMAIL, ADMIN_PASSWORD);
  const userResp = await adminCtx
    .post("/api/admin/users", {
      data: {
        email: moderatorEmail,
        display_name: "EE Moderator",
        password: MODERATOR_PASSWORD,
        roles: ["moderator"],
      },
    });
  if (!userResp.ok()) throw new Error(`Create moderator failed: ${await userResp.text()}`);
  await adminCtx.dispose();

  const maintCtx2 = await createApiContext(MAINTAINER_EMAIL, MAINTAINER_PASSWORD);
  const memResp = await maintCtx2.post(`/api/projects/${project.id}/members`, {
    data: { email: moderatorEmail },
  });
  if (!memResp.ok()) throw new Error(`Add moderator to project failed: ${await memResp.text()}`);
  await maintCtx2.dispose();

  return { id: project.id, name, moderatorEmail };
}

export async function createExecutionBundle(
  projectId: string,
  name: string,
  envIdentifier: string,
  entrypoint: string,
  interpreter: string,
): Promise<{ bundleId: string; bundleName: string }> {
  const ctx = await createApiContext(RESEARCHER_EMAIL, RESEARCHER_PASSWORD);

  const resResp = await ctx.get("/api/resources");
  if (resResp.ok()) {
    const resources = await resResp.json();
    const resource = resources.find(
      (r: any) => r.identifier === RESOURCE_IDENTIFIER,
    );
    if (resource) {
      await ctx.post(`/api/terms/resources/${resource.id}/accept`).catch(() => {});
    }
  }

  const createResp = await ctx.post(`/api/projects/${projectId}/bundles`, {
    data: { name },
  });
  if (!createResp.ok()) {
    throw new Error(`Create bundle failed: ${await createResp.text()}`);
  }
  const bundle = await createResp.json();

  const envsResp = await ctx.get("/api/execution-environments");
  const envs = await envsResp.json();
  const env = envs.find((e: any) => e.identifier === envIdentifier);
  if (!env) throw new Error(`Environment ${envIdentifier} not found`);

  const updateResp = await ctx.put(
    `/api/projects/${projectId}/bundles/${bundle.id}`,
    {
      data: {
        execution_environment_id: env.id,
        version: "1.0.0",
        entrypoint,
        interpreter,
        resource_identifiers: [RESOURCE_IDENTIFIER],
      },
    },
  );
  if (!updateResp.ok()) {
    throw new Error(`Update bundle failed: ${await updateResp.text()}`);
  }

  await ctx.dispose();
  return { bundleId: bundle.id, bundleName: name };
}

export async function approveBundle(
  bundleId: string,
  moderatorEmail: string,
): Promise<void> {
  const ctx = await createApiContext(moderatorEmail, MODERATOR_PASSWORD);
  const resp = await ctx.post(`/api/admin/bundles/${bundleId}/approve`);
  if (!resp.ok()) throw new Error(`Approve failed: ${await resp.text()}`);
  await ctx.dispose();
}

export async function pollBuild(
  projectId: string,
  bundleId: string,
  api: APIRequestContext,
): Promise<void> {
  const deadline = Date.now() + 300_000;

  while (Date.now() < deadline) {
    const resp = await api.get(
      `/api/projects/${projectId}/bundles/${bundleId}`,
    );
    if (resp.ok()) {
      const bundle = await resp.json();
      if (bundle.build_status === "environment_ready") {
        return;
      }
      if (bundle.build_status === "environment_build_failed") {
        throw new Error(
          `Build failed: ${bundle.build_error || "unknown error"}`,
        );
      }
    }
    await new Promise((r) => setTimeout(r, 5000));
  }
  throw new Error("Build did not complete within 300s");
}

export async function approveAndReleaseOutputSetForBundle(
  bundleId: string,
  projectId: string,
): Promise<void> {
  const moderatorEmail = `release-moderator-${Date.now()}@setup.local`;
  const moderatorPassword = "testpass123";
  const adminCtx = await createApiContext(ADMIN_EMAIL, ADMIN_PASSWORD);
  const userResp = await adminCtx.post("/api/admin/users", {
    data: {
      email: moderatorEmail,
      display_name: "Release Moderator",
      password: moderatorPassword,
      roles: ["moderator"],
    },
  });
  if (!userResp.ok()) throw new Error(`Create release moderator failed: ${await userResp.text()}`);
  await adminCtx.dispose();

  const maintCtx2 = await createApiContext(MAINTAINER_EMAIL, MAINTAINER_PASSWORD);
  const memResp = await maintCtx2.post(`/api/projects/${projectId}/members`, {
    data: { email: moderatorEmail },
  });
  if (!memResp.ok()) throw new Error(`Add release moderator to project failed: ${await memResp.text()}`);
  await maintCtx2.dispose();

  // Step 1: Find the execution request and approve output set (moderator)
  const modCtx = await createApiContext(moderatorEmail, moderatorPassword);
  const execDeadline = Date.now() + 60_000;
  let execRequestId: string | null = null;

  while (Date.now() < execDeadline) {
    const resp = await modCtx.get(`/api/projects/${projectId}/execution-requests`);
    if (resp.ok()) {
      const requests = await resp.json();
      const match = requests.find(
        (r: any) => r.analysis_bundle_id === bundleId,
      );
      if (match && match.status === "completed") {
        execRequestId = match.id;
        break;
      }
    }
    await new Promise((r) => setTimeout(r, 2000));
  }

  if (!execRequestId) throw new Error("Completed execution request not found within 60s");

  // Step 2: Wait for and approve the output set (moderator)
  const outDeadline = Date.now() + 60_000;
  let outputSetId: string | null = null;

  while (Date.now() < outDeadline) {
    const resp = await modCtx.get(
      `/api/admin/execution-requests/${execRequestId}/outputs`,
    );
    if (resp.ok()) {
      const outputSet = await resp.json();
      if (outputSet && outputSet.id) {
        outputSetId = outputSet.id;
        break;
      }
    }
    await new Promise((r) => setTimeout(r, 2000));
  }

  if (!outputSetId) throw new Error("Output set not created within 60s");

  const aprResp = await modCtx.post(
    `/api/admin/output-sets/${outputSetId}/approve`,
  );
  if (!aprResp.ok()) {
    throw new Error(`Approve output set failed: ${await aprResp.text()}`);
  }

  // Step 3: Release the output set (same moderator — now has output.release)
  const relResp = await modCtx.post(
    `/api/admin/output-sets/${outputSetId}/release`,
  );
  await modCtx.dispose();
  if (!relResp.ok()) {
    throw new Error(`Release output set failed: ${await relResp.text()}`);
  }
}

export async function verifyArchiveContents(
  download: Download,
  expectedFiles: string[],
): Promise<void> {
  const filename = download.suggestedFilename();
  if (!/\.zip$/i.test(filename)) {
    throw new Error(`Expected .zip download, got: ${filename}`);
  }
  const downloadPath = await download.path();
  if (!downloadPath) throw new Error("Download path is null");
  const stats = fs.statSync(downloadPath);
  if (stats.size === 0) throw new Error("Downloaded archive is empty");
  const listing = execSync(`unzip -l "${downloadPath}"`, {
    encoding: "utf-8",
  });
  for (const file of expectedFiles) {
    if (!listing.includes(file)) {
      throw new Error(`Expected file "${file}" not found in archive`);
    }
  }
}
