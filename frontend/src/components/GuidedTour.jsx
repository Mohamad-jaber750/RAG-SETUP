import { useEffect, useState } from "react";

const STEPS = [
  {
    title: "Welcome to CIS Assistant",
    text: "This quick tour shows you how to start chats, ask questions, and verify every answer.",
    target: ".brand-row",
  },
  {
    title: "Start a fresh thread",
    text: "Create a new conversation without losing your saved chat history.",
    target: ".new-chat",
  },
  {
    title: "Resume previous work",
    text: "Your recent MongoDB-backed conversations live here. Select one to continue it.",
    target: ".history",
  },
  {
    title: "Ask the assistant",
    text: "Enter a CIS Controls question here. The response appears progressively as it is generated.",
    target: ".composer",
  },
  {
    title: "Verify and improve answers",
    text: "Citation badges open source previews. You can also rate or regenerate an answer and switch versions.",
    target: ".conversation",
  },
];

function getTargetRect(selector) {
  const element = document.querySelector(selector);
  if (!element) return null;
  element.scrollIntoView({ behavior: "smooth", block: "center" });
  const rect = element.getBoundingClientRect();
  return {
    top: Math.max(8, rect.top - 8),
    left: Math.max(8, rect.left - 8),
    width: Math.min(window.innerWidth - 16, rect.width + 16),
    height: Math.min(window.innerHeight - 16, rect.height + 16),
  };
}

export default function GuidedTour() {
  const [step, setStep] = useState(() => (localStorage.getItem("cis-tour-complete") ? -1 : 0));
  const [targetRect, setTargetRect] = useState(null);

  useEffect(() => {
    if (step < 0) return undefined;
    const update = () => setTargetRect(getTargetRect(STEPS[step].target));
    const frame = requestAnimationFrame(update);
    window.addEventListener("resize", update);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", update);
    };
  }, [step]);

  if (step < 0) {
    return (
      <button
        className="tour-launcher"
        type="button"
        onClick={() => setStep(0)}
        aria-label="Open guided tour"
        title="Guided tour"
      >
        ?
      </button>
    );
  }

  const finish = () => {
    localStorage.setItem("cis-tour-complete", "true");
    setStep(-1);
  };
  const cardOnLeft = targetRect && targetRect.left > window.innerWidth / 2;
  const cardStyle = targetRect
    ? {
        top: Math.min(targetRect.top, window.innerHeight - 310),
        ...(cardOnLeft
          ? { right: window.innerWidth - targetRect.left + 24 }
          : { left: Math.min(targetRect.left + targetRect.width + 24, window.innerWidth - 380) }),
      }
    : {};

  return (
    <div className="tour-layer" aria-live="polite">
      <div className="tour-shade" />
      {targetRect && <div className="tour-spotlight" style={targetRect} aria-hidden="true" />}
      <aside
        className="tour-card"
        style={cardStyle}
        role="dialog"
        aria-modal="true"
        aria-labelledby="tour-title"
      >
        <span className="tour-count">
          Step {step + 1} of {STEPS.length}
        </span>
        <h2 id="tour-title">{STEPS[step].title}</h2>
        <p>{STEPS[step].text}</p>
        <div className="tour-progress" aria-hidden="true">
          {STEPS.map((item, index) => (
            <i className={index <= step ? "active" : ""} key={item.title} />
          ))}
        </div>
        <div className="tour-actions">
          <button type="button" className="tour-skip" onClick={finish}>
            Skip tour
          </button>
          {step > 0 && (
            <button type="button" onClick={() => setStep(step - 1)}>
              Back
            </button>
          )}
          <button
            className="tour-primary"
            type="button"
            onClick={() => (step === STEPS.length - 1 ? finish() : setStep(step + 1))}
          >
            {step === STEPS.length - 1 ? "Got it" : "Next"}
          </button>
        </div>
      </aside>
    </div>
  );
}
