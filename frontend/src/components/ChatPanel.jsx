import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Markdown from 'react-markdown';
import { PaperPlaneRight, ChatCircleDots, User, Waves, X } from '@phosphor-icons/react';
import { sendChat } from '../api';
import './ChatPanel.css';

export default function ChatPanel({ sessionId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesContainerRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll only the chat messages container — never the page
  useEffect(() => {
    if (messages.length > 0 || loading) {
      const container = messagesContainerRef.current;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }, [messages, loading]);

  async function handleSend(e) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setInput('');
    setError('');
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setLoading(true);

    try {
      const data = await sendChat(sessionId, text);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.reply },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const hasMessages = messages.length > 0 || loading;

  return (
    <div className="chat-panel">
      <div className="chat-divider">
        <div className="chat-divider__line"></div>
        <span className="chat-divider__label">
          <ChatCircleDots weight="fill" size={14} />
          Continue the conversation
        </span>
        <div className="chat-divider__line"></div>
      </div>

      <AnimatePresence>
        {hasMessages && (
          <motion.div
            className="chat-messages"
            ref={messagesContainerRef}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                className={`chat-msg chat-msg--${msg.role}`}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.3, delay: 0.05 }}
              >
                <div className="chat-msg__avatar">
                  {msg.role === 'user' ? (
                    <User weight="fill" size={16} />
                  ) : (
                    <Waves weight="fill" size={16} />
                  )}
                </div>
                <div className="chat-msg__content">
                  <span className="chat-msg__label">
                    {msg.role === 'user' ? 'You' : 'Coach'}
                  </span>
                  <div className="chat-msg__bubble">
                    {msg.role === 'assistant' ? (
                      <Markdown>{msg.content}</Markdown>
                    ) : (
                      <p>{msg.content}</p>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}

            {loading && (
              <motion.div
                className="chat-msg chat-msg--assistant"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="chat-msg__avatar">
                  <Waves weight="fill" size={16} />
                </div>
                <div className="chat-msg__content">
                  <span className="chat-msg__label">Coach</span>
                  <div className="chat-msg__bubble">
                    <div className="chat-typing">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {error && (
          <motion.div
            className="chat-error"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <p>{error}</p>
            <button onClick={() => setError('')} aria-label="Dismiss error">
              <X weight="bold" size={16} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <form className="chat-input-bar" onSubmit={handleSend}>
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder="Ask your coach a follow-up question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <motion.button
          type="submit"
          className="chat-send-btn"
          disabled={!input.trim() || loading}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <PaperPlaneRight weight="fill" size={20} />
        </motion.button>
      </form>
    </div>
  );
}
