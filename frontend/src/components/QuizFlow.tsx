import { useCallback, useEffect, useState } from "react";

import {
  answerQuestion,
  type Claim,
  claimBrick,
  type QuizQuestion,
  startQuiz,
} from "../lib/api";

type Phase =
  | "loading"
  | "question"
  | "answering"
  | "claiming"
  | "won"
  | "gone"
  | "failed"
  | "error";

// Live countdown to the hold deadline. Server sends naive UTC, so append "Z".
function HoldClock({ until }: { until: string }) {
  const target = new Date(until.endsWith("Z") ? until : until + "Z").getTime();
  const [left, setLeft] = useState(() => Math.max(0, Math.floor((target - Date.now()) / 1000)));
  useEffect(() => {
    const id = setInterval(
      () => setLeft(Math.max(0, Math.floor((target - Date.now()) / 1000))),
      1000,
    );
    return () => clearInterval(id);
  }, [target]);
  const mm = String(Math.floor(left / 60)).padStart(2, "0");
  const ss = String(left % 60).padStart(2, "0");
  return (
    <span>
      {mm}:{ss}
    </span>
  );
}

export default function QuizFlow({
  dropCode,
  number,
  onExit,
}: {
  dropCode: string;
  number: number;
  onExit: () => void;
}) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [question, setQuestion] = useState<QuizQuestion | null>(null);
  const [progress, setProgress] = useState({ answered: 0, correct: 0, required: 0, total: 0 });
  const [seconds, setSeconds] = useState(10);
  const [timeLeft, setTimeLeft] = useState(10);
  const [claim, setClaim] = useState<Claim | null>(null);
  const [message, setMessage] = useState("");

  const start = useCallback(async () => {
    setPhase("loading");
    setClaim(null);
    try {
      const s = await startQuiz(dropCode, number);
      setSessionId(s.session_id);
      setQuestion(s.question);
      setProgress({
        answered: s.answered,
        correct: s.correct,
        required: s.required_correct,
        total: s.total_questions,
      });
      setSeconds(s.seconds_per_question);
      setTimeLeft(s.seconds_per_question);
      setPhase("question");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Something went wrong");
      setPhase("error");
    }
  }, [dropCode, number]);

  useEffect(() => {
    start();
  }, [start]);

  const submit = useCallback(
    async (choiceIndex: number) => {
      if (sessionId === null) return;
      setPhase("answering");
      try {
        const a = await answerQuestion(sessionId, choiceIndex);
        setProgress({
          answered: a.answered,
          correct: a.correct,
          required: a.required_correct,
          total: a.total_questions,
        });
        if (a.result === "next" && a.question) {
          setQuestion(a.question);
          setTimeLeft(seconds);
          setPhase("question");
        } else if (a.result === "passed") {
          setPhase("claiming");
          const c = await claimBrick(sessionId);
          if (c.status === "won") {
            setClaim(c.brick);
            setPhase("won");
          } else {
            setPhase("gone");
          }
        } else {
          setPhase("failed");
        }
      } catch (e) {
        setMessage(e instanceof Error ? e.message : "Something went wrong");
        setPhase("error");
      }
    },
    [sessionId, seconds],
  );

  // Per-question countdown; hitting 0 submits an out-of-range index → counts wrong.
  useEffect(() => {
    if (phase !== "question") return;
    if (timeLeft <= 0) {
      submit(question ? question.options.length : 0);
      return;
    }
    const id = setTimeout(() => setTimeLeft((t) => t - 1), 1000);
    return () => clearTimeout(id);
  }, [phase, timeLeft, submit, question]);

  const wrap = "w-full max-w-md space-y-6 text-center";

  if (phase === "loading" || phase === "claiming") {
    return (
      <div className={wrap}>
        <p className="text-neutral-500">…</p>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className={wrap}>
        <p className="uppercase">{message}</p>
        <button onClick={onExit} className="lnk">
          BACK
        </button>
      </div>
    );
  }

  if (phase === "failed") {
    return (
      <div className={wrap}>
        <p className="uppercase">Failed — {progress.correct} of {progress.required}</p>
        <div className="flex justify-center gap-4">
          <button onClick={start} className="bg-black px-4 py-2 uppercase text-white">
            Try again
          </button>
          <button onClick={onExit} className="lnk">
            BACK
          </button>
        </div>
      </div>
    );
  }

  if (phase === "gone") {
    return (
      <div className={wrap}>
        <p className="uppercase tracking-[0.2em]">GONE</p>
        <p className="text-neutral-500">Someone claimed it first.</p>
        <button onClick={onExit} className="lnk">
          BACK
        </button>
      </div>
    );
  }

  if (phase === "won" && claim) {
    return (
      <div className="w-full max-w-md space-y-5 text-center">
        <p className="uppercase tracking-[0.2em]">You got it</p>
        <img src={claim.image_url} alt={claim.title} className="w-full border border-black" />
        <div className="uppercase">
          #{String(claim.number).padStart(2, "0")} · {claim.title}
        </div>
        <div className="uppercase text-neutral-500">
          Pay within <HoldClock until={claim.held_until} /> — ${(claim.price_cents / 100).toFixed(2)}
        </div>
        <button
          disabled
          className="w-full border border-black px-4 py-2 uppercase opacity-40"
          title="Stripe checkout coming next"
        >
          Checkout — coming soon
        </button>
        <button onClick={onExit} className="lnk">
          ← BACK
        </button>
      </div>
    );
  }

  // phase === "question" | "answering"
  const answering = phase === "answering";
  return (
    <div className="w-full max-w-md space-y-6">
      <div className="flex items-center justify-between uppercase text-neutral-500">
        <span>
          {progress.correct} / {progress.required} correct
        </span>
        <span>{timeLeft}s</span>
      </div>
      <div className="h-1 w-full bg-neutral-200">
        <div className="h-1 bg-black" style={{ width: `${(timeLeft / seconds) * 100}%` }} />
      </div>

      <p className="uppercase">{question?.prompt}</p>

      <div className="space-y-3">
        {question?.options.map((opt, i) => (
          <button
            key={i}
            disabled={answering}
            onClick={() => submit(i)}
            className="w-full border border-black px-3 py-2 text-left uppercase transition-colors hover:bg-black hover:text-white disabled:opacity-40"
          >
            {opt}
          </button>
        ))}
      </div>

      <button onClick={onExit} className="lnk">
        ← GIVE UP
      </button>
    </div>
  );
}
