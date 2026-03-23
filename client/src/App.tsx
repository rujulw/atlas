import { type ReactElement } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import ProtectedAppShell from "./components/ProtectedAppShell";
import Landing from "./pages/Landing";

function PlaceholderApp(): ReactElement {
  return <div className="min-h-screen bg-slate-950" />;
}

function DocsPlaceholder(): ReactElement {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-center text-slate-200">
      <div className="max-w-xl space-y-4">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">docs</p>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] text-white">Documentation route coming next.</h1>
      </div>
    </main>
  );
}

export default function App(): ReactElement {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/docs" element={<DocsPlaceholder />} />
        <Route element={<ProtectedAppShell isAuthenticated={false} />}>
          <Route path="/app" element={<PlaceholderApp />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
