import { type FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { login, register } from "../lib/api";
import { useAuth } from "../lib/auth";

type Mode = "login" | "register";

export default function SignIn() {
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // where to go after auth: the page they came from (else the landing)
  const cameFrom = (location.state as { from?: string } | null)?.from;
  const returnTo = cameFrom && cameFrom !== "/signin" ? cameFrom : "/";

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
      setUser(await call(email, password));
      navigate(returnTo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setPending(false);
    }
  }

  const field =
    "w-full border border-black bg-transparent px-3 py-2 normal-case outline-none placeholder:text-black";

  return (
    <form onSubmit={submit} className="w-full max-w-sm space-y-4">
      <div className="flex gap-2">
        {(["login", "register"] as Mode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => {
              setMode(m);
              setError(null);
            }}
            className={m === mode ? "bg-black px-2 py-1 text-white" : "lnk"}
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

      {error && <p className="text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={pending}
        className="w-full border border-black bg-black px-2 py-2 text-white transition-colors hover:bg-white hover:text-black disabled:opacity-40"
      >
        {pending ? "…" : mode === "login" ? "ENTER" : "CREATE"}
      </button>
    </form>
  );
}
