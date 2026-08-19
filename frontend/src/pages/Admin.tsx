import { type FormEvent, useState } from "react";

import {
  createBrick,
  createDrop,
  createQuizQuestion,
  publishDrop,
  type CreateDropPayload,
} from "../lib/api";
import { useAuth } from "../lib/auth";


const field =
  "w-full border border-black bg-transparent px-3 py-2 normal-case outline-none placeholder:text-black";

const submitBtn =
  "w-full border border-black bg-black px-2 py-2 text-white transition-colors hover:bg-white hover:text-black disabled:opacity-40";

const sectionLabel = "uppercase tracking-[0.2em] text-neutral-500";


export default function Admin() {
  const { user, loading } = useAuth();
  if (loading) return <p>…</p>;
  if (!user?.is_admin) return <p>Admins only.</p>;

  return (
    <div className="w-full max-w-md space-y-8">
      <p className={sectionLabel}>Admin</p>
      <CreateDropForm />
      <CreateBrickForm />
      <PublishDropForm />
      <CreateQuestionForm />
    </div>
  );
}

// create a drop

const initialDropForm: CreateDropPayload = { code: "", title: "", go_live_at: "" };

function CreateDropForm() {
  const [form, setForm] = useState<CreateDropPayload>(initialDropForm);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setPending(true);
    try {
      const drop = await createDrop({
        ...form,
        go_live_at: new Date(form.go_live_at).toISOString(),
      });
      setSuccess(`Created "${drop.code}" as a draft.`);
      setForm(initialDropForm);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the drop");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <p className={sectionLabel}>Create drop</p>

      <input
        value={form.code}
        onChange={(e) => setForm({ ...form, code: e.target.value })}
        placeholder="code (e.g. DROP02)"
        required
        className={field}
      />
      <input
        value={form.title}
        onChange={(e) => setForm({ ...form, title: e.target.value })}
        placeholder="title"
        required
        className={field}
      />
      <input
        type="datetime-local"
        value={form.go_live_at}
        onChange={(e) => setForm({ ...form, go_live_at: e.target.value })}
        required
        className={field}
      />

      {error && <p className="text-red-600">{error}</p>}
      {success && <p className="uppercase text-neutral-500">{success}</p>}

      <button type="submit" disabled={pending} className={submitBtn}>
        {pending ? "…" : "Create drop"}
      </button>
    </form>
  );
}


function PublishDropForm() {
  const [code, setCode] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setPending(true);
    try {
      const drop = await publishDrop(code);
      setSuccess(`${drop.code} is now ${drop.status}.`);
      setCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not publish the drop");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <p className={sectionLabel}>Publish drop</p>

      <input
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="drop code (e.g. DROP02)"
        required
        className={field}
      />

      {error && <p className="text-red-600">{error}</p>}
      {success && <p className="uppercase text-neutral-500">{success}</p>}

      <button type="submit" disabled={pending} className={submitBtn}>
        {pending ? "…" : "Publish drop"}
      </button>
    </form>
  );
}

// ── add brick ──

// All strings — this mirrors what the <input>s produce, NOT BrickCreatePayload
// (whose number/price_cents are real numbers). We convert at submit time.
type BrickFormState = {
  dropCode: string;
  number: string;
  title: string;
  image_url: string;
  price: string; // dollars, not cents — same idea as go_live_at
};

const initialBrickForm: BrickFormState = {
  dropCode: "",
  number: "",
  title: "",
  image_url: "",
  price: "",
};

function CreateBrickForm() {
  const [form, setForm] = useState<BrickFormState>(initialBrickForm);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSuccess(null);
    setError(null);
    setPending(true);
    try {
      // Build the API payload FROM the form: dropCode is a separate arg, and
      // number/price get converted from strings to the numbers the backend wants.
      const brick = await createBrick(form.dropCode, {
        number: Number(form.number),
        title: form.title,
        image_url: form.image_url,
        price_cents: Math.round(parseFloat(form.price) * 100),
      });
      setSuccess(`Added brick #${brick.number} to ${form.dropCode}.`);
      setForm(initialBrickForm);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the brick");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <p className={sectionLabel}>Add brick</p>

      <input
        value={form.dropCode}
        onChange={(e) => setForm({ ...form, dropCode: e.target.value })}
        placeholder="drop code (e.g. DROP02)"
        required
        className={field}
      />
      <input
        type="number"
        value={form.number}
        onChange={(e) => setForm({ ...form, number: e.target.value })}
        placeholder="number (1–20)"
        required
        className={field}
      />
      <input
        value={form.title}
        onChange={(e) => setForm({ ...form, title: e.target.value })}
        placeholder="title"
        required
        className={field}
      />
      <input
        value={form.image_url}
        onChange={(e) => setForm({ ...form, image_url: e.target.value })}
        placeholder="image URL"
        required
        className={field}
      />
      <input
        type="number"
        step="0.01"
        value={form.price}
        onChange={(e) => setForm({ ...form, price: e.target.value })}
        placeholder="price in dollars (e.g. 50.00)"
        required
        className={field}
      />

      {error && <p className="text-red-600">{error}</p>}
      {success && <p className="uppercase text-neutral-500">{success}</p>}

      <button type="submit" disabled={pending} className={submitBtn}>
        {pending ? "…" : "Add brick"}
      </button>
    </form>
  );
}


type QuestionFormState = {
  prompt: string;
  options: string[];
  correctIndex: number;
  category: string;
};

const initialQuestionForm: QuestionFormState = {
  prompt: "",
  options: ["", "", "", ""],
  correctIndex: 0,
  category: "",
};

function CreateQuestionForm() {
  const [form, setForm] = useState<QuestionFormState>(initialQuestionForm);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Update a single option without mutating the array in place: copy it, change
  // the one slot, hand the new array back to setForm.
  function setOption(index: number, value: string) {
    const next = [...form.options];
    next[index] = value;
    setForm({ ...form, options: next });
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSuccess(null);
    setError(null);
    setPending(true);
    try {
      const q = await createQuizQuestion({
        prompt: form.prompt,
        options: form.options,
        correct_index: form.correctIndex,
        category: form.category || null, // "" → null (no category)
      });
      setSuccess(`Added question #${q.id}.`);
      setForm(initialQuestionForm);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the question");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <p className={sectionLabel}>Add question</p>

      <input
        value={form.prompt}
        onChange={(e) => setForm({ ...form, prompt: e.target.value })}
        placeholder="prompt"
        required
        className={field}
      />

      {form.options.map((opt, i) => (
        <label key={i} className="flex items-center gap-2">
          <input
            type="radio"
            name="correct" // shared name = only one radio can be checked at a time
            checked={form.correctIndex === i}
            onChange={() => setForm({ ...form, correctIndex: i })}
          />
          <input
            value={opt}
            onChange={(e) => setOption(i, e.target.value)}
            placeholder={`option ${i + 1}`}
            required
            className={field}
          />
        </label>
      ))}

      <input
        value={form.category}
        onChange={(e) => setForm({ ...form, category: e.target.value })}
        placeholder="category (optional)"
        className={field}
      />

      {error && <p className="text-red-600">{error}</p>}
      {success && <p className="uppercase text-neutral-500">{success}</p>}

      <button type="submit" disabled={pending} className={submitBtn}>
        {pending ? "…" : "Add question"}
      </button>
    </form>
  );
}
