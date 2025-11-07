'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, Home as HomeIcon, MapPin, Calendar, Bed, Bath, Ruler } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { homesAPI } from '@/lib/api/homes';
import { formatDate } from '@/lib/utils';

export default function HomesPage() {
  const { data: homes, isLoading, error } = useQuery({
    queryKey: ['homes'],
    queryFn: homesAPI.getHomes,
  });
  const formatAddress = (addr: any) => {
    if (!addr) return "";
    if (typeof addr === "string") return addr;
    const parts = [addr.street, addr.city, addr.province, addr.postal_code, addr.country].filter(Boolean);
    return parts.join(", ");
  };


  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error loading homes. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Homes</h1>
          <p className="text-gray-600 mt-1">Manage your homes and digital twins</p>
        </div>
        <Link href="/dashboard/homes/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Add Home
          </Button>
        </Link>
      </div>

      {/* Homes Grid */}
      {homes && homes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {homes.map((home) => (
            <Link key={home.id} href={`/dashboard/homes/${home.id}`}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                {/* Floor Plan Image */}
                {home.floor_plan_url ? (
                  <div className="h-48 bg-gray-200 rounded-t-xl overflow-hidden">
                    <img
                      src={home.floor_plan_url}
                      alt={home.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="h-48 bg-gradient-to-br from-blue-100 to-green-100 rounded-t-xl flex items-center justify-center">
                    <HomeIcon className="w-16 h-16 text-gray-400" />
                  </div>
                )}

                <CardHeader>
                  <CardTitle className="text-xl">{home.name}</CardTitle>
                  <CardDescription className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    {formatAddress(home.address)}
                  </CardDescription>
                </CardHeader>

                <CardContent>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    {home.total_sqft && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <Ruler className="w-4 h-4" />
                        {home.total_sqft.toLocaleString()} sqft
                      </div>
                    )}
                    {home.num_bedrooms && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <Bed className="w-4 h-4" />
                        {home.num_bedrooms} beds
                      </div>
                    )}
                    {home.num_bathrooms && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <Bath className="w-4 h-4" />
                        {home.num_bathrooms} baths
                      </div>
                    )}
                    {home.year_built && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <Calendar className="w-4 h-4" />
                        Built {home.year_built}
                      </div>
                    )}
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-500">
                    Created {formatDate(home.created_at)}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <HomeIcon className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No homes yet</h3>
              <p className="text-gray-600 mb-6">
                Get started by creating your first home digital twin
              </p>
              <Link href="/dashboard/homes/new">
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Your First Home
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

