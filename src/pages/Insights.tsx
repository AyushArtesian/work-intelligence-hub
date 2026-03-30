import { CalendarDays, Target, AlertTriangle, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

const fadeIn = (delay: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, delay },
});

const sections = [
  {
    icon: CalendarDays,
    title: "Weekly Summary",
    color: "bg-primary/10 text-primary",
    items: [
      "Processed 142 emails and 68 Teams messages this week",
      "Most active day was Wednesday with 38 emails",
      "Average response time improved to 2.1 hours",
      "3 meetings were rescheduled due to conflicts",
    ],
  },
  {
    icon: Target,
    title: "Key Decisions",
    color: "bg-success/10 text-success",
    items: [
      "Marketing approved the Q3 campaign budget of $45,000",
      "Engineering decided to postpone v2.0 launch to March 15",
      "HR confirmed new hire start date for March 1st",
      "Product team aligned on cutting Feature X from MVP",
    ],
  },
  {
    icon: AlertTriangle,
    title: "Risks Identified",
    color: "bg-warning/10 text-warning",
    items: [
      "Client project deadline may slip — awaiting vendor confirmation",
      "Two team members flagged burnout concerns in 1:1s",
      "Budget overrun risk on the infrastructure migration project",
    ],
  },
  {
    icon: TrendingUp,
    title: "Trends",
    color: "bg-primary/10 text-primary",
    items: [
      "Cross-team collaboration increased 25% over last month",
      "Email volume trending down — more conversations in Teams",
      "Task completion rate improved from 72% to 84%",
      "Meeting duration decreased by an average of 12 minutes",
    ],
  },
];

const Insights = () => (
  <div className="p-6 max-w-6xl mx-auto space-y-6">
    <motion.div {...fadeIn(0)}>
      <h1 className="text-2xl font-bold text-foreground">Insights</h1>
      <p className="text-sm text-muted-foreground mt-1">AI-generated intelligence from your communications.</p>
    </motion.div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {sections.map((section, i) => (
        <motion.div key={section.title} {...fadeIn(0.1 + i * 0.1)} className="glass-card p-5 hover-lift">
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
            <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${section.color}`}>
              <section.icon className="h-4 w-4" />
            </div>
            {section.title}
          </h2>
          <ul className="space-y-2.5">
            {section.items.map((item, j) => (
              <li key={j} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
                {item}
              </li>
            ))}
          </ul>
        </motion.div>
      ))}
    </div>
  </div>
);

export default Insights;
