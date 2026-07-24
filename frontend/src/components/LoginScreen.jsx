import { startGoogleLogin } from "../services/authApi";
import PropTypes from "prop-types";

export default function LoginScreen({ error }) {
  return (
    <main className="login-screen">
      <section className="login-card">
        <div className="hero-mark login-mark">C</div>
        <p className="login-kicker">SECURE RAG GATEWAY</p>
        <h1>CIS Controls Assistant</h1>
        <p>
          Sign in with Google to use the RAG assistant through the protected middleware API. Python
          RAG credentials stay server-side.
        </p>
        {error && <div className="error-box">{error}</div>}
        <button className="google-login" onClick={startGoogleLogin}>
          <span>G</span>
          Sign in with Google
        </button>
      </section>
    </main>
  );
}

LoginScreen.propTypes = {
  error: PropTypes.string,
};
