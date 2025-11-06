'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  MessageSquare, 
  Palette, 
  FolderKanban, 
  ShoppingCart, 
  Users, 
  Settings,
  LayoutDashboard,
  Package
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'My Homes', href: '/dashboard/homes', icon: Home },
  { name: 'AI Chat', href: '/dashboard/chat', icon: MessageSquare },
  { name: 'Design Studio', href: '/dashboard/design', icon: Palette },
  { name: 'Projects', href: '/dashboard/projects', icon: FolderKanban },
  { name: 'Products', href: '/dashboard/products', icon: ShoppingCart },
  { name: 'Community', href: '/dashboard/community', icon: Users },
];

const secondaryNavigation = [
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200">
      {/* Logo */}
      <div className="flex items-center gap-2 px-6 py-4 border-b border-gray-200">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
          <Home className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold text-gray-900">HomeView AI</span>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <Icon className="w-5 h-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Secondary Navigation */}
      <div className="px-3 py-4 border-t border-gray-200 space-y-1">
        {secondaryNavigation.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <Icon className="w-5 h-5" />
              {item.name}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

