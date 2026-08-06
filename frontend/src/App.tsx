import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import { login, logout, me, register, type User } from "./lib/api";

function Shell({ children }: { children: ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-black px-6 text-white">
      <div className="w-full max-w-sm">
        <h1 className="mb-10 text-center font-mono text-sm tracking-[0.4em] text-neutral-400">
          STEADYCORP
        </h1>
        {children}
      </div>
    </main>
  );
}

type Mode = "login" | "register";

function AuthForm({ onAuthed }: { onAuthed: (u: User) => void }) {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      const call = mode === "login" ? login : register;
      onAuthed(await call(email, password));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setPending(false);
    }
  }

  const field =
    "w-full border border-neutral-800 bg-transparent px-3 py-2 font-mono text-sm " +
    "outline-none placeholder:text-neutral-600 focus:border-neutral-500";

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="flex gap-6 font-mono text-xs tracking-widest">
        {(["login", "register"] as Mode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => {
              setMode(m);
              setError(null);
            }}
            className={m === mode ? "text-white" : "text-neutral-600 hover:text-neutral-400"}
          >
            {m.toUpperCase()}
          </button>
        ))}
      </div>

      <input
        type="email"
        required
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="email"
        className={field}
      />
      <input
        type="password"
        required
        minLength={mode === "register" ? 8 : undefined}
        autoComplete={mode === "login" ? "current-password" : "new-password"}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="password"
        className={field}
      />

      {error && <p className="font-mono text-xs text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={pending}
        className="w-full bg-white py-2 font-mono text-xs tracking-widest text-black disabled:opacity-40"
      >
        {pending ? "…" : mode === "login" ? "ENTER" : "CREATE"}
      </button>
    </form>
  );
}

function Account({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [pending, setPending] = useState(false);

  async function handleLogout() {
    setPending(true);
    try {
      await logout();
    } finally {
      onLogout();
    }
  }

  return (
    <div className="space-y-6 text-center">
      <div className="font-mono text-xs tracking-widest text-neutral-500">YOU&apos;RE IN</div>
      <div className="font-mono text-sm">{user.email}</div>
      {user.is_admin && (
        <div className="inline-block border border-neutral-700 px-2 py-1 font-mono text-[10px] tracking-widest text-neutral-400">
          ADMIN
        </div>
      )}
      <button
        onClick={handleLogout}
        disabled={pending}
        className="block w-full border border-neutral-800 py-2 font-mono text-xs tracking-widest text-neutral-400 hover:text-white disabled:opacity-40"
      >
        {pending ? "…" : "LOG OUT"}
      </button>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Shell>
      {loading ? (
        <p className="text-center font-mono text-xs tracking-widest text-neutral-600">…</p>
      ) : user ? (
        <Account user={user} onLogout={() => setUser(null)} />
      ) : (
        <AuthForm onAuthed={setUser} />
      )}
    </Shell>
  );
}
