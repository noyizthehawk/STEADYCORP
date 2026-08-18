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

// ── quiz + claim ──

export type QuizQuestion = { id: number; prompt: string; options: string[] };

export type StartQuiz = {
  session_id: number;
  question: QuizQuestion;
  required_correct: number; // K
  total_questions: number; // N
  seconds_per_question: number;
  answered: number;
  correct: number;
};

export type AnswerResult = {
  result: "next" | "passed" | "failed";
  question: QuizQuestion | null; // present only when result === "next"
  answered: number;
  correct: number;
  required_correct: number;
  total_questions: number;
};

export type Claim = {
  number: number;
  title: string;
  image_url: string;
  price_cents: number;
  held_until: string; // naive-UTC ISO from the server
};

// "gone" (a 409) isn't an error — it's a valid game outcome, so we return it.
export type ClaimResult = { status: "won"; brick: Claim } | { status: "gone" };

async function detail(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => ({}));
  return typeof body.detail === "string" ? body.detail : fallback;
}

export async function startQuiz(dropCode: string, number: number): Promise<StartQuiz> {
  const res = await fetch(`${BASE_URL}/api/drops/${dropCode}/bricks/${number}/quiz/start`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error(await detail(res, "Could not start the quiz"));
  return res.json() as Promise<StartQuiz>;
}

export async function answerQuestion(
  sessionId: number,
  choiceIndex: number,
): Promise<AnswerResult> {
  const res = await fetch(`${BASE_URL}/api/quiz/${sessionId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ choice_index: choiceIndex }),
    credentials: "include",
  });
  if (!res.ok) throw new Error(await detail(res, "Answer failed"));
  return res.json() as Promise<AnswerResult>;
}

export async function claimBrick(sessionId: number): Promise<ClaimResult> {
  const res = await fetch(`${BASE_URL}/api/quiz/${sessionId}/claim`, {
    method: "POST",
    credentials: "include",
  });
  if (res.ok) return { status: "won", brick: (await res.json()) as Claim };
  if (res.status === 409) return { status: "gone" }; // won the quiz, lost the race
  throw new Error(await detail(res, "Claim failed"));
}

// ── checkout + collection ──

export type OwnedBrick = { number: number; title: string; image_url: string; price_cents: number };

export async function checkout(sessionId: number): Promise<{ checkout_url: string }> {
  const res = await fetch(`${BASE_URL}/api/quiz/${sessionId}/checkout`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error(await detail(res, "Checkout failed"));
  return res.json() as Promise<{ checkout_url: string }>;
}

export async function getCollection(): Promise<OwnedBrick[]> {
  const res = await fetch(`${BASE_URL}/api/me/bricks`, { credentials: "include" });
  if (!res.ok) throw new Error(await detail(res, "Could not load your collection"));
  return res.json() as Promise<OwnedBrick[]>;
}

// ── admin: drops, bricks, quiz questions ──

export type DropStatus = "draft" | "live" | "closed";

export type Drop = {
  id: number;
  code: string;
  title: string;
  go_live_at: string;
  status: DropStatus;
  created_at: string;
};

export type CreateDropPayload = {
  code: string;
  title: string;
  go_live_at: string;
};

export async function createDrop(payload: CreateDropPayload): Promise<Drop> {
  const res = await fetch(`${BASE_URL}/api/drops`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await detail(res, "Could not create the drop"));
  return res.json() as Promise<Drop>;
}

export async function publishDrop(code: string): Promise<Drop> {
  const res = await fetch(`${BASE_URL}/api/drops/${code}/publish`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error(await detail(res, "Could not publish the drop"));
  return res.json() as Promise<Drop>;
}

export type BrickCreatePayload = {
  number: number;
  title: string;
  image_url: string;
  price_cents: number;
};

export async function createBrick(code: string, payload: BrickCreatePayload): Promise<Brick> {
  const res = await fetch(`${BASE_URL}/api/drops/${code}/bricks`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await detail(res, "Could not create the brick"));
  return res.json() as Promise<Brick>;
}

export type CreateQuestionPayload = {
  prompt: string;
  options: string[];
  correct_index: number;
  category?: string | null;
  drop_id?: number | null;
};

export type AdminQuizQuestion = {
  id: number;
  prompt: string;
  options: string[];
  correct_index: number;
  category: string | null;
  drop_id: number | null;
};

export async function createQuizQuestion(
  payload: CreateQuestionPayload,
): Promise<AdminQuizQuestion> {
  const res = await fetch(`${BASE_URL}/api/quiz/questions`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await detail(res, "Could not create the question"));
  return res.json() as Promise<AdminQuizQuestion>;
}

