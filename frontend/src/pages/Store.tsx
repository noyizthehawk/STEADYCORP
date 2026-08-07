import { type FormEvent, useState } from "react";

import { type Brick, getBrick, parseBrickCode } from "../lib/api";

function BrickCard({ brick }: { brick: Brick }) {
  const price = `$${(brick.price_cents / 100).toFixed(2)}`;
  const gone = brick.status !== "available";
  return (
    <div className="space-y-4">
      <div className="relative">
        <img
          src={brick.image_url}
          alt={brick.title}
          className={`w-full border border-black ${gone ? "opacity-40" : ""}`}
        />
        {gone && (
          <span className="absolute inset-0 flex items-center justify-center">
            {brick.status === "sold" ? "GONE" : "HELD"}
          </span>
        )}
      </div>
      <div className="flex items-center justify-between uppercase">
        <span>
          #{String(brick.number).padStart(2, "0")} · {brick.title}
        </span>
        <span>{price}</span>
      </div>
    </div>
  );
}

// The store IS the gate: type a code, see the brick. Public — no login needed.
export default function Store() {
  const [code, setCode] = useState("");
  const [brick, setBrick] = useState<Brick | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBrick(null);

    const parsed = parseBrickCode(code);
    if (!parsed) {
      setError("Nothing here.");
      return;
    }

    setPending(true);
    try {
      setBrick(await getBrick(parsed.dropCode, parsed.number));
    } catch {
      setError("Nothing here.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="w-full max-w-md space-y-8">
      <form onSubmit={submit}>
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="WHAT BRICK DO YOU WANT?"
          autoFocus
          className="w-full border-b border-black bg-transparent py-3 text-center uppercase outline-none placeholder:text-black"
        />
      </form>

      {pending && <p className="text-center">…</p>}
      {error && !pending && <p className="text-center uppercase">{error}</p>}
      {brick && !pending && <BrickCard brick={brick} />}
    </div>
  );
}
