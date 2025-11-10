'use client';

import { MainNavigation } from '@/components/shared/MainNavigation';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // No authentication required - open access for all users

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Main Navigation - Top */}
      <MainNavigation />

      {/* Page Content - Full Width */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}

