import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import "./NewQuizPage.css";
import "./StatsPage.css";

interface QuizHistoryItem {
  session_id: string;
  topic: string;
  difficulty: number;
  total_questions: number;
  answered: number;
  correct: number;
  score_percent: number;
  started_at: string;
  ended_at: string;
}

interface UserStats {
  total_quizzes: number;
  total_questions_answered: number;
  total_correct: number;
  overall_score_percent: number;
  quizzes: QuizHistoryItem[];
}

export function StatsPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<UserStats>("/quiz/stats")
      .then(setStats)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load stats"),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="quiz-page">
        <div className="quiz-card">
          <p>Loading your stats...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="quiz-page">
        <div className="quiz-card">
          <h1>Couldn't load stats</h1>
          <p className="quiz-error" role="alert">
            {error}
          </p>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="quiz-page">
      <div className="quiz-card stats-card">
        <h1>Your Stats</h1>

        <div className="stats-summary">
          <div className="stats-tile">
            <p className="stats-tile-value">{stats.total_quizzes}</p>
            <p className="stats-tile-label">Quizzes Taken</p>
          </div>
          <div className="stats-tile">
            <p className="stats-tile-value">{stats.overall_score_percent}%</p>
            <p className="stats-tile-label">All-Time Score</p>
          </div>
          <div className="stats-tile">
            <p className="stats-tile-value">{stats.total_questions_answered}</p>
            <p className="stats-tile-label">Questions Answered</p>
          </div>
        </div>

        {stats.quizzes.length === 0 ? (
          <p>You haven't completed any quizzes yet.</p>
        ) : (
          <table className="stats-table">
            <thead>
              <tr>
                <th>Topic</th>
                <th>Difficulty</th>
                <th>Score</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {stats.quizzes.map((quiz) => (
                <tr key={quiz.session_id}>
                  <td>{quiz.topic}</td>
                  <td>{quiz.difficulty}</td>
                  <td>
                    {quiz.score_percent}% ({quiz.correct}/{quiz.answered})
                  </td>
                  <td>{new Date(quiz.started_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <button className="quiz-next" onClick={() => navigate("/new-quiz")}>
          New Quiz
        </button>
      </div>
    </div>
  );
}

export default StatsPage;
