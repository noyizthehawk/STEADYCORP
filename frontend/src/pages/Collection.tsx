import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { getCollection, type OwnedBrick } from "../lib/api";

export default function Collection() {
  const [bricks, setBricks] = useState<OwnedBrick[] | null>(null);
  const [params] = useSearchParams();
  const justPaid = params.get("paid") === "1";

  useEffect(() => {
    getCollection()
      .then(setBricks)
      .catch(() => setBricks([]));
  }, []);

  if (bricks === null) {
    return <p className="text-neutral-500">…</p>;
  }

  return (
    <div className="w-full max-w-md space-y-6">
      {justPaid && <p className="uppercase tracking-[0.2em]">Payment received</p>}
      <p className="uppercase tracking-[0.2em] text-neutral-500"></p>
      {bricks.length === 0 ? (
        <p className="uppercase text-neutral-500">Nothing yet. Go get one!</p>
      ) : (
        bricks.map((b, i) => (
          <div key={i} className="space-y-2">
            <img src={b.image_url} alt={b.title} className="w-full border border-black" />
            <div className="flex justify-between uppercase">
              <span>
                #{String(b.number).padStart(2, "0")} · {b.title}
              </span>
              <span>${(b.price_cents / 100).toFixed(2)}</span>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
