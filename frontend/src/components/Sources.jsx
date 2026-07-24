import { useId, useState } from "react";
import PropTypes from "prop-types";
import { sourcePropType } from "@/shared/propTypes";

export default function Sources({ sources }) {
  const [open, setOpen] = useState(false);
  const regionId = useId();

  if (!sources?.length) return null;

  return (
    <>
      <div className="message-meta">
        <span className="inline-citations" aria-label="Citations">
          {sources.map((source, index) => (
            <button
              type="button"
              className="citation"
              key={`citation-${source.filename || "cis"}-${source.page_number}-${index}`}
              aria-label={`Citation ${index + 1}: ${source.section_title || "CIS Controls v8"}`}
            >
              [{index + 1}]
              <span role="tooltip">
                <strong>{source.section_title || "CIS Controls v8"}</strong>
                <small>Page {source.page_number ?? "—"}</small>
                {source.content}
              </span>
            </button>
          ))}
        </span>
        <button
          className="source-toggle"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-controls={regionId}
        >
          ▱ {sources.length} source{sources.length === 1 ? "" : "s"}
        </button>
      </div>
      <div id={regionId} className={`sources ${open ? "open" : ""}`}>
        {sources.map((source, index) => (
          <article
            className="source-card"
            key={`${source.filename || "cis"}-${source.page_number}-${source.section_title || index}`}
          >
            <strong>
              {index + 1}. {source.section_title || "CIS Controls v8"} · Page{" "}
              {source.page_number ?? "—"}
            </strong>
            <p>{source.content}</p>
          </article>
        ))}
      </div>
    </>
  );
}

Sources.propTypes = {
  sources: PropTypes.arrayOf(sourcePropType),
};
