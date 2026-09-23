import { Link, useLocation } from "react-router-dom";
import "./Header.css";

export function Header() {
  // useLocation's return value changes on every navigation, which forces
  // this component to re-render and re-check localStorage — there's no
  // reactive auth state (context) yet, so this is what keeps the nav in sync
  useLocation();
  const isLoggedIn = Boolean(localStorage.getItem("access_token"));

  return (
    <header className="app-header">
      <Link to={isLoggedIn ? "/new-quiz" : "/login"} className="app-header-logo">
        MindLoop
      </Link>
      {isLoggedIn && (
        <nav className="app-header-nav">
          <Link to="/new-quiz">New Quiz</Link>
          <Link to="/stats">Stats</Link>
        </nav>
      )}
    </header>
  );
}

export default Header;
