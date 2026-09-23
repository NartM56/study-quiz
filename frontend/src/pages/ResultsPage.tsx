import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import "./NewQuizPage.css";
import "./ResultsPage.css";

interface SessionResult {
  session_id: string;
  total_questions: number;
  answered: number;
  correct: number;
  score_percent: number;
  ended_at: string;
}

export function ResultsPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const hasFetched = useRef(false);

  const [result, setResult] = useState<SessionResult | null>(null);
  const [error, setError] = useState("");
  const [alreadyFinished, setAlreadyFinished] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // guards against React StrictMode's double-invoke in dev, which would
    // otherwise fire this non-idempotent POST twice and hit a real 409
    if (hasFetched.current) return;
    hasFetched.current = true;

    const finishSession = async () => {
      try {
        const data = await api.post<SessionResult>(
          `/quiz/sessions/${sessionId}/finish`,
        );
        setResult(data);
      } catch (err) {
        if (err instanceof ApiError && err.status === 409) {
          setAlreadyFinished(true);
        } else {
          setError(err instanceof Error ? err.message : "Failed to load results");
        }
      } finally {
        setLoading(false);
      }
    };

    finishSession();
  }, [sessionId]);

  if (loading) {
    return (
      <div className="quiz-page">
        <div className="quiz-card">
          <p>Calculating your score...</p>
        </div>
      </div>
    );
  }

  if (alreadyFinished) {
    return (
      <div className="quiz-page">
        <div className="quiz-card">
          <h1>Already completed</h1>
          <p>This quiz has already been scored.</p>
          <button className="quiz-next" onClick={() => navigate("/new-quiz")}>
            New Quiz
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="quiz-page">
        <div className="quiz-card">
          <h1>Something went wrong</h1>
          <p className="quiz-error" role="alert">
            {error}
          </p>
          <button className="quiz-next" onClick={() => navigate("/new-quiz")}>
            New Quiz
          </button>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <div className="quiz-page">
      <div className="quiz-card results-card">
        <h1>Quiz Complete</h1>
        <p className="results-score">{result.score_percent}%</p>
        <p className="results-detail">
          {result.correct} of {result.answered} answered correctly
          {result.answered < result.total_questions
            ? ` (${result.total_questions - result.answered} unanswered)`
            : ""}
        </p>
        <button className="quiz-next" onClick={() => navigate("/new-quiz")}>
          New Quiz
        </button>
      </div>
    </div>
  );
}

export default ResultsPage;
