"use client";

import { useAuth } from "@/lib/AuthContext";
import styles from "./Header.module.css";

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className={styles.header}>
      <span className={styles.brand}>FERRY</span>
      <div className={styles.user}>
        {user ? (
          <>
            <button
              onClick={logout}
              style={{
                background: "none",
                border: "none",
                color: "var(--color-text-secondary)",
                cursor: "pointer",
                fontSize: "0.85rem",
                marginRight: "var(--spacing-sm)",
              }}
            >
              Sign out
            </button>
            <span data-testid="header-user-name">{user.display_name}</span>
            <div className={styles.avatar}>
              {user.display_name.charAt(0).toUpperCase()}
            </div>
          </>
        ) : (
          <span>Loading…</span>
        )}
      </div>
    </header>
  );
}
