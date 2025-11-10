import { ChatInterface } from '@/components/chat/ChatInterface';

export default function ChatHomePage() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <ChatInterface />
      </div>
    </main>
  );
}

