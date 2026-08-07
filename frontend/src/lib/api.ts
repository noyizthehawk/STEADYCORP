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

export type BrickStatus = "available" | "held" | "sold";

export type Brick = {
  number: number;
  title: string;
  image_url: string;
  price_cents: number;
  status: BrickStatus;
};

// Turn a typed code into { dropCode, number }. Forgiving: uppercases and
// tolerates any separator — "DROP01/BRICK07", "drop01 7", "DROP01-BRICK7".
export function parseBrickCode(input: string): { dropCode: string; number: number } | null {
  const m = input.trim().toUpperCase().match(/^(DROP\d+)\D+(\d+)$/);
  return m ? { dropCode: m[1], number: Number(m[2]) } : null;
}

export async function getBrick(dropCode: string, number: number): Promise<Brick> {
  const res = await fetch(`${BASE_URL}/api/drops/${dropCode}/bricks/${number}`, {
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error("Nothing here.");
  }
  return res.json() as Promise<Brick>;
}
