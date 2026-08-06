export type User = { id: number; email: string; is_admin: boolean };

const BASE_URL = ""; // Vite proxies /api → backend, so a relative path is fine in dev

export async function login(email: string, password: string): Promise<User> {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST", // sending to backend server
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    credentials: "include", // accept + store the httpOnly session cookie the server sets
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Login failed");
  }
  return res.json() as Promise<User>;
}


export async function me(): Promise<User> {
  const res = await fetch(`${BASE_URL}/api/auth/me`, {
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error("Not authenticated");
  }
  return res.json() as Promise<User>;
}

export async function register(email: string, password: string): Promise<User> {
  const res = await fetch(`${BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    credentials: "include",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Registration failed");
  }
  return res.json() as Promise<User>;
}

export async function logout(): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  // 204 No Content — there is no body to parse, so we just confirm it worked.
  if (!res.ok) {
    throw new Error("Logout failed");
  }
}
