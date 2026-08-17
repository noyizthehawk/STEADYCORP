import { type FormEvent, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import QuizFlow from "../components/QuizFlow";
import { type Brick, getBrick, parseBrickCode } from "../lib/api";
import { useAuth } from "../lib/auth";

type Target = { dropCode: string; number: number };

// The store IS the gate: type a code, see the brick, buy it (quiz → claim).
export default function Store() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [code, setCode] = useState("");
  const [brick, setBrick] = useState<Brick | null>(null);
  const [target, setTarget] = useState<Target | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [phase, setPhase] = useState<"browse" | "quiz">("browse");

  // Restore the brick from ?b=DROP01-7 — set when a signed-out Buy sends the
  // user through sign-in, so they land back on their brick instead of an empty
  // box. Also makes a brick a shareable/refreshable deep link.
  useEffect(() => {
    const parsed = parseBrickCode(searchParams.get("b") ?? "");
    if (!parsed) return; // no param, or garbage — just show the empty box
    setCode(`${parsed.dropCode}-${parsed.number}`);
    setPending(true);
    getBrick(parsed.dropCode, parsed.number)
      .then((b) => {
        setBrick(b);
        setTarget(parsed);
      })
      .catch(() => setError("Nothing here."))
      .finally(() => setPending(false));
  }, [searchParams]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBrick(null);
    setTarget(null);

    const parsed = parseBrickCode(code);
    if (!parsed) {
      setError("Nothing here.");
      return;
    }
    setPending(true);
    try {
      setBrick(await getBrick(parsed.dropCode, parsed.number));
      setTarget(parsed);
    } catch {
      setError("Nothing here.");
    } finally {
      setPending(false);
    }
  }

  function onBuy() {
    if (!user) {
      // carry the brick through sign-in so they return to it, not an empty store
      const from = target ? `/store?b=${target.dropCode}-${target.number}` : "/store";
      navigate("/signin", { state: { from } }); // login required to claim
      return;
    }
    setPhase("quiz");
  }

  async function backToBrowse() {
    setPhase("browse");
    if (target) {
      try {
        setBrick(await getBrick(target.dropCode, target.number)); // refresh the status
      } catch {
        /* leave the last view as-is */
      }
    }
  }

  if (phase === "quiz" && target) {
    return <QuizFlow dropCode={target.dropCode} number={target.number} onExit={backToBrowse} />;
  }

  const price = brick ? `$${(brick.price_cents / 100).toFixed(2)}` : "";
  const gone = brick ? brick.status !== "available" : false;

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

      {pending && <p className="text-center text-neutral-500">…</p>}
      {error && !pending && <p className="text-center uppercase text-neutral-500">{error}</p>}

      {brick && !pending && (
        <div className="space-y-4">
          <div className="relative">
            <img
              src={brick.image_url}
              alt={brick.title}
              className={`w-full border border-black ${gone ? "opacity-40" : ""}`}
            />
            {gone && (
              <span className="absolute inset-0 flex items-center justify-center tracking-[0.2em]">
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
          {!gone && (
            <button
              onClick={onBuy}
              className="w-full border border-black bg-black px-4 py-2 uppercase text-white transition-colors hover:bg-white hover:text-black"
            >
              Buy
            </button>
          )}
        </div>
      )}
    </div>
  );
}
