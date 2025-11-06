'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Bell, User, LogOut, Settings, ChevronDown } from 'lucide-react';
import { useAuthStore } from '@/lib/stores/authStore';
import { Button } from '@/components/ui/button';

export function Header() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const getUserTypeLabel = (userType: string) => {
    switch (userType) {
      case 'HOMEOWNER':
        return 'Homeowner';
      case 'DIY_WORKER':
        return 'DIY Worker';
      case 'CONTRACTOR':
        return 'Contractor';
      default:
        return userType;
    }
  };

  const getUserTypeColor = (userType: string) => {
    switch (userType) {
      case 'HOMEOWNER':
        return 'bg-purple-100 text-homeowner';
      case 'DIY_WORKER':
        return 'bg-orange-100 text-diy';
      case 'CONTRACTOR':
        return 'bg-blue-100 text-contractor';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Search or Breadcrumbs (placeholder) */}
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-gray-900">Dashboard</h2>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-4">
          {/* Notifications */}
          <button className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-3 p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div className="text-left hidden md:block">
                  <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                  <p className={`text-xs px-2 py-0.5 rounded-full inline-block ${getUserTypeColor(user?.user_type || '')}`}>
                    {getUserTypeLabel(user?.user_type || '')}
                  </p>
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-600" />
            </button>

            {/* Dropdown Menu */}
            {showUserMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowUserMenu(false)}
                ></div>
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-20">
                  <div className="px-4 py-3 border-b border-gray-200">
                    <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      router.push('/dashboard/settings');
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <Settings className="w-4 h-4" />
                    Settings
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

