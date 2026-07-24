import PropTypes from "prop-types";

export const sourcePropType = PropTypes.shape({
  page_number: PropTypes.number,
  section_title: PropTypes.string,
  filename: PropTypes.string,
  content: PropTypes.string,
});

export const messagePropType = PropTypes.shape({
  id: PropTypes.string.isRequired,
  role: PropTypes.oneOf(["user", "assistant"]).isRequired,
  content: PropTypes.string.isRequired,
  sources: PropTypes.arrayOf(sourcePropType),
  seconds: PropTypes.number,
  streaming: PropTypes.bool,
  error: PropTypes.bool,
  versions: PropTypes.arrayOf(
    PropTypes.shape({
      content: PropTypes.string.isRequired,
      sources: PropTypes.arrayOf(sourcePropType),
    }),
  ),
  active_version: PropTypes.number,
  feedback: PropTypes.shape({
    rating: PropTypes.oneOf(["up", "down"]),
    reasons: PropTypes.arrayOf(PropTypes.string),
    comment: PropTypes.string,
  }),
});

export const chatPropType = PropTypes.shape({
  id: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  messages: PropTypes.arrayOf(messagePropType),
});

export const userPropType = PropTypes.shape({
  id: PropTypes.string,
  email: PropTypes.string,
  displayName: PropTypes.string,
  avatarUrl: PropTypes.string,
});
