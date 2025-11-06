'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { Home, ArrowLeft, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { homesAPI } from '@/lib/api/homes';
import type { CreateHomeRequest } from '@/lib/types/home';
import Link from 'next/link';

export default function NewHomePage() {
  const router = useRouter();
  const [formData, setFormData] = useState<CreateHomeRequest>({
    name: '',
    address: '',
    total_sqft: undefined,
    num_bedrooms: undefined,
    num_bathrooms: undefined,
    year_built: undefined,
    home_type: '',
  });
  const [error, setError] = useState('');

  const createHomeMutation = useMutation({
    mutationFn: homesAPI.createHome,
    onSuccess: (home) => {
      router.push(`/dashboard/homes/${home.id}`);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create home');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.name || !formData.address) {
      setError('Name and address are required');
      return;
    }

    createHomeMutation.mutate(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name.includes('num_') || name === 'total_sqft' || name === 'year_built'
        ? value ? parseInt(value) : undefined
        : value,
    });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/homes">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Create New Home</h1>
          <p className="text-gray-600 mt-1">Add your home to start using AI features</p>
        </div>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Home className="w-5 h-5" />
            Home Details
          </CardTitle>
          <CardDescription>
            Enter basic information about your home
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border-2 border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Home Name *</Label>
              <Input
                id="name"
                name="name"
                type="text"
                placeholder="e.g., My Main Residence"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>

            {/* Address */}
            <div className="space-y-2">
              <Label htmlFor="address">Address *</Label>
              <Input
                id="address"
                name="address"
                type="text"
                placeholder="123 Main St, City, State ZIP"
                value={formData.address}
                onChange={handleChange}
                required
              />
            </div>

            {/* Home Type */}
            <div className="space-y-2">
              <Label htmlFor="home_type">Home Type</Label>
              <Input
                id="home_type"
                name="home_type"
                type="text"
                placeholder="e.g., Single Family, Condo, Townhouse"
                value={formData.home_type}
                onChange={handleChange}
              />
            </div>

            {/* Grid for numeric fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Total Square Feet */}
              <div className="space-y-2">
                <Label htmlFor="total_sqft">Total Square Feet</Label>
                <Input
                  id="total_sqft"
                  name="total_sqft"
                  type="number"
                  placeholder="2000"
                  value={formData.total_sqft || ''}
                  onChange={handleChange}
                />
              </div>

              {/* Year Built */}
              <div className="space-y-2">
                <Label htmlFor="year_built">Year Built</Label>
                <Input
                  id="year_built"
                  name="year_built"
                  type="number"
                  placeholder="2000"
                  value={formData.year_built || ''}
                  onChange={handleChange}
                />
              </div>

              {/* Bedrooms */}
              <div className="space-y-2">
                <Label htmlFor="num_bedrooms">Bedrooms</Label>
                <Input
                  id="num_bedrooms"
                  name="num_bedrooms"
                  type="number"
                  placeholder="3"
                  value={formData.num_bedrooms || ''}
                  onChange={handleChange}
                />
              </div>

              {/* Bathrooms */}
              <div className="space-y-2">
                <Label htmlFor="num_bathrooms">Bathrooms</Label>
                <Input
                  id="num_bathrooms"
                  name="num_bathrooms"
                  type="number"
                  step="0.5"
                  placeholder="2"
                  value={formData.num_bathrooms || ''}
                  onChange={handleChange}
                />
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-3 pt-4">
              <Link href="/dashboard/homes" className="flex-1">
                <Button type="button" variant="outline" className="w-full">
                  Cancel
                </Button>
              </Link>
              <Button
                type="submit"
                className="flex-1"
                disabled={createHomeMutation.isPending}
              >
                {createHomeMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Home'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Next Steps Info */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <h3 className="font-semibold text-blue-900 mb-2">What's Next?</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>Upload floor plans and room photos</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>Create a digital twin of your home</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>Start chatting with AI about your home</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>Transform rooms with AI design studio</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

