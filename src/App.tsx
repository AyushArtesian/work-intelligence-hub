import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useEffect, useState } from "react";
import { MainLayout } from "@/components/MainLayout";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import AIChat from "./pages/AIChat";
import Insights from "./pages/Insights";
import Actions from "./pages/Actions";
import DataSources from "./pages/DataSources";
import SettingsPage from "./pages/SettingsPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const AuthGuard = ({ children }: { children: React.ReactNode }) => {
  const [status, setStatus] = useState<"loading" | "authorized" | "unauthorized">("loading");

  useEffect(() => {
    fetch("/api/auth/me", {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((res) => {
        if (res.ok) {
          setStatus("authorized");
        } else {
          setStatus("unauthorized");
        }
      })
      .catch(() => setStatus("unauthorized"));
  }, []);

  if (status === "loading") return <div>Loading...</div>;
  if (status === "unauthorized") {
    window.location.href = "/";
    return null;
  }
  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/login" element={<Index />} />
          <Route
            path="/dashboard"
            element={
              <AuthGuard>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </AuthGuard>
            }
          />
          <Route path="/chat" element={<MainLayout><AIChat /></MainLayout>} />
          <Route path="/insights" element={<MainLayout><Insights /></MainLayout>} />
          <Route path="/actions" element={<MainLayout><Actions /></MainLayout>} />
          <Route path="/data-sources" element={<MainLayout><DataSources /></MainLayout>} />
          <Route path="/settings" element={<MainLayout><SettingsPage /></MainLayout>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
