'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  MessageSquare, 
  Palette, 
  Compass, 
  Users, 
  Briefcase,
  Home,
  Bell,
  Settings,
  User
} from 'lucide-react';
import { cn } from '@/lib/utils';

const mainTabs = [
  { 
    name: 'Chat', 
    href: '/dashboard/chat', 
    icon: MessageSquare,
    description: 'AI Project Assistant'
  },
  { 
    name: 'Design Studio', 
    href: '/dashboard/studio', 
    icon: Palette,
    description: 'Visual Editor'
  },
  { 
    name: 'Explore', 
    href: '/dashboard/explore', 
    icon: Compass,
    description: 'Discover Ideas'
  },
  { 
    name: 'Community', 
    href: '/dashboard/community', 
    icon: Users,
    description: 'Connect & Share'
  },
  { 
    name: 'Jobs', 
    href: '/dashboard/jobs', 
    icon: Briefcase,
    description: 'Find Contractors'
  },
];

export function MainNavigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-2 group">
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow">
              <Home className="w-6 h-6 text-white" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                HomeView AI
              </h1>
              <p className="text-xs text-gray-500">Your Home, Reimagined</p>
            </div>
          </Link>

          {/* Main Tabs */}
          <div className="flex items-center gap-1">
            {mainTabs.map((tab) => {
              const isActive = pathname?.startsWith(tab.href);
              const Icon = tab.icon;
              
              return (
                <Link
                  key={tab.name}
                  href={tab.href}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200',
                    'hover:bg-gray-50',
                    isActive 
                      ? 'bg-primary/10 text-primary font-medium' 
                      : 'text-gray-600 hover:text-gray-900'
                  )}
                  title={tab.description}
                >
                  <Icon className={cn(
                    'w-5 h-5',
                    isActive ? 'text-primary' : 'text-gray-500'
                  )} />
                  <span className="hidden md:inline text-sm font-medium">
                    {tab.name}
                  </span>
                </Link>
              );
            })}
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            {/* Notifications */}
            <button 
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors relative"
              title="Notifications"
            >
              <Bell className="w-5 h-5 text-gray-600" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {/* Settings */}
            <Link
              href="/dashboard/settings"
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              title="Settings"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </Link>

            {/* Profile */}
            <Link
              href="/dashboard/profile"
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
              title="Profile"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

