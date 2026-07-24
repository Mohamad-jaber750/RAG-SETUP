import { lazy, Suspense } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import LoginScreen from "@/components/LoginScreen";
import useAuth from "@/hooks/useAuth";

const AssistantApp = lazy(() => import("@/App"));

function LoadingScreen() {
  return (
    <main className="login-screen">
      <div className="auth-loader" role="status" aria-label="Checking authentication" />
    </main>
  );
}

function ProtectedRoute() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingScreen />;
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}

function AssistantRoute() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <AssistantApp />
    </Suspense>
  );
}

function LoginRoute() {
  const { user, loading, error } = useAuth();
  if (loading) return <LoadingScreen />;
  return user ? <Navigate to="/" replace /> : <LoginScreen error={error} />;
}

function NotFound() {
  return (
    <main className="fatal-error">
      <section className="login-card">
        <p className="login-kicker">ERROR 404</p>
        <h1>Page not found</h1>
        <p>The requested page does not exist.</p>
        <a className="google-login" href="/">
          Return to the assistant
        </a>
      </section>
    </main>
  );
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<AssistantRoute />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
