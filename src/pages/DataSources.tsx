import { RefreshCw, CheckCircle2, XCircle } from "lucide-react";
import { motion } from "framer-motion";

const sources = [
  {
    name: "Microsoft Teams",
    description: "Chat messages, channels, and meeting transcripts",
    connected: true,
    lastSync: "2 minutes ago",
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
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" fill="hsl(var(--muted))" />
        <text x="12" y="16" textAnchor="middle" fontSize="10" fill="hsl(var(--muted-foreground))">G</text>
      </svg>
    ),
  },
];

const DataSources = () => (
  <div className="p-6 max-w-4xl mx-auto space-y-6">
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
      <h1 className="text-2xl font-bold text-foreground">Data Sources</h1>
      <p className="text-sm text-muted-foreground mt-1">Manage your connected services and data integrations.</p>
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
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all active:scale-95 ${
                source.connected
                  ? "border border-border text-foreground hover:bg-accent"
                  : "bg-primary text-primary-foreground hover:opacity-90"
              }`}
            >
              {source.connected ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5" /> Sync
                </>
              ) : (
                "Connect"
              )}
            </button>
          </div>
        </motion.div>
      ))}
    </div>
  </div>
);

export default DataSources;
