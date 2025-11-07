'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/stores/authStore';
import { Home, MessageSquare, Palette, FolderKanban, ShoppingCart, Users } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const quickActions = [
  {
    title: 'My Homes',
    description: 'View and manage your homes',
    icon: Home,
    href: '/dashboard/homes',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  {
    title: 'Assistant',
    description: 'Chat first + quick transformations',
    icon: MessageSquare,
    href: '/dashboard/assistant',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  {
    title: 'Design Studio',
    description: 'Transform your rooms with AI',
    icon: Palette,
    href: '/dashboard/design',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  {
    title: 'Projects',
    description: 'Manage your home projects',
    icon: FolderKanban,
    href: '/dashboard/projects',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
  },
  {
    title: 'Products',
    description: 'Find products for your home',
    icon: ShoppingCart,
    href: '/dashboard/products',
    color: 'text-pink-600',
    bgColor: 'bg-pink-100',
  },
  {
    title: 'Community',
    description: 'Connect with others',
    icon: Users,
    href: '/dashboard/community',
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-100',
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, checkAuth, router]);

  if (!user) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user.full_name}!
        </h1>
        <p className="text-gray-600 mt-2">
          {user.user_type === 'HOMEOWNER' && "Let's transform your home with AI"}
          {user.user_type === 'DIY_WORKER' && "Ready to plan your next DIY project?"}
          {user.user_type === 'CONTRACTOR' && "Manage your projects and find new clients"}
        </p>
      </div>

      {/* Quick Actions Grid */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link key={action.href} href={action.href}>
                <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <CardHeader>
                    <div className={`w-12 h-12 ${action.bgColor} rounded-lg flex items-center justify-center mb-3`}>
                      <Icon className={`w-6 h-6 ${action.color}`} />
                    </div>
                    <CardTitle className="text-lg">{action.title}</CardTitle>
                    <CardDescription>{action.description}</CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-gray-500 py-8">
              <p>No recent activity yet</p>
              <p className="text-sm mt-2">Start by creating your first home or project</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Getting Started */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Getting Started</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold mb-2">
                1
              </div>
              <CardTitle className="text-lg">Create Your Home</CardTitle>
              <CardDescription>
                Upload floor plans and photos to create a digital twin of your home
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-green-600 font-bold mb-2">
                2
              </div>
              <CardTitle className="text-lg">Explore with AI</CardTitle>
              <CardDescription>
                Chat with AI, visualize designs, and get cost estimates
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 font-bold mb-2">
                3
              </div>
              <CardTitle className="text-lg">Execute Your Plan</CardTitle>
              <CardDescription>
                Create projects, find products, and connect with contractors
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  );
}

