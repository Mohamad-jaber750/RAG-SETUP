import ReactMarkdown from "react-markdown";
import PropTypes from "prop-types";
import remarkGfm from "remark-gfm";
import Sources from "./Sources";
import MessageActions from "./MessageActions";
import { messagePropType } from "@/shared/propTypes";

export default function MessageList({ messages, busy, onRegenerate, onSelectVersion, onFeedback }) {
  return (
    <div className="messages">
      {messages.map((message) =>
        message.role === "user" ? (
          <div className="message user" key={message.id}>
            <div className="user-bubble">{message.content}</div>
          </div>
        ) : (
          <div className="message assistant" key={message.id}>
            <div className="assistant-avatar">C</div>
            <div className="assistant-body">
              {message.error ? (
                <div className="error-box">{message.content}</div>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              )}
              <Sources sources={message.sources} />
              {!message.error && !message.streaming && (
                <MessageActions
                  message={message}
                  onRegenerate={onRegenerate}
                  onSelectVersion={onSelectVersion}
                  onFeedback={onFeedback}
                />
              )}
              {message.seconds && (
                <span className="timing">Answered in {message.seconds.toFixed(1)}s</span>
              )}
            </div>
          </div>
        ),
      )}
      {busy && !messages.some((message) => message.streaming) && (
        <div className="message assistant" aria-label="Assistant is responding">
          <div className="assistant-avatar">C</div>
          <div className="assistant-body">
            <div className="typing">
              <i />
              <i />
              <i />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

MessageList.propTypes = {
  messages: PropTypes.arrayOf(messagePropType).isRequired,
  busy: PropTypes.bool.isRequired,
  onRegenerate: PropTypes.func.isRequired,
  onSelectVersion: PropTypes.func.isRequired,
  onFeedback: PropTypes.func.isRequired,
};
