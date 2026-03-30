import { Mail, MessageSquare, AlertCircle, Zap, FileText, CheckSquare, BarChart3, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface UserProfile {
  displayName: string;
  mail: string;
}

interface GraphData {
  emails: any[];
  chats: any[];
  messages: any[];
}

const fadeIn = (delay: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, delay },
});

const StatCard = ({ icon: Icon, label, value, color }: { icon: any; label: string; value: string; color: string }) => (
  <div className="glass-card p-5 hover-lift">
    <div className="flex items-center gap-3">
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-foreground">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  </div>
);

const Dashboard = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const userResponse = await fetch("http://localhost:8000/auth/me", {
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        });
        if (userResponse.ok) {
          const userData = await userResponse.json();
          setUser(userData);
        }

        const dataResponse = await fetch("http://localhost:8000/data/fetch", {
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        });
        if (dataResponse.ok) {
          const graphData = await dataResponse.json();
          setData(graphData);
        }
      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const firstName = user?.displayName?.split(" ")[0] || "User";
  const emailCount = data?.emails?.length || 0;
  const chatCount = data?.chats?.length || 0;
  const messageCount = data?.messages?.reduce((acc, chat) => acc + (chat.messages?.length || 0), 0) || 0;
  
  // Count connected data sources dynamically
  const connectedSources = (emailCount > 0 ? 1 : 0) + (chatCount > 0 ? 1 : 0);

  const insights = [
    `You have ${emailCount} emails in your inbox`,
    `Connected to ${chatCount} Teams chats`,
    `${messageCount} messages across chats`,
    "Synced with Microsoft Graph API",
  ];

  const actions = [
    { title: "View all emails", source: "Outlook", urgent: emailCount > 10 },
    { title: "Review Teams conversations", source: "Teams chats", urgent: chatCount > 5 },
    { title: "Check message activity", source: "Chat messages", urgent: false },
    { title: "Configure data sources", source: "Settings", urgent: false },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <motion.div {...fadeIn(0)}>
        <h1 className="text-2xl font-bold text-foreground">Good morning, {firstName}</h1>
        <p className="text-sm text-muted-foreground mt-1">Here's your work intelligence summary for today.</p>
      </motion.div>

      {/* Stats */}
      <motion.div {...fadeIn(0.1)} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Mail} label="Emails received" value={emailCount.toString()} color="bg-primary/10 text-primary" />
        <StatCard icon={MessageSquare} label="Teams chats" value={chatCount.toString()} color="bg-success/10 text-success" />
        <StatCard icon={AlertCircle} label="Chat messages" value={messageCount.toString()} color="bg-warning/10 text-warning" />
        <StatCard icon={CheckSquare} label="Data sources" value={connectedSources.toString()} color="bg-destructive/10 text-destructive" />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key Insights */}
        <motion.div {...fadeIn(0.2)} className="glass-card p-5">
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
            <Zap className="h-4 w-4 text-primary" />
            Key Insights
          </h2>
          <ul className="space-y-3">
            {insights.map((insight, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                {insight}
              </li>
            ))}
          </ul>
        </motion.div>

        {/* Pending Actions */}
        <motion.div {...fadeIn(0.3)} className="glass-card p-5">
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
            <CheckSquare className="h-4 w-4 text-primary" />
            Pending Actions
          </h2>
          <ul className="space-y-3">
            {actions.map((action, i) => (
              <li key={i} className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-accent/50 transition-colors">
                <div>
                  <p className="text-sm font-medium text-foreground">{action.title}</p>
                  <p className="text-xs text-muted-foreground">{action.source}</p>
                </div>
                {action.urgent && (
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-destructive/10 text-destructive">
                    Active
                  </span>
                )}
              </li>
            ))}
          </ul>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div {...fadeIn(0.4)} className="glass-card p-5">
        <h2 className="text-sm font-semibold text-foreground mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { icon: Mail, label: "Summarize Emails", desc: "Get a quick summary of today's emails" },
            { icon: FileText, label: "Show Pending Tasks", desc: "View all extracted tasks" },
            { icon: BarChart3, label: "Generate Daily Report", desc: "Create an AI-powered daily report" },
          ].map((action, i) => (
            <button
              key={i}
              className="flex items-center gap-3 rounded-lg border border-border p-4 text-left hover:bg-accent/50 transition-colors group"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <action.icon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">{action.label}</p>
                <p className="text-xs text-muted-foreground truncate">{action.desc}</p>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default Dashboard;
