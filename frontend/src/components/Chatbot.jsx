import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { FiMessageSquare, FiX, FiSend } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { text: "Hello! I'm your SafeDrive AI assistant. How can I help you navigate the platform today?", isBot: true }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userText = input;
    setMessages(prev => [...prev, { text: userText, isBot: false }]);
    setInput("");
    setIsLoading(true);

    try {
      // Send the current message and the previous conversation history
      const history = messages.map(msg => ({ role: msg.isBot ? 'assistant' : 'user', content: msg.text }));
      const res = await axios.post('http://localhost:5000/api/chat', { 
        message: userText,
        history: history
      });
      if (res.data.success) {
        setMessages(prev => [...prev, { text: res.data.response, isBot: true }]);
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { text: "Sorry, I'm having trouble connecting right now. Please check if the API key is configured.", isBot: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 p-4 bg-primary text-black rounded-full shadow-lg hover:scale-110 transition-transform z-50 flex items-center justify-center"
      >
        {isOpen ? <FiX size={24} /> : <FiMessageSquare size={24} />}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-80 sm:w-96 h-[500px] max-h-[70vh] bg-bg-surface border border-white/10 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden backdrop-blur-xl">
          {/* Header */}
          <div className="bg-primary/10 p-4 border-b border-white/10 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-primary to-secondary flex items-center justify-center text-black font-bold">
              AI
            </div>
            <div>
              <h3 className="font-bold text-white">SafeDrive Assistant</h3>
              <p className="text-xs text-green-400">Online</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.isBot ? 'justify-start' : 'justify-end'}`}>
                <div 
                  className={`max-w-[80%] p-3 rounded-2xl text-sm ${
                    msg.isBot 
                      ? 'bg-white/5 border border-white/10 text-gray-200 rounded-tl-none prose prose-invert prose-sm max-w-none prose-p:leading-snug prose-p:my-1 prose-ul:my-1 prose-li:my-0' 
                      : 'bg-primary text-black font-medium rounded-tr-none'
                  }`}
                >
                  {msg.isBot ? (
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  ) : (
                    msg.text
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white/5 border border-white/10 p-3 rounded-2xl rounded-tl-none flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <form onSubmit={handleSend} className="p-3 border-t border-white/10 bg-black/20">
            <div className="relative flex items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask something..."
                className="w-full bg-white/5 border border-white/10 rounded-full pl-4 pr-12 py-3 text-sm text-white focus:outline-none focus:border-primary transition-colors"
              />
              <button 
                type="submit"
                disabled={isLoading || !input.trim()}
                className="absolute right-2 p-2 bg-primary text-black rounded-full hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                <FiSend size={16} />
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
