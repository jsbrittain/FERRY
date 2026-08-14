"use client";

import Link from "next/link";

const docs = [
  {
    slug: "getting-started",
    title: "Getting Started",
    description: "Overview of the FERRY research platform and how to begin.",
  },
  {
    slug: "bundle-structure",
    title: "Bundle Structure",
    description: "How to structure an Analysis Bundle for submission.",
  },
  {
    slug: "local-development",
    title: "Local Development",
    description: "Develop and test Analysis Bundles locally before submission.",
  },
  {
    slug: "submission-workflow",
    title: "Submission Workflow",
    description: "The end-to-end workflow from draft to approved output release.",
  },
  {
    slug: "governance-overview",
    title: "Governance Overview",
    description: "How institutional governance applies to your research.",
  },
];

export default function DocsIndexPage() {
  return (
    <>
      <h1 className="page-title">Researcher Documentation</h1>
      <p style={{ color: "var(--color-text-secondary)", marginBottom: "var(--spacing-lg)", lineHeight: 1.6 }}>
        Guidance for using the FERRY research platform. Topics link to institutional
        publications rather than duplicating them.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-md)" }}>
        {docs.map((doc) => (
          <div key={doc.slug} className="card">
            <Link
              href={`/docs/${doc.slug}`}
              style={{ color: "var(--color-primary)", textDecoration: "none", fontSize: "1rem", fontWeight: 600 }}
            >
              {doc.title}
            </Link>
            <p style={{ color: "var(--color-text-secondary)", marginTop: "var(--spacing-xs)", lineHeight: 1.5 }}>
              {doc.description}
            </p>
          </div>
        ))}
      </div>
    </>
  );
}
