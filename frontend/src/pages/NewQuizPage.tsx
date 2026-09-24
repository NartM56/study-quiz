import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import "./NewQuizPage.css";

interface QuestionOption {
  id: string;
  text: string;
}

interface QuestionOut {
  question_id: string;
  body: string;
  options: QuestionOption[];
}

interface SessionCreateResponse {
  session_id: string;
  topic: string;
  difficulty: number;
  questions: QuestionOut[];
}

export function NewQuizPage() {
  const [quizTopic, setQuizTopic] = useState("");
  const [quizDifficulty, setQuizDifficulty] = useState("");
  const [questionAmount, setQuestionAmount] = useState<number | undefined>(
    undefined,
  );
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError("");

    try {
      const data = await api.post<SessionCreateResponse>("/quiz/sessions", {
        topic: quizTopic,
        difficulty: Number(quizDifficulty),
        question_count: questionAmount,
      });
      console.log("Quiz created:", data);
      navigate(`/quiz/${data.session_id}`, {
        state: { questions: data.questions },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create quiz");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="quiz-page">
      <div className="quiz-card">
        <h1>New Quiz</h1>
        <form className="quiz-form" onSubmit={handleSubmit}>
          <label>
            Quiz Topic
            <input
              type="text"
              value={quizTopic}
              onChange={(e) => setQuizTopic(e.target.value)}
              placeholder="e.g. Photosynthesis"
              required
            />
          </label>

          <label>
            Quiz Difficulty
            <select
              value={quizDifficulty}
              onChange={(e) => setQuizDifficulty(e.target.value)}
              required
            >
              <option value="" disabled>
                Select difficulty
              </option>
              <option value="1">1 - Very Easy</option>
              <option value="2">2 - Easy</option>
              <option value="3">3 - Medium</option>
              <option value="4">4 - Hard</option>
              <option value="5">5 - Very Hard</option>
            </select>
          </label>

          <label>
            Question Amount
            <input
              type="number"
              value={questionAmount ?? ""}
              onChange={(e) => setQuestionAmount(Number(e.target.value))}
              min={1}
              max={20}
              placeholder="Up to 20"
              required
            />
          </label>

          {error && (
            <p className="quiz-error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" disabled={creating}>
            {creating ? "Creating..." : "Create Quiz"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default NewQuizPage;
