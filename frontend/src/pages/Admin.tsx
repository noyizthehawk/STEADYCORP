import { type FormEvent, useState } from "react";
import { useAuth } from "../lib/auth";
import { createDrop, publishDrop, createBrick, createQuizQuestion, type CreateDropPayload } from "../lib/api";


const initialForm: CreateDropPayload = {
    code: "",
    title: "",
    go_live_at: "",
  };
export default function Admin() {
    const [form, setForm] = useState<CreateDropPayload>(initialForm);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [pending, setPending] = useState(false);
    const { user, loading } = useAuth();
    if (loading) return <p>…</p>;
    if  (!user?.is_admin) return <p>Admins only.</p>;

    async function submit(e: FormEvent ){
        e.preventDefault();
        setError(null);
        setSuccess(null);
        setPending(true);
        try{
            const drop = await createDrop({
                ...form,
                go_live_at: new Date(form.go_live_at).toISOString(),
            });
            setSuccess(`Created "${drop.code}" as a draft.`);
            setForm(initialForm); // set to intiial form
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Something went wrong, couldnt create drop");
        }
        finally {
            setPending(false);
        }
    }
    const field =
    "w-full border border-black bg-transparent px-3 py-2 normal-case outline-none placeholder:text-black";

  return (
    <div className="w-full max-w-md space-y-8">
      <p className="uppercase tracking-[0.2em] text-neutral-500">Admin</p>

      <form onSubmit={submit} className="space-y-4">
        <p className="uppercase tracking-[0.2em] text-neutral-500">Create drop</p>

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

        <button
          type="submit"
          disabled={pending}
          className="w-full border border-black bg-black px-2 py-2 text-white transition-colors hover:bg-white hover:text-black disabled:opacity-40"
        >
          {pending ? "…" : "Create drop"}
        </button>
      </form>
    </div>
  );

    
     



}
    