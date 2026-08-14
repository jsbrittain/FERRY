"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/AuthContext";
import {
  OutputSetListItem,
  OutputSet,
  AuditEvent,
  getAdminOutputSets,
  getAdminOutputSet,
  getGovernanceStatus,
  approveOutputSet,
  rejectOutputSet,
  releaseOutputSet,
  triggerOutputSetAiReview,
  getAdminOutputSetFileContent,
  getAuditEvents,
  downloadAdminOutputSetZip,
} from "@/lib/api";
import { RejectDialog } from "@/components/RejectDialog";
import { ConfirmationDialog } from "@/components/ConfirmationDialog";
import AIReviewCard from "@/components/AIReviewCard";
import type { AIReview } from "@/components/AIReviewCard";
import { CodeBlock } from "@/components/CodeBlock";

function eventLabel(eventType: string): string {
  const labels: Record<string, string> = {
    "output_set.created": "Output set created",
    "output_set.approved": "Output approved",
    "output_set.rejected": "Output rejected",
    "output_set.released": "Output released",
    "execution.started": "Execution started",
    "execution.completed": "Execution completed",
    "execution.failed": "Execution failed",
  };
  return labels[eventType] || eventType;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString();
}

function statusBadge(status: string): { background: string; color: string; label: string } {
  switch (status) {
    case "pending_review":
      return { background: "#fff3e0", color: "#e65100", label: "Pending Review" };
    case "approved":
      return { background: "#e3f2fd", color: "#1565c0", label: "Approved" };
    case "rejected":
      return { background: "#f8d7da", color: "#721c24", label: "Rejected" };
    case "released":
      return { background: "#d4edda", color: "#155724", label: "Released" };
    default:
      return { background: "#f0f0f0", color: "#666", label: status };
  }
}

const STATUS_FILTERS = [
  { key: "all", label: "All" },
  { key: "pending_review", label: "Pending Review" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
  { key: "released", label: "Released" },
];

function isBinaryFile(filename: string): boolean {
  const textExts = new Set([
    "py", "r", "R", "sh", "js", "ipynb", "txt", "md",
    "csv", "json", "yaml", "yml", "xml", "html", "htm",
    "cfg", "conf", "ini", "env", "log", "tsv", "rst",
    "toml", "css", "ts", "tsx", "jsx", "sql",
  ]);
  const parts = filename.split(".");
  const ext = parts.length > 1 ? parts[parts.length - 1].toLowerCase() : "";
  return !textExts.has(ext);
}

export default function GovernanceOutputsPage() {
  const { user } = useAuth();
  const [allSets, setAllSets] = useState<OutputSetListItem[]>([]);
  const [govStatus, setGovStatus] = useState<{ prevent_self_moderation: boolean } | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [expandedData, setExpandedData] = useState<Record<string, OutputSet>>({});
  const [outputAudit, setOutputAudit] = useState<Record<string, AuditEvent[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [rejectTarget, setRejectTarget] = useState<string | null>(null);
  const [approveTarget, setApproveTarget] = useState<string | null>(null);
  const [viewedFile, setViewedFile] = useState<Record<string, string | null>>({});
  const [fileContent, setFileContent] = useState<Record<string, string>>({});
  const [fileContentLoading, setFileContentLoading] = useState<Record<string, boolean>>({});
  const [aiReviewTriggerId, setAiReviewTriggerId] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<Record<string, AIReview | null>>({});

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return Promise.all([
      getAdminOutputSets(),
      getGovernanceStatus().catch(() => null),
    ])
      .then(([data, gov]) => {
        setAllSets(data);
        setGovStatus(gov);
      })
      .catch(() => setError("Failed to load output sets"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const filteredSets = statusFilter === "all"
    ? allSets
    : allSets.filter((s) => s.status === statusFilter);

  const handleAction = async (
    outputSetId: string,
    apiFn: (id: string) => Promise<unknown>,
  ) => {
    setActionError(null);
    setActionLoading(true);
    try {
      await apiFn(outputSetId);
      await load();
      if (expandedId === outputSetId) {
        const updated = await getAdminOutputSet(outputSetId);
        setExpandedData((prev) => ({ ...prev, [outputSetId]: updated }));
        setAiStatus((prev) => ({
          ...prev,
          [outputSetId]: updated.ai_review ?? null,
        }));
      }
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setActionLoading(false);
    }
  };

  const handleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      setExpandedData((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      setViewedFile((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      return;
    }
    try {
      const outputSet = await getAdminOutputSet(id);
      setExpandedData((prev) => ({ ...prev, [id]: outputSet }));
      setAiStatus((prev) => ({
        ...prev,
        [id]: outputSet.ai_review ?? null,
      }));
    } catch {
      setExpandedData((prev) => ({ ...prev, [id]: null as unknown as OutputSet }));
    }
    if (!outputAudit[id]) {
      try {
        const res = await getAuditEvents({
          resource_type: "output_set",
          resource_id: id,
          limit: 20,
        });
        setOutputAudit((prev) => ({ ...prev, [id]: res.items }));
      } catch {
        setOutputAudit((prev) => ({ ...prev, [id]: [] }));
      }
    }
    setExpandedId(id);
  };

  const handleViewFile = async (outputSetId: string, path: string) => {
    if (viewedFile[outputSetId] === path) {
      setViewedFile((prev) => ({ ...prev, [outputSetId]: null }));
      return;
    }
    setViewedFile((prev) => ({ ...prev, [outputSetId]: path }));
    const cacheKey = `${outputSetId}:${path}`;
    if (!fileContent[cacheKey]) {
      setFileContentLoading((prev) => ({ ...prev, [cacheKey]: true }));
      try {
        const content = await getAdminOutputSetFileContent(outputSetId, path);
        setFileContent((prev) => ({ ...prev, [cacheKey]: content }));
      } catch {
        setFileContent((prev) => ({ ...prev, [cacheKey]: "Failed to load file content." }));
      } finally {
        setFileContentLoading((prev) => ({ ...prev, [cacheKey]: false }));
      }
    }
  };

  const handleTriggerAiReview = async (outputSetId: string) => {
    setAiReviewTriggerId(outputSetId);
    setAiStatus((prev) => ({
      ...prev,
      [outputSetId]: {
        id: "",
        status: "pending",
        summary: null,
        assessment: null,
        assessment_confidence: null,
        reviewer_notes: null,
      },
    }));
    try {
      const updated = await triggerOutputSetAiReview(outputSetId);
      setExpandedData((prev) => ({ ...prev, [outputSetId]: updated }));
      setAiStatus((prev) => ({
        ...prev,
        [outputSetId]: updated.ai_review ?? null,
      }));
      const poll = setInterval(async () => {
        try {
          const refreshed = await getAdminOutputSet(outputSetId);
          setExpandedData((prev) => ({ ...prev, [outputSetId]: refreshed }));
          const review = refreshed.ai_review;
          if (review && review.status !== "pending") {
            setAiStatus((prev) => ({ ...prev, [outputSetId]: review }));
            clearInterval(poll);
          }
        } catch {
          clearInterval(poll);
        }
      }, 5000);
    } catch {
      setAiStatus((prev) => ({
        ...prev,
        [outputSetId]: null,
      }));
    } finally {
      setAiReviewTriggerId(null);
    }
  };

  const pendingReviewId = expandedId && aiStatus[expandedId]?.status === "pending" ? expandedId : null;

  useEffect(() => {
    if (!pendingReviewId) return;

    const poll = setInterval(async () => {
      try {
        const refreshed = await getAdminOutputSet(pendingReviewId);
        const r = refreshed.ai_review;
        if (r && r.status !== "pending") {
          setAiStatus((prev) => ({ ...prev, [pendingReviewId]: r }));
          clearInterval(poll);
        }
      } catch {
        clearInterval(poll);
      }
    }, 5000);

    return () => clearInterval(poll);
  }, [pendingReviewId]);

  const handleDownloadFile = async (outputSetId: string, filename: string) => {
    try {
      const response = await fetch(
        `/api/admin/output-sets/${outputSetId}/files/${encodeURIComponent(filename)}`,
        { credentials: "include" },
      );
      if (!response.ok) throw new Error("Download failed");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      // silent
    }
  };

  const handleDownloadAll = async (outputSetId: string) => {
    try {
      await downloadAdminOutputSetZip(outputSetId);
    } catch {
      // silent
    }
  };

  return (
    <>
      <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "var(--spacing-md)" }}>
        Execution Outputs
      </h2>

      {!loading && !error && allSets.length > 0 && (
        <div style={{ display: "flex", gap: "var(--spacing-xs)", marginBottom: "var(--spacing-md)", flexWrap: "wrap" }}>
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setStatusFilter(f.key)}
              style={{
                padding: "4px 12px",
                fontSize: "0.85rem",
                background:
                  statusFilter === f.key
                    ? "var(--color-primary, #1976d2)"
                    : "transparent",
                color:
                  statusFilter === f.key
                    ? "#fff"
                    : "var(--color-text-secondary)",
                border: "1px solid",
                borderColor:
                  statusFilter === f.key
                    ? "var(--color-primary, #1976d2)"
                    : "var(--color-border)",
                borderRadius: "4px",
                cursor: "pointer",
                fontWeight: statusFilter === f.key ? 600 : 400,
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="card empty-state">Loading...</div>
      ) : error ? (
        <div className="card empty-state">{error}</div>
      ) : allSets.length === 0 ? (
        <div className="card empty-state">No output sets registered yet.</div>
      ) : filteredSets.length === 0 ? (
        <div className="card empty-state">No output sets with status "{statusFilter.replace("_", " ")}".</div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Project</th>
                <th>Analysis</th>
                <th>Files</th>
                <th>Status</th>
                <th>Inspect</th>
              </tr>
            </thead>
            <tbody>
              {filteredSets.map((s) => {
                const badge = statusBadge(s.status);
                return (
                  <tr key={s.id}>
                    <td style={{ color: "var(--color-text-secondary)" }}>
                      {s.project_name || ""}
                    </td>
                    <td style={{ fontWeight: 500 }}>
                      <button
                        onClick={() => handleExpand(s.id)}
                        style={{
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          fontWeight: 600,
                          fontSize: "0.9rem",
                          padding: 0,
                          color: "var(--color-text)",
                        }}
                      >
                        {s.execution_request_name || s.execution_request_id.slice(0, 8)}
                      </button>
                    </td>
                    <td style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem" }}>
                      {s.file_count} file{s.file_count !== 1 ? "s" : ""}
                    </td>
                    <td>
                      <span
                        style={{
                          display: "inline-block",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "0.8rem",
                          fontWeight: 600,
                          background: badge.background,
                          color: badge.color,
                        }}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleExpand(s.id)}
                        style={{
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          fontSize: "0.85rem",
                          padding: 0,
                          color: "var(--color-primary, #1976d2)",
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {expandedId && expandedData[expandedId] && (() => {
        const os = expandedData[expandedId];
        const osId = expandedId;
        const outputs = os?.outputs || [];

        const hasBinary = outputs.some((o) => isBinaryFile(o.filename));
        const close = () => setExpandedId(null);

        return (
          <div
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0,0,0,0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 1000,
            }}
            onClick={close}
          >
            <div
              className="card"
              style={{
                maxWidth: "720px",
                width: "90%",
                maxHeight: "80vh",
                overflowY: "auto",
                padding: 0,
                fontSize: "0.85rem",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "var(--spacing-md) var(--spacing-lg)",
                  borderBottom: "1px solid var(--color-border)",
                }}
              >
                <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>
                  Output Set Detail
                </h3>
                <button
                  onClick={close}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "1.2rem",
                    color: "var(--color-text-secondary)",
                    padding: "4px",
                    lineHeight: 1,
                  }}
                  aria-label="Close"
                >
                  ×
                </button>
              </div>

              <div style={{ padding: "var(--spacing-lg)" }}>
                  {os?.status === "pending_review" && user?.capabilities.includes("output.review") && govStatus?.prevent_self_moderation === true && os.requested_by_id === user?.id && !user?.capabilities.includes("governance.self_regulate") && (
                    <div style={{
                      padding: "12px 16px",
                      marginBottom: "var(--spacing-lg)",
                      background: "#fff3cd",
                      border: "1px solid #ffc107",
                      borderRadius: "4px",
                      color: "#856404",
                      fontSize: "0.85rem",
                      lineHeight: 1.6,
                    }}>
                      <strong>Independent moderation required.</strong><br />
                      You requested this execution. Another authorised moderator
                      must review its outputs.
                    </div>
                  )}
                {/* Rejection reason */}
                {os?.rejection_reason && (
                  <div
                    style={{
                      fontSize: "0.85rem",
                      marginBottom: "var(--spacing-sm)",
                      padding: "8px 12px",
                      background: "#f8d7da",
                      borderRadius: "4px",
                    }}
                  >
                    <strong style={{ display: "block", marginBottom: "4px" }}>
                      Rejection reason:
                    </strong>
                    {os.rejection_reason}
                  </div>
                )}

                {/* Binary artefacts warning */}
                {hasBinary && (
                  <div
                    style={{
                      fontSize: "0.85rem",
                      marginBottom: "var(--spacing-lg)",
                      padding: "12px 16px",
                      background: "#f8d7da",
                      border: "1px solid #f5c6cb",
                      borderRadius: "4px",
                      lineHeight: 1.6,
                    }}
                  >
                    <strong>Binary artefacts present</strong>
                    <br />
                    This Output Set contains one or more binary artefacts
                    that cannot be previewed within FERRY.
                    These files are available for download if you wish
                    to inspect them using external tools.
                  </div>
                )}

                {/* Artefacts with file inspection */}
                {outputs.length > 0 && (
                  <section aria-label="Output Files" style={{ marginBottom: "var(--spacing-lg)" }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "var(--spacing-sm)",
                      }}
                    >
                      <h3
                        style={{
                          fontSize: "0.95rem",
                          fontWeight: 600,
                          margin: 0,
                        }}
                      >
                        Artefacts
                      </h3>
                      <button
                        className="btn btn-sm"
                        onClick={() => handleDownloadAll(osId)}
                      >
                        Download All
                      </button>
                    </div>
                    {outputs.map((o) => {
                      const isBinary = isBinaryFile(o.filename);
                      const isViewing = viewedFile[osId] === o.filename;
                      return (
                        <div key={o.filename} style={{ marginBottom: "var(--spacing-xs)" }}>
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "var(--spacing-sm)",
                              padding: "4px 0",
                            }}
                          >
                            <span style={{ fontWeight: 500, fontSize: "0.85rem" }}>
                              {o.filename}
                            </span>
                            <span style={{ color: "var(--color-text-secondary)", fontSize: "0.8rem" }}>
                              {o.size > 1024
                                ? `${(o.size / 1024).toFixed(1)} KB`
                                : `${o.size} bytes`}
                            </span>
                            {isBinary ? (
                              <span
                                style={{
                                  display: "inline-block",
                                  padding: "1px 6px",
                                  borderRadius: "3px",
                                  fontSize: "0.7rem",
                                  fontWeight: 600,
                                  background: "#fff3e0",
                                  color: "#e65100",
                                }}
                                title="Binary file — manual inspection required"
                              >
                                BIN
                              </span>
                            ) : (
                              <button
                                className="btn btn-sm"
                                style={{
                                  background: "none",
                                  border: "1px solid var(--color-border, #ccc)",
                                  cursor: "pointer",
                                  fontSize: "0.75rem",
                                  padding: "2px 8px",
                                }}
                                onClick={() => handleViewFile(osId, o.filename)}
                              >
                                {isViewing ? "Close" : "View"}
                              </button>
                            )}
                            <button
                              className="btn btn-sm"
                              style={{
                                background: "none",
                                border: "1px solid var(--color-border, #ccc)",
                                cursor: "pointer",
                                fontSize: "0.75rem",
                                padding: "2px 8px",
                              }}
                              onClick={() => handleDownloadFile(osId, o.filename)}
                            >
                              Download
                            </button>
                          </div>
                          {isViewing && (
                            <div style={{ marginTop: "var(--spacing-xs)", marginBottom: "var(--spacing-sm)" }}>
                              {fileContentLoading[`${osId}:${o.filename}`] ? (
                                <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem" }}>
                                  Loading file content...
                                </div>
                              ) : fileContent[`${osId}:${o.filename}`] ? (
                                <CodeBlock
                                  code={fileContent[`${osId}:${o.filename}`]}
                                  language={o.filename.split(".").pop() || "text"}
                                />
                              ) : null}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </section>
                )}

                {/* AI Review section */}
                <section aria-label="AI Review">
                  <AIReviewCard
                    review={aiStatus[osId] ?? null}
                    title="AI Outputs Summary"
                    onRefresh={
                      aiStatus[osId]?.status !== "pending"
                        ? () => handleTriggerAiReview(osId)
                        : undefined
                    }
                    refreshing={aiReviewTriggerId === osId}
                  />
                </section>

                {/* Audit History */}
                <section aria-label="Audit History" style={{ marginBottom: "var(--spacing-lg)" }}>
                  <h3
                    style={{
                      fontSize: "0.95rem",
                      fontWeight: 600,
                      marginBottom: "var(--spacing-sm)",
                    }}
                  >
                    Governance History
                  </h3>
                  {!outputAudit[osId] ? (
                    <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem" }}>
                      Loading...
                    </div>
                  ) : outputAudit[osId].length === 0 ? (
                    <div style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem" }}>
                      No audit events.
                    </div>
                  ) : (
                    outputAudit[osId].map((e) => (
                      <div
                        key={e.id}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          padding: "3px 0",
                          borderBottom: "1px solid var(--color-border, #eee)",
                          fontSize: "0.85rem",
                        }}
                      >
                        <span style={{ fontWeight: 500 }}>{eventLabel(e.event_type)}</span>
                        <span style={{ color: "var(--color-text-secondary)" }}>
                          {e.actor_display_name} — {formatTime(e.occurred_at)}
                        </span>
                      </div>
                    ))
                  )}
                </section>

                {/* Governance Actions */}
                <section aria-label="Governance Actions">
                  {os?.status === "pending_review" && user?.capabilities.includes("output.review") && !(govStatus?.prevent_self_moderation === true && os.requested_by_id === user?.id && !user?.capabilities.includes("governance.self_regulate")) && (
                    <div style={{ paddingTop: "var(--spacing-md)" }}>
                      <div style={{ display: "flex", gap: "var(--spacing-sm)" }}>
                        <button
                          className="btn btn-sm"
                          style={{ background: "var(--color-success, #2e7d32)", color: "#fff", border: "none" }}
                          onClick={() => setApproveTarget(osId)}
                          disabled={actionLoading}
                        >
                          {actionLoading ? "Processing…" : "Approve"}
                        </button>
                        <button
                          className="btn btn-sm"
                          style={{ background: "var(--color-danger, #c62828)", color: "#fff", border: "none" }}
                          onClick={() => setRejectTarget(osId)}
                          disabled={actionLoading}
                        >
                          {actionLoading ? "Processing…" : "Reject"}
                        </button>
                      </div>
                    </div>
                  )}
                  {os?.status === "approved" && user?.capabilities.includes("output.release") && (
                    <div style={{ paddingTop: "var(--spacing-md)" }}>
                      {govStatus?.prevent_self_moderation === true
                        && os.requested_by_id === user?.id
                        && !user?.capabilities.includes("governance.self_regulate") ? (
                        <span style={{ color: "var(--color-text-secondary)", fontSize: "0.85rem", fontStyle: "italic" }}>
                          Independent release required. You requested
                          this execution. Another authorised moderator
                          must authorise release of its outputs.
                        </span>
                      ) : (
                        <button
                          className="btn btn-sm"
                          style={{ background: "var(--color-primary, #1976d2)", color: "#fff", border: "none" }}
                          onClick={() => handleAction(osId, releaseOutputSet)}
                          disabled={actionLoading}
                        >
                          {actionLoading ? "Processing…" : "Release"}
                        </button>
                      )}
                    </div>
                  )}
                </section>
              </div>
            </div>
          </div>
        );
      })()}

      {rejectTarget && (
        <RejectDialog
          title="Output Set"
          onConfirm={async (reason) => {
            setActionError(null);
            setActionLoading(true);
            try {
              await rejectOutputSet(rejectTarget, reason);
              const rejectedId = rejectTarget;
              setRejectTarget(null);
              await load();
              if (expandedId === rejectedId) {
                const updated = await getAdminOutputSet(rejectedId);
                setExpandedData((prev) => ({ ...prev, [rejectedId]: updated }));
                setAiStatus((prev) => ({
                  ...prev,
                  [rejectedId]: updated.ai_review ?? null,
                }));
              }
            } catch (e) {
              setActionError(e instanceof Error ? e.message : "Rejection failed");
            } finally {
              setActionLoading(false);
            }
          }}
          onCancel={() => setRejectTarget(null)}
        />
      )}

      {approveTarget && (
        <ConfirmationDialog
          title="Approve Output Set?"
          message={
            <span>
              This Output Set will be approved for release.
              <br /><br />
              Confirm that you are satisfied the reviewed outputs
              are ready to proceed to the release stage.
              <br /><br />
              <strong>You are making an institutional governance decision.</strong>
            </span>
          }
          confirmLabel="Approve Output Set"
          onConfirm={() => {
            const id = approveTarget;
            setApproveTarget(null);
            handleAction(id, approveOutputSet);
          }}
          onCancel={() => setApproveTarget(null)}
        />
      )}

      {actionError && (
        <div
          style={{
            padding: "8px 12px",
            marginBottom: "var(--spacing-md)",
            background: "#f8d7da",
            color: "#721c24",
            borderRadius: "4px",
            fontSize: "0.85rem",
          }}
        >
          {actionError}
        </div>
      )}
    </>
  );
}
