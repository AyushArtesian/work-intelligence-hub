import { useState } from "react";
import { Mail, CheckSquare, FileText, Play, Loader2, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const actionsList = [
  {
    id: "summarize",
    icon: Mail,
    title: "Summarize Emails",
    description: "Get a concise summary of all emails from today, highlighting key topics and action items.",
  },
  {
    id: "tasks",
    icon: CheckSquare,
    title: "Extract Tasks",
    description: "Scan all conversations and emails to identify and list actionable tasks with deadlines.",
  },
  {
    id: "report",
    icon: FileText,
    title: "Generate Report",
    description: "Create a comprehensive daily report with communication analytics, insights, and recommendations.",
  },
];

// Helper function to format result objects into readable text
const formatResultObject = (obj: any): string => {
  if (typeof obj === "string") return obj;
  if (!obj) return "No output generated.";
  
  let output = "";
  
  // Handle summarize emails response
  if (obj.action === "summarize_emails") {
    output += `📧 **Email Summary**\n`;
    output += `Status: ${obj.status}\n`;
    if (obj.email_count) output += `Emails analyzed: ${obj.email_count}\n\n`;
    if (obj.summary) output += obj.summary;
    return output;
  }
  
  // Handle extract tasks response
  if (obj.action === "extract_tasks") {
    output += `✅ **Extracted Tasks**\n`;
    output += `Status: ${obj.status}\n`;
    if (obj.task_count) output += `Tasks found: ${obj.task_count}\n\n`;
    if (obj.tasks && Array.isArray(obj.tasks) && obj.tasks.length > 0) {
      obj.tasks.forEach((task: any, idx: number) => {
        output += `${idx + 1}. **${task.task || "Untitled"}**\n`;
        if (task.deadline) output += `   📅 Deadline: ${task.deadline}\n`;
        if (task.context) output += `   📝 Context: ${task.context}\n`;
        if (task.source) output += `   📌 Source: ${task.source}\n`;
        output += "\n";
      });
    } else {
      output += "No tasks extracted.";
    }
    return output;
  }
  
  // Handle generate report response
  if (obj.action === "generate_report") {
    output += `📊 **Daily Report**\n`;
    output += `Status: ${obj.status}\n\n`;
    if (obj.executive_summary) output += `**Executive Summary**\n${obj.executive_summary}\n\n`;
    if (obj.priorities) output += `**Priorities**\n${obj.priorities}\n\n`;
    if (obj.blockers) output += `**Blockers**\n${obj.blockers}\n\n`;
    if (obj.recommendations) output += `**Recommendations**\n${obj.recommendations}`;
    return output;
  }
  
  // Fallback: display as formatted JSON
  return JSON.stringify(obj, null, 2);
};

const Actions = () => {
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const runAction = async (id: string) => {
    setError(null);
    setRunning(id);
    try {
      const response = await fetch("http://localhost:8000/actions/run", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action_id: id }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload?.detail || "Action failed");
      }

      // Convert result (object/string) to formatted display string
      const resultStr = typeof payload.result === "string" 
        ? payload.result 
        : formatResultObject(payload.result);
      
      setResults((prev) => ({ ...prev, [id]: resultStr || "No output generated." }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to run action";
      setError(msg);
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-foreground">Actions</h1>
        <p className="text-sm text-muted-foreground mt-1">Run AI-powered actions on your communications.</p>
      </motion.div>

      {error && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </motion.div>
      )}

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
                onClick={() => runAction(action.id)}
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
