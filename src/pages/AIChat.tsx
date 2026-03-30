import { useState, useRef, useEffect } from "react";
import { Send, Copy, RefreshCw, ChevronDown, ChevronUp, Bot, User } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

const initialMessages: Message[] = [
  {
    id: 1,
    role: "assistant",
    content: "Hello! I'm your Work Intelligence AI assistant. I can help you analyze your emails, chats, and tasks. What would you like to know?",
  },
];

const AIChat = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [expandedSources, setExpandedSources] = useState<number | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    fetch("/api/auth/me", {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(async (res) => {
        if (!res.ok) return null;
        const user = await res.json();
        const resolved = user?.mail || user?.userPrincipalName || user?.id || null;
        setUserId(resolved);
      })
      .catch(() => setUserId(null));
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { id: Date.now(), role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      if (!userId) {
        throw new Error("User context not loaded yet. Please retry in a moment.");
      }

      const response = await fetch("/api/chat", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: input,
          user_id: userId,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      const sourceLabels = Array.isArray(data.sources)
        ? data.sources.map((s: { source?: string; content?: string }) => {
            const source = s?.source || "unknown";
            const snippet = (s?.content || "").trim();
            return snippet ? `${source}: ${snippet}` : source;
          })
        : undefined;
      const assistantMsg: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content: data.answer || "I don't have enough information.",
        sources: sourceLabels,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMsg: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content: "Sorry, I encountered an error processing your message. Please try again.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      {/* Messages */}
      <div className="flex-1 overflow-auto px-4 py-6">
        <div className="max-w-2xl mx-auto space-y-4">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
              >
                {msg.role === "assistant" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary mt-0.5">
                    <Bot className="h-4 w-4" />
                  </div>
                )}
                <div className={`max-w-[80%] ${msg.role === "user" ? "order-first" : ""}`}>
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground rounded-br-md"
                        : "glass-card rounded-bl-md"
                    }`}
                  >
                    <div className="whitespace-pre-wrap text-foreground" dangerouslySetInnerHTML={{
                      __html: msg.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')
                    }} />
                  </div>

                  {msg.role === "assistant" && (
                    <div className="flex items-center gap-1 mt-2">
                      <button className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent transition-colors">
                        <Copy className="h-3 w-3" /> Copy
                      </button>
                      <button className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent transition-colors">
                        <RefreshCw className="h-3 w-3" /> Regenerate
                      </button>
                      {msg.sources && (
                        <button
                          onClick={() => setExpandedSources(expandedSources === msg.id ? null : msg.id)}
                          className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent transition-colors"
                        >
                          Sources {expandedSources === msg.id ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                        </button>
                      )}
                    </div>
                  )}

                  {msg.sources && expandedSources === msg.id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="mt-2 rounded-lg bg-secondary p-3 space-y-1"
                    >
                      {msg.sources.map((s, i) => (
                        <p key={i} className="text-xs text-muted-foreground">📎 {s}</p>
                      ))}
                    </motion.div>
                  )}
                </div>
                {msg.role === "user" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground mt-0.5">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {isTyping && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Bot className="h-4 w-4" />
              </div>
              <div className="glass-card rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:0s]" />
                  <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:0.15s]" />
                  <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:0.3s]" />
                </div>
              </div>
            </motion.div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border bg-card/80 backdrop-blur-sm px-4 py-4">
        <div className="max-w-2xl mx-auto flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder="Ask about your emails, chats, or tasks…"
            className="flex-1 rounded-xl border border-input bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/20"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim()}
            className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground transition-all hover:opacity-90 disabled:opacity-40 active:scale-95"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIChat;
