import { useState } from "react";
import { Mail, CheckSquare, FileText, Play, Loader2, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const actionsList = [
  {
    id: "summarize",
    icon: Mail,
    title: "Summarize Emails",
    description: "Get a concise summary of all emails from today, highlighting key topics and action items.",
    result: "**Today's Email Summary (24 emails)**\n\n📧 **High Priority:**\n• CFO requesting budget finalization by Friday\n• Client asked for revised timeline on Project Atlas\n\n📋 **Action Items:**\n• Respond to vendor proposal (deadline: tomorrow)\n• Review and approve marketing assets\n• Schedule follow-up with sales team\n\n📊 **Topics:** Budget (8), Project Atlas (5), Hiring (4), Marketing (3), Other (4)",
  },
  {
    id: "tasks",
    icon: CheckSquare,
    title: "Extract Tasks",
    description: "Scan all conversations and emails to identify and list actionable tasks with deadlines.",
    result: "**Extracted Tasks (12 found)**\n\n🔴 **Urgent:**\n1. Finalize Q2 budget — Due: Friday\n2. Respond to vendor proposal — Due: Tomorrow\n3. Review client feedback on Project Atlas — Due: Wednesday\n\n🟡 **This Week:**\n4. Schedule 1-on-1 with new hire\n5. Update project roadmap\n6. Send weekly stakeholder update\n\n🟢 **Later:**\n7. Plan team offsite for April\n8. Research new analytics tools",
  },
  {
    id: "report",
    icon: FileText,
    title: "Generate Report",
    description: "Create a comprehensive daily report with communication analytics, insights, and recommendations.",
    result: "**Daily Intelligence Report — March 30, 2026**\n\n📈 **Communication Stats:**\n• Emails: 24 received, 18 sent\n• Teams Messages: 45 sent, 62 received\n• Meetings: 4 attended (2.5 hours total)\n\n🎯 **Key Outcomes:**\n• Budget approved for Q3 marketing campaign\n• Engineering sprint planning completed\n• New hire onboarding documents signed\n\n💡 **Recommendations:**\n• Block focus time tomorrow morning — high meeting load expected\n• Follow up with Sarah on design review\n• Prepare talking points for Thursday's board meeting",
  },
];

const Actions = () => {
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, string>>({});

  const runAction = (id: string, result: string) => {
    setRunning(id);
    setTimeout(() => {
      setResults((prev) => ({ ...prev, [id]: result }));
      setRunning(null);
    }, 2000);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-foreground">Actions</h1>
        <p className="text-sm text-muted-foreground mt-1">Run AI-powered actions on your communications.</p>
      </motion.div>

      <div className="space-y-4">
        {actionsList.map((action, i) => (
          <motion.div
            key={action.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.1 }}
            className="glass-card overflow-hidden"
          >
            <div className="flex items-center justify-between p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <action.icon className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">{action.title}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">{action.description}</p>
                </div>
              </div>
              <button
                onClick={() => runAction(action.id, action.result)}
                disabled={running === action.id}
                className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:opacity-90 disabled:opacity-60 active:scale-95"
              >
                {running === action.id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {running === action.id ? "Running…" : "Run"}
              </button>
            </div>

            <AnimatePresence>
              {results[action.id] && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-border"
                >
                  <div className="p-5 bg-secondary/50 relative">
                    <button
                      onClick={() => setResults((prev) => { const n = { ...prev }; delete n[action.id]; return n; })}
                      className="absolute top-3 right-3 text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                    <div
                      className="text-sm text-foreground leading-relaxed whitespace-pre-wrap pr-6"
                      dangerouslySetInnerHTML={{
                        __html: results[action.id].replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')
                      }}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Actions;
