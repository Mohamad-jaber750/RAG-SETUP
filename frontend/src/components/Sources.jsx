import { useState } from "react";

export default function Sources({ sources }) {
  const [open, setOpen] = useState(false);
  if (!sources?.length) return null;
  return <>
    <div className="message-meta">
      <button className="source-toggle" onClick={() => setOpen(value => !value)} aria-expanded={open}>▱ {sources.length} source{sources.length === 1 ? "" : "s"}</button>
    </div>
    <div className={`sources ${open ? "open" : ""}`}>
      {sources.map((source, index) => <article className="source-card" key={`${source.page_number}-${index}`}>
        <strong>{index + 1}. {source.section_title || "CIS Controls v8"} · Page {source.page_number ?? "—"}</strong>
        <p>{source.content}</p>
      </article>)}
    </div>
  </>;
}
