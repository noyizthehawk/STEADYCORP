import { useEffect, useState } from "react";

import { getDrops, getDropBricks, type Brick, type Drop } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function Dropadmin() {
  const { user, loading } = useAuth();

  // all the drops in the db (null = haven't loaded yet)
  const [drops, setDrops] = useState<Drop[] | null>(null);
  // which drop's bricks are currently expanded
  const [openCode, setOpenCode] = useState<string | null>(null);
  // bricks for the currently-open drop
  const [bricks, setBricks] = useState<Brick[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // fetch the list of drops once, when the page loads
  useEffect(() => {
    getDrops()
      .then(setDrops)
      .catch(() => setDrops([]));
  }, []);

  // TODO: a handler that, when a drop is clicked, sets openCode and loads its
  // bricks via getDropBricks(code) → setBricks(...)

  // guard
  if (loading) return <p>…</p>;
  if (!user?.is_admin) return <p>Admins only.</p>;

  function handleDropClick(code: string) {
    // click the open drop again → close it
    if (openCode === code) {
      setOpenCode(null);
      return;
    }
    setOpenCode(code);
    setBricks(null); // clear the previous drop's bricks so we show a loader, not stale data
    setError(null);
    getDropBricks(code)
      .then(setBricks)
      .catch(() => setError("Could not load bricks"));
  }

  if (drops === null) return <p className="text-neutral-500">…</p>;

  return (
    <div className="w-full max-w-md space-y-6">
      <p className="uppercase tracking-[0.2em] text-neutral-500">Drops</p>

      {error && <p className="text-red-600">{error}</p>}

      {drops.length === 0 ? (
        <p className="uppercase text-neutral-500">No drops yet.</p>
      ) : (
        drops.map((drop) => (
          <div key={drop.code} className="space-y-3">
            {/* the drop row — click to expand/collapse its bricks */}
            <button
              onClick={() => handleDropClick(drop.code)}
              className="flex w-full items-center justify-between border border-black px-3 py-2 uppercase transition-colors hover:bg-black hover:text-white"
            >
              <span>
                {drop.code} · {drop.title}
              </span>
              <span className="text-neutral-500">{drop.status}</span>
            </button>

            {/* bricks show only for the open drop */}
            {openCode === drop.code && (
              <div className="space-y-2 pl-3">
                {bricks === null ? (
                  <p className="text-neutral-500">…</p>
                ) : bricks.length === 0 ? (
                  <p className="uppercase text-neutral-500">No bricks yet.</p>
                ) : (
                  bricks.map((brick) => (
                    <div
                      key={brick.number}
                      className="flex items-center justify-between uppercase text-sm"
                    >
                      <span>
                        #{String(brick.number).padStart(2, "0")} · {brick.title}
                      </span>
                      <span className="text-neutral-500">{brick.status}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}
