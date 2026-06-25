import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import WorkspaceApp from "./App";
import { LandingPage } from "./pages/LandingPage";
import "@xyflow/react/dist/style.css";
import "./styles/globals.css";
import "./styles/landing.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<WorkspaceApp />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
