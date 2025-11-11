'use client';

import { Suspense, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Home, Loader2, User, Wrench, Briefcase } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { authAPI } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/stores/authStore';
import type { UserType } from '@/lib/types/auth';

const userTypeConfig = {
  homeowner: {
    label: 'Homeowner',
    icon: Home,
    color: 'text-homeowner',
    bgColor: 'bg-purple-100',
    description: 'Visualize designs and find contractors',
  },
  diy: {
    label: 'DIY Worker',
    icon: Wrench,
    color: 'text-diy',
    bgColor: 'bg-orange-100',
    description: 'Plan projects and get AI assistance',
  },
  contractor: {
    label: 'Contractor',
    icon: Briefcase,
    color: 'text-contractor',
    bgColor: 'bg-blue-100',
    description: 'Find clients and showcase work',
  },
};

function RegisterPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setAuth = useAuthStore((state) => state.setAuth);

  const typeParam = searchParams.get('type') || 'homeowner';
  const userTypeKey = typeParam === 'diy' ? 'diy' : typeParam === 'contractor' ? 'contractor' : 'homeowner';
  const userTypeValue: UserType = typeParam === 'diy' ? 'DIY_WORKER' : typeParam === 'contractor' ? 'CONTRACTOR' : 'HOMEOWNER';

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    user_type: userTypeValue,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setFormData(prev => ({ ...prev, user_type: userTypeValue }));
  }, [userTypeValue]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      const { confirmPassword, ...registerData } = formData;
      const response = await authAPI.register(registerData);
      setAuth(response.user, response.access_token, response.refresh_token);
      router.push('/dashboard');
    } catch (err: any) {
      console.error('Registration error:', err);
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const config = userTypeConfig[userTypeKey];
  const Icon = config.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 text-2xl font-bold text-primary">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <Home className="w-6 h-6 text-white" />
            </div>
            HomeView AI
          </Link>
          <p className="text-gray-600 mt-2">Create your account to get started</p>
        </div>

        {/* Register Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className={`w-12 h-12 ${config.bgColor} rounded-lg flex items-center justify-center`}>
                <Icon className={`w-6 h-6 ${config.color}`} />
              </div>
              <div>
                <CardTitle>Sign Up as {config.label}</CardTitle>
                <CardDescription>{config.description}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border-2 border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Full Name Field */}
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name</Label>
                <Input
                  id="full_name"
                  name="full_name"
                  type="text"
                  placeholder="John Doe"
                  value={formData.full_name}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Email Field */}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
                <p className="text-xs text-gray-500">Must be at least 8 characters</p>
              </div>

              {/* Confirm Password Field */}
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Already have an account?</span>
              </div>
            </div>

            {/* Login Link */}
            <Link href="/login">
              <Button variant="outline" className="w-full">
                Sign In
              </Button>
            </Link>

            {/* Change User Type */}
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-600 mb-2">Want to sign up as a different type?</p>
              <div className="flex gap-2 justify-center">
                {Object.entries(userTypeConfig).map(([key, value]) => (
                  key !== userTypeKey && (
                    <Link key={key} href={`/register?type=${key}`}>
                      <Button variant="ghost" size="sm">
                        {value.label}
                      </Button>
                    </Link>
                  )
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Back to Home */}
        <div className="text-center mt-6">
          <Link href="/" className="text-sm text-gray-600 hover:text-primary">
            ← Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
      <RegisterPageContent />
    </Suspense>
  );
}
