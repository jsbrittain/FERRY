import { request, type APIRequestContext } from "@playwright/test";
import { createZip } from "./zip";

const BASE = process.env.PLAYWRIGHT_BASE_URL || "https://localhost";
export const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "admin@ferry.local";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin";
export const MAINTAINER_EMAIL =
  process.env.MAINTAINER_EMAIL || "maintainer@ferry.local";
const MAINTAINER_PASSWORD = process.env.MAINTAINER_PASSWORD || "maintainer";
export const RESEARCHER_EMAIL =
  process.env.RESEARCHER_EMAIL || "researcher@ferry.local";
const RESEARCHER_PASSWORD = process.env.RESEARCHER_PASSWORD || "researcher";

export const RESOURCE_IDENTIFIER = "demo-surveillance";
export const ENVIRONMENT_IDENTIFIER = "python-3.13";

async function createApiContext(email: string, password: string): Promise<APIRequestContext> {
  const ctx = await request.newContext({ baseURL: BASE, ignoreHTTPSErrors: true });
  const resp = await ctx.post("/api/auth/login", { data: { email, password } });
  if (!resp.ok()) throw new Error(`API login failed for ${email}: ${resp.status()}`);
  await ctx.post("/api/terms/platform/accept").catch(() => {});
  return ctx;
}

export async function ensureTermsPublished(): Promise<void> {
  const ctx = await createApiContext(ADMIN_EMAIL, ADMIN_PASSWORD);
  await ctx
    .post("/api/admin/terms/platform", {
      data: {
        version: "1.0.0",
        title: "FERRY Platform Terms",
        content: "## Terms\n\nAccept to continue.",
      },
    })
    .catch(() => {});
  await ctx.dispose();
}

export async function createUser(
  email: string,
  displayName: string,
  roles: string[],
): Promise<void> {
  const ctx = await createApiContext(ADMIN_EMAIL, ADMIN_PASSWORD);
  const resp = await ctx.post("/api/admin/users", {
    data: { email, display_name: displayName, password: "testpass123", roles },
  });
  if (!resp.ok() && resp.status() !== 409) {
    throw new Error(`Create user failed: ${resp.status()} ${await resp.text()}`);
  }
  await ctx.dispose();
}

export async function provisionProject(
  ts: number,
  researcherEmail?: string,
  moderatorEmail?: string,
): Promise<{ id: string; name: string }> {
  const ctx = await createApiContext(MAINTAINER_EMAIL, MAINTAINER_PASSWORD);
  const name = `Test Project ${ts}`;
  const projResp = await ctx.post("/api/projects", {
    data: { name, description: "Acceptance test project" },
  });
  if (!projResp.ok()) throw new Error(`Create project failed: ${await projResp.text()}`);
  const project = await projResp.json();

  if (researcherEmail) {
    const m = await ctx.post(`/api/projects/${project.id}/members`, { data: { email: researcherEmail } });
    if (!m.ok()) throw new Error(`Add researcher failed: ${await m.text()}`);
  }
  if (moderatorEmail) {
    const m = await ctx.post(`/api/projects/${project.id}/members`, { data: { email: moderatorEmail } });
    if (!m.ok()) throw new Error(`Add moderator failed: ${await m.text()}`);
  }

  const resResp = await ctx.get("/api/resources");
  if (resResp.ok()) {
    const resources = await resResp.json();
    const resource = resources.find((r: any) => r.identifier === RESOURCE_IDENTIFIER);
    if (resource) {
      await ctx.post(`/api/terms/resources/${resource.id}/accept`).catch(() => {});
    }
  }

  const attResp = await ctx.post(`/api/projects/${project.id}/resources`, {
    data: { resource_identifiers: [RESOURCE_IDENTIFIER] },
  });
  if (!attResp.ok()) throw new Error(`Attach resource failed: ${await attResp.text()}`);

  await ctx.dispose();
  return { id: project.id, name };
}

export async function createAndSubmitBundle(
  projectId: string,
  analysisName: string,
): Promise<string> {
  const ctx = await createApiContext(RESEARCHER_EMAIL, RESEARCHER_PASSWORD);

  const resResp = await ctx.get("/api/resources");
  if (resResp.ok()) {
    const resources = await resResp.json();
    const resource = resources.find((r: any) => r.identifier === RESOURCE_IDENTIFIER);
    if (resource) {
      await ctx.post(`/api/terms/resources/${resource.id}/accept`).catch(() => {});
    }
  }

  const createResp = await ctx.post(`/api/projects/${projectId}/bundles`, {
    data: { name: analysisName },
  });
  if (!createResp.ok()) throw new Error(`Create bundle failed: ${await createResp.text()}`);
  const bundle = await createResp.json();

  const zipBuffer = createZip([
    { name: "run.py", content: "print('hello')" },
    { name: "requirements.txt", content: "" },
  ]);
  const uploadResp = await ctx.post(
    `/api/projects/${projectId}/bundles/${bundle.id}/files/upload`,
    { multipart: { file: { name: "bundle.zip", mimeType: "application/zip", buffer: zipBuffer } } },
  );
  if (!uploadResp.ok()) throw new Error(`File upload failed: ${await uploadResp.text()}`);

  const envsResp = await ctx.get("/api/execution-environments");
  const envs = await envsResp.json();
  const env = envs.find((e: any) => e.identifier === ENVIRONMENT_IDENTIFIER);
  if (!env) throw new Error(`Environment ${ENVIRONMENT_IDENTIFIER} not found`);

  const updateResp = await ctx.put(`/api/projects/${projectId}/bundles/${bundle.id}`, {
    data: {
      execution_environment_id: env.id,
      version: "1.0.0", entrypoint: "run.py", interpreter: "python",
      resource_identifiers: [RESOURCE_IDENTIFIER],
    },
  });
  if (!updateResp.ok()) throw new Error(`Update bundle failed: ${await updateResp.text()}`);

  const submitResp = await ctx.post(`/api/projects/${projectId}/bundles/${bundle.id}/submit`);
  if (!submitResp.ok()) throw new Error(`Submit bundle failed: ${await submitResp.text()}`);

  await ctx.dispose();
  return bundle.id;
}
