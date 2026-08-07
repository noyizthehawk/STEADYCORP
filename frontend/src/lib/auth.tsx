// Shared auth state for the whole app. With multiple pages, "who is logged in"
// can't live in one component anymore — the header, the sign-in page, and the
// future Buy button all need it. AuthProvider checks /me once on load and hands
// the current user (and helpers) to any component via the useAuth() hook.

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { logout, me, type User } from "./api";

type AuthValue = {
  user: User | null;
  loading: boolean;
  setUser: (u: User | null) => void;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function signOut() {
    try {
      await logout();
    } finally {
      setUser(null);
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, setUser, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within <AuthProvider>");
  }
  return ctx;
}
