import { User, Shield, Palette } from "lucide-react";
import { motion } from "framer-motion";

const SettingsPage = () => (
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
          JD
        </div>
        <div>
          <p className="font-semibold text-foreground">John Doe</p>
          <p className="text-sm text-muted-foreground">john.doe@company.com</p>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground">Full Name</label>
          <input defaultValue="John Doe" className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring/20" />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Email</label>
          <input defaultValue="john.doe@company.com" className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring/20" />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Role</label>
          <input defaultValue="Product Manager" className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring/20" />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Department</label>
          <input defaultValue="Product" className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring/20" />
        </div>
      </div>
    </motion.div>

    {/* Connected Accounts */}
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
      <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-5">
        <Shield className="h-4 w-4 text-primary" /> Connected Accounts
      </h2>
      <div className="space-y-3">
        {[
          { name: "Microsoft Account", email: "john.doe@company.com", connected: true },
          { name: "Google Account", email: "Not connected", connected: false },
        ].map((acct) => (
          <div key={acct.name} className="flex items-center justify-between rounded-lg border border-border p-4">
            <div>
              <p className="text-sm font-medium text-foreground">{acct.name}</p>
              <p className="text-xs text-muted-foreground">{acct.email}</p>
            </div>
            <button className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              acct.connected ? "text-destructive hover:bg-destructive/10" : "bg-primary text-primary-foreground hover:opacity-90"
            }`}>
              {acct.connected ? "Disconnect" : "Connect"}
            </button>
          </div>
        ))}
      </div>
    </motion.div>

    {/* Appearance */}
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-6">
      <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-5">
        <Palette className="h-4 w-4 text-primary" /> Appearance
      </h2>
      <p className="text-sm text-muted-foreground mb-3">Toggle dark mode using the moon/sun icon in the top navigation bar.</p>
    </motion.div>

    <div className="flex justify-end">
      <button className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:opacity-90 active:scale-95">
        Save Changes
      </button>
    </div>
  </div>
);

export default SettingsPage;
