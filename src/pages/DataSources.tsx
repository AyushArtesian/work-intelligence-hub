import { RefreshCw, CheckCircle2, XCircle } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";

interface DataSource {
  name: string;
  description: string;
  connected: boolean;
  lastSync: string | null;
  source: "teams" | "outlook" | "google";
  icon: JSX.Element;
  syncing?: boolean;
}

const initialSources: DataSource[] = [
  {
    name: "Microsoft Teams",
    description: "Chat messages, channels, and meeting transcripts",
    connected: true,
    lastSync: "2 minutes ago",
    source: "teams",
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none">
        <path d="M20.5 7.5a2 2 0 100-4 2 2 0 000 4z" fill="hsl(var(--primary))" />
        <rect x="14" y="6" width="8" height="10" rx="1.5" fill="hsl(var(--primary))" opacity="0.7" />
        <rect x="2" y="4" width="13" height="14" rx="2" fill="hsl(var(--primary))" />
        <path d="M6 9h5M6 12h3" stroke="hsl(var(--primary-foreground))" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    name: "Microsoft Outlook",
    description: "Emails, calendar events, and contacts",
    connected: true,
    lastSync: "5 minutes ago",
    source: "outlook",
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none">
        <rect x="2" y="4" width="20" height="16" rx="2" fill="hsl(var(--primary))" />
        <path d="M2 8l10 6 10-6" stroke="hsl(var(--primary-foreground))" strokeWidth="1.5" />
      </svg>
    ),
  },
  {
    name: "Google Workspace",
    description: "Gmail, Google Drive, and Google Calendar",
    connected: false,
    lastSync: null,
    source: "google",
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" fill="hsl(var(--muted))" />
        <text x="12" y="16" textAnchor="middle" fontSize="10" fill="hsl(var(--muted-foreground))">G</text>
      </svg>
    ),
  },
];

const DataSources = () => {
  const [sources, setSources] = useState<DataSource[]>(initialSources);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [fetching, setFetching] = useState(false);
  const [processing, setProcessing] = useState(false);

  const handleFetch = async () => {
    setFetching(true);
    try {
      const response = await fetch("http://localhost:8000/data/fetch", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const result = await response.json();
        const emailsFetched = Array.isArray(result.emails) ? result.emails.length : 0;
        const messagesFetched = Array.isArray(result.messages)
          ? result.messages.reduce((total: number, group: any) => {
              const groupMsgs = Array.isArray(group?.messages) ? group.messages.length : 0;
              return total + groupMsgs;
            }, 0)
          : 0;
        console.log("Fetch successful:", result);
        alert(`Fetched data successfully!\nEmails: ${emailsFetched}\nMessages: ${messagesFetched}`);
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Fetch failed");
      }
    } catch (error) {
      console.error("Fetch error:", error);
      alert(`Error fetching data: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setFetching(false);
    }
  };

  const handleProcess = async () => {
    setProcessing(true);
    try {
      const response = await fetch("http://localhost:8000/data/process", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const result = await response.json();
        const docsSaved = result.documents_saved || 0;
        const docsIndexed = result.documents_indexed || 0;
        console.log("Process successful:", result);
        alert(`Processed data successfully!\nDocuments saved: ${docsSaved}\nDocuments indexed: ${docsIndexed}`);
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Process failed");
      }
    } catch (error) {
      console.error("Process error:", error);
      alert(`Error processing data: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleSync = async (sourceName: string) => {
    setSyncing(sourceName);
    try {
      const response = await fetch("http://localhost:8000/data/sync", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const result = await response.json();
        // Update last sync time
        setSources((prev) =>
          prev.map((s) =>
            s.name === sourceName
              ? { ...s, lastSync: "just now" }
              : s
          )
        );
        console.log("Sync successful:", result);
      } else {
        console.error("Sync failed:", response.statusText);
        alert("Failed to sync data. Check console for details.");
      }
    } catch (error) {
      console.error("Sync error:", error);
      alert("Error syncing data");
    } finally {
      setSyncing(null);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-foreground">Data Sources</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your connected services and data integrations.</p>
      </motion.div>

      {/* Pipeline Actions */}
      <motion.div 
        initial={{ opacity: 0, y: 12 }} 
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-4 border border-border"
      >
        <p className="text-xs font-semibold text-muted-foreground mb-3 uppercase">Data Pipeline</p>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleFetch}
            disabled={fetching}
            className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-accent transition-all disabled:opacity-50 active:scale-95"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${fetching ? "animate-spin" : ""}`} />
            {fetching ? "Fetching..." : "1. Fetch Data"}
          </button>
          <button
            onClick={handleProcess}
            disabled={processing}
            className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-accent transition-all disabled:opacity-50 active:scale-95"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${processing ? "animate-spin" : ""}`} />
            {processing ? "Processing..." : "2. Process & Index"}
          </button>
          <span className="px-3 py-2 text-xs text-muted-foreground">→ Then sync your sources below</span>
        </div>
      </motion.div>

      <div className="space-y-4">
        {sources.map((source, i) => (
          <motion.div
            key={source.name}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.1 }}
            className="glass-card p-5 hover-lift"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-secondary">
                  {source.icon}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">{source.name}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">{source.description}</p>
                  <div className="flex items-center gap-1.5 mt-2">
                    {source.connected ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                        <span className="text-xs text-success font-medium">Connected</span>
                        <span className="text-xs text-muted-foreground ml-2">Last synced {source.lastSync}</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">Not connected</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={() => source.connected && handleSync(source.name)}
                disabled={syncing === source.name || !source.connected}
                className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed ${
                  source.connected
                    ? "border border-border text-foreground hover:bg-accent"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                <RefreshCw className={`h-3.5 w-3.5 ${syncing === source.name ? "animate-spin" : ""}`} />
                {syncing === source.name ? "Syncing..." : source.connected ? "Sync" : "Connect"}
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default DataSources;

