import { Brain } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

const Login = () => {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-sm"
      >
        <div className="flex flex-col items-center text-center mb-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary mb-4">
            <Brain className="h-7 w-7 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">Work Intelligence AI</h1>
          <p className="mt-2 text-sm text-muted-foreground max-w-xs">
            Turn your conversations into insights and actions
          </p>
        </div>

        <div className="glass-card p-6">
          <a
            href="http://localhost:8000/auth/login"
            className="flex w-full items-center justify-center gap-3 rounded-lg bg-foreground px-4 py-3 text-sm font-medium text-background transition-all hover:opacity-90 active:scale-[0.98]"
          >
            <svg className="h-5 w-5" viewBox="0 0 23 23" fill="none">
              <path d="M1 1h10v10H1z" fill="#F25022" />
              <path d="M12 1h10v10H12z" fill="#7FBA00" />
              <path d="M1 12h10v10H1z" fill="#00A4EF" />
              <path d="M12 12h10v10H12z" fill="#FFB900" />
            </svg>
            Continue with Microsoft
          </a>

          <div className="mt-4 flex items-center gap-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground">or</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          <div className="mt-4 space-y-3">
            <input
              type="email"
              placeholder="Email address"
              className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/20"
            />
            <input
              type="password"
              placeholder="Password"
              className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/20"
            />
            <a
              href="http://localhost:8000/auth/login"
              className="w-full inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:opacity-90 active:scale-[0.98]"
            >
              Sign In
            </a>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          By continuing, you agree to our Terms and Privacy Policy.
        </p>
      </motion.div>
    </div>
  );
};

export default Login;
