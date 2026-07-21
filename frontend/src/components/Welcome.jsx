import { suggestions } from "../data/previewMessages";

export default function Welcome({ onAsk }) {
  return <div className="welcome">
    <div className="hero-mark">C</div>
    <h1>How can I help?</h1>
    <p>Ask anything about the CIS Critical Security Controls v8.</p>
    <div className="suggestions">{suggestions.map(text => <button key={text} onClick={() => onAsk(text)}>{text}</button>)}</div>
  </div>;
}
