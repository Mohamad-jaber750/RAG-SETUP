import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Sources from "./Sources";

export default function MessageList({ messages, busy }) {
  return <div className="messages">
    {messages.map((message, index) => message.role === "user" ?
      <div className="message user" key={index}><div className="user-bubble">{message.content}</div></div> :
      <div className="message assistant" key={index}>
        <div className="assistant-avatar">C</div>
        <div className="assistant-body">
          {message.error ? <div className="error-box">{message.content}</div> : <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>}
          <Sources sources={message.sources}/>
          {message.seconds && <span className="timing">Answered in {message.seconds.toFixed(1)}s</span>}
        </div>
      </div>)}
    {busy && <div className="message assistant"><div className="assistant-avatar">C</div><div className="assistant-body"><div className="typing"><i/><i/><i/></div></div></div>}
  </div>;
}
