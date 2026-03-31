import { CalendarDays, Target, AlertTriangle, TrendingUp, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface InsightsData {
  weekly_summary: string[];
  key_decisions: string[];
  risks: string[];
  trends: string[];
}

const fadeIn = (delay: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, delay },
});

const sections = (data: InsightsData) => [
  {
    icon: CalendarDays,
    title: "Weekly Summary",
    color: "bg-primary/10 text-primary",
    items: data.weekly_summary || [],
  },
  {
    icon: Target,
    title: "Key Decisions",
    color: "bg-success/10 text-success",
    items: data.key_decisions || [],
  },
  {
    icon: AlertTriangle,
    title: "Risks Identified",
    color: "bg-warning/10 text-warning",
    items: data.risks || [],
  },
  {
    icon: TrendingUp,
    title: "Trends",
    color: "bg-primary/10 text-primary",
    items: data.trends || [],
  },
];

const Insights = () => {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/data/insights", {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch insights");
        }

        const insightsData = await response.json();
        setData(insightsData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load insights");
        console.error("Failed to fetch insights:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Generating insights...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <motion.div {...fadeIn(0)}>
          <h1 className="text-2xl font-bold text-foreground">Insights</h1>
          <p className="text-sm text-muted-foreground mt-1">AI-generated intelligence from your communications.</p>
        </motion.div>
        <div className="mt-6 p-4 bg-warning/10 border border-warning/20 rounded-lg text-warning">
          {error}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <motion.div {...fadeIn(0)}>
          <h1 className="text-2xl font-bold text-foreground">Insights</h1>
          <p className="text-sm text-muted-foreground mt-1">AI-generated intelligence from your communications.</p>
        </motion.div>
        <div className="mt-6 p-4 bg-muted/50 border border-muted/20 rounded-lg text-muted-foreground">
          No insights available. Please sync your data first.
        </div>
      </div>
    );
  }

  const sectionItems = sections(data);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <motion.div {...fadeIn(0)}>
        <h1 className="text-2xl font-bold text-foreground">Insights</h1>
        <p className="text-sm text-muted-foreground mt-1">AI-generated intelligence from your communications.</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sectionItems.map((section, i) => (
          <motion.div key={section.title} {...fadeIn(0.1 + i * 0.1)} className="glass-card p-5 hover-lift">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${section.color}`}>
                <section.icon className="h-4 w-4" />
              </div>
              {section.title}
            </h2>
            {section.items.length > 0 ? (
              <ul className="space-y-2.5">
                {section.items.map((item, j) => (
                  <li key={j} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                    <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground italic">No items to display</p>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Insights;
