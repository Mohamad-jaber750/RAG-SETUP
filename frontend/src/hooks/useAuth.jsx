import { createContext, useContext, useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { consumeAuthErrorFromUrl, getCurrentUser, logout } from "@/services/authApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const preview = new URLSearchParams(window.location.search).get("preview") === "true";
  const [user, setUser] = useState(preview ? { displayName: "Preview User" } : null);
  const [loading, setLoading] = useState(!preview);
  const [error, setError] = useState(() => (preview ? "" : consumeAuthErrorFromUrl() || ""));

  useEffect(() => {
    if (preview) return;

    getCurrentUser()
      .then(setUser)
      .catch((authError) => setError(authError.message))
      .finally(() => setLoading(false));
  }, [preview]);

  const signOut = async () => {
    try {
      await logout();
    } finally {
      setUser(null);
    }
  };

  const value = useMemo(
    () => ({ user, loading, error, preview, signOut }),
    [error, loading, preview, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
