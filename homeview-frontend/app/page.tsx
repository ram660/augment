'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to chat - no authentication required
    router.push('/dashboard/chat');
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-primary to-secondary rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
          <span className="text-3xl">🏠</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">HomeView AI</h1>
        <p className="text-gray-600">Loading your workspace...</p>
      </div>
    </div>
  );
}

