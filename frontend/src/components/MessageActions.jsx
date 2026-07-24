import { useState } from "react";
import PropTypes from "prop-types";
import { messagePropType } from "@/shared/propTypes";

const REASONS = ["Helpful", "Accurate", "Clear", "Not accurate", "Not relevant", "Missing detail"];

export default function MessageActions({ message, onRegenerate, onSelectVersion, onFeedback }) {
  const [rating, setRating] = useState(null);
  const [reasons, setReasons] = useState([]);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);
  const versions = message.versions || [];

  const submit = async () => {
    setSaving(true);
    try {
      await onFeedback(message.id, { rating, reasons, comment });
      setRating(null);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="message-actions">
      <button type="button" onClick={() => setRating("up")} aria-label="Helpful answer">
        <span aria-hidden="true">↑</span>
      </button>
      <button type="button" onClick={() => setRating("down")} aria-label="Unhelpful answer">
        <span aria-hidden="true">↓</span>
      </button>
      <button className="regenerate-button" type="button" onClick={() => onRegenerate(message)}>
        ↻ <span>Regenerate</span>
      </button>
      {versions.length > 1 && (
        <label>
          Version
          <select
            value={message.active_version ?? versions.length - 1}
            onChange={(event) => onSelectVersion(message, Number(event.target.value))}
          >
            {versions.map((_, index) => (
              <option value={index} key={`version-${index}`}>
                {index + 1} of {versions.length}
              </option>
            ))}
          </select>
        </label>
      )}
      {message.feedback && <span className="feedback-saved">Feedback saved</span>}
      {rating && (
        <div className="modal-backdrop" role="presentation">
          <div
            className="feedback-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="feedback-title"
          >
            <h2 id="feedback-title">
              What made this answer {rating === "up" ? "helpful" : "unhelpful"}?
            </h2>
            <div className="reason-chips">
              {REASONS.map((reason) => (
                <button
                  type="button"
                  className={reasons.includes(reason) ? "selected" : ""}
                  aria-pressed={reasons.includes(reason)}
                  onClick={() =>
                    setReasons((current) =>
                      current.includes(reason)
                        ? current.filter((item) => item !== reason)
                        : [...current, reason],
                    )
                  }
                  key={reason}
                >
                  {reason}
                </button>
              ))}
            </div>
            <textarea
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              placeholder="Add an optional comment"
              maxLength={1000}
            />
            <div className="modal-actions">
              <button type="button" onClick={() => setRating(null)}>
                Cancel
              </button>
              <button type="button" disabled={saving} onClick={submit}>
                {saving ? "Saving…" : "Submit feedback"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

MessageActions.propTypes = {
  message: messagePropType.isRequired,
  onRegenerate: PropTypes.func.isRequired,
  onSelectVersion: PropTypes.func.isRequired,
  onFeedback: PropTypes.func.isRequired,
};
