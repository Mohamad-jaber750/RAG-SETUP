import { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";

export default function Composer({ busy, onSubmit }) {
  const [prompt, setPrompt] = useState("");
  const textarea = useRef(null);

  const submit = (event) => {
    event?.preventDefault();
    if (!busy && prompt.trim()) {
      onSubmit(prompt.trim());
      setPrompt("");
    }
  };

  useEffect(() => {
    textarea.current.style.height = "auto";
    textarea.current.style.height = `${Math.min(textarea.current.scrollHeight, 180)}px`;
  }, [prompt]);

  return (
    <footer className="composer-wrap">
      <form className="composer" onSubmit={submit}>
        <textarea
          ref={textarea}
          rows="1"
          maxLength="4000"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
          placeholder="Message CIS Assistant"
          aria-label="Message"
        />
        <button
          className="send-button"
          disabled={busy || !prompt.trim()}
          type="submit"
          aria-label="Send message"
        >
          ↑
        </button>
      </form>
      <p className="disclaimer">
        Answers are grounded in the indexed CIS Controls document. Check cited sources for accuracy.
      </p>
    </footer>
  );
}

Composer.propTypes = {
  busy: PropTypes.bool.isRequired,
  onSubmit: PropTypes.func.isRequired,
};
