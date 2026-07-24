import { Component } from "react";
import PropTypes from "prop-types";

export default class ErrorBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return (
        <main className="fatal-error">
          <section className="login-card">
            <p className="login-kicker">APPLICATION ERROR</p>
            <h1>Something went wrong</h1>
            <p>
              The interface encountered an unexpected error. Your saved conversations were not
              deleted.
            </p>
            <button className="google-login" onClick={() => window.location.reload()}>
              Reload application
            </button>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
};
