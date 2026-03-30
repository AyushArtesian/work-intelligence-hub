import { User, Shield, Palette, LogOut } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

interface UserProfile {
  id: string;
  displayName: string;
  mail: string;
  userPrincipalName: string;
  mobilePhone?: string;
  jobTitle?: string;
}

const SettingsPage = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await fetch("http://localhost:8000/auth/me", {
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        });
        if (response.ok) {
          const data = await response.json();
          setUser(data);
        }
      } catch (error) {
        console.error("Failed to fetch user profile:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  const handleLogout = async () => {
    try {
      await fetch("http://localhost:8000/auth/logout", {
        method: "POST",
        credentials: "include",
      });
      navigate("/");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  if (loading) {
    return (
      <div className="p-6 max-w-3xl mx-auto flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Loading profile...</p>
      </div>
    );
  }

  const displayName = user?.displayName || user?.userPrincipalName || "User";
  const email = user?.mail || user?.userPrincipalName || "No email";
  const initials = getInitials(displayName);

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your account and preferences.</p>
      </motion.div>

      {/* Profile */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6">
        <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-5">
          <User className="h-4 w-4 text-primary" /> Profile
        </h2>
        <div className="flex items-center gap-4 mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-xl font-bold text-primary-foreground">
            {initials}
          </div>
          <div>
            <p className="font-semibold text-foreground">{displayName}</p>
            <p className="text-sm text-muted-foreground">{email}</p>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground">Full Name</label>
            <input
              disabled
              defaultValue={displayName}
              className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-ring/20"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">Email</label>
            <input
              disabled
              defaultValue={email}
              className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-ring/20"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">User ID</label>
            <input
              disabled
              defaultValue={user?.id || "N/A"}
              className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-ring/20"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">Job Title</label>
            <input
              disabled
              defaultValue={user?.jobTitle || "Not specified"}
              className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-ring/20"
            />
          </div>
        </div>
      </motion.div>

      {/* Connected Accounts */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
        <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-5">
          <Shield className="h-4 w-4 text-primary" /> Connected Accounts
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div>
              <p className="text-sm font-medium text-foreground">Microsoft Account</p>
              <p className="text-xs text-muted-foreground">{email}</p>
            </div>
            <span className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
              Connected
            </span>
          </div>
          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div>
              <p className="text-sm font-medium text-foreground">Google Account</p>
              <p className="text-xs text-muted-foreground">Not connected</p>
            </div>
            <button className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-colors hover:opacity-90">
              Connect
            </button>
          </div>
        </div>
      </motion.div>

      {/* Appearance */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-6">
        <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-5">
          <Palette className="h-4 w-4 text-primary" /> Appearance
        </h2>
        <p className="text-sm text-muted-foreground mb-3">Toggle dark mode using the moon/sun icon in the top navigation bar.</p>
      </motion.div>

      <div className="flex justify-between gap-3">
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 rounded-lg bg-destructive/10 px-6 py-2.5 text-sm font-medium text-destructive transition-all hover:bg-destructive/20 active:scale-95"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </div>
    </div>
  );
};
