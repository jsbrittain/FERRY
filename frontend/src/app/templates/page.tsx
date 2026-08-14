"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Template, getTemplates } from "@/lib/api";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);

  const load = useCallback(async () => {
    try {
      const data = await getTemplates();
      setTemplates(data);
    } catch {
      setTemplates([]);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <h1 className="page-title">Bundle Templates</h1>
      <p style={{ color: "var(--color-text-secondary)", marginBottom: "var(--spacing-lg)", lineHeight: 1.6 }}>
        Downloadable bundle templates. Download, customise with your analysis code,
        then upload to FERRY as a new Analysis Bundle.
      </p>

      {templates.length === 0 ? (
        <div className="card empty-state">
          No bundle templates available.
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Environment</th>
                <th>Description</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {templates.map((tpl) => (
                <tr key={tpl.identifier}>
                  <td style={{ fontWeight: 500 }}>
                    <Link
                      href={`/templates/${tpl.identifier}`}
                      style={{ color: "var(--color-primary)", textDecoration: "none" }}
                    >
                      {tpl.name}
                    </Link>
                  </td>
                  <td style={{ color: "var(--color-text-secondary)" }}>
                    {tpl.execution_environment_identifier ? (
                      <Link
                        href={`/environments/${tpl.execution_environment_identifier}`}
                        style={{ color: "var(--color-primary)", textDecoration: "none" }}
                      >
                        {tpl.execution_environment_identifier}
                      </Link>
                    ) : "—"}
                  </td>
                  <td style={{ color: "var(--color-text-secondary)" }}>
                    {tpl.description || "—"}
                  </td>
                  <td>
                    <Link
                      href={`/templates/${tpl.identifier}`}
                      className="btn"
                      style={{ fontSize: "0.85rem", padding: "2px 10px", textDecoration: "none" }}
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
