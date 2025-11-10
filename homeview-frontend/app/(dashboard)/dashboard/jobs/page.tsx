'use client';

import { useState } from 'react';
import { 
  Briefcase, 
  MapPin, 
  DollarSign, 
  Clock, 
  Star,
  CheckCircle,
  Shield,
  MessageSquare,
  Plus,
  Search,
  Filter
} from 'lucide-react';

const mockContractors = [
  {
    id: 1,
    name: 'ABC Contractors',
    specialty: 'Kitchen & Bathroom Specialists',
    location: 'Seattle, WA',
    priceRange: '$$$',
    experience: '15 years',
    rating: 4.9,
    reviews: 234,
    licensed: true,
    insured: true,
    verified: true,
    avatar: '🏗️',
  },
  {
    id: 2,
    name: 'XYZ Remodeling',
    specialty: 'Full Home Renovations',
    location: 'Seattle, WA',
    priceRange: '$$',
    experience: '8 years',
    rating: 4.7,
    reviews: 156,
    licensed: true,
    insured: true,
    verified: true,
    avatar: '🔨',
  },
  {
    id: 3,
    name: 'Elite Builders',
    specialty: 'Custom Carpentry & Woodwork',
    location: 'Bellevue, WA',
    priceRange: '$$$$',
    experience: '20 years',
    rating: 5.0,
    reviews: 89,
    licensed: true,
    insured: true,
    verified: true,
    avatar: '🪚',
  },
];

export default function JobsPage() {
  const [activeTab, setActiveTab] = useState<'contractors' | 'jobs'>('contractors');
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="h-full flex bg-gray-50">
      {/* Filters Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
          
          {/* Location */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <input
              type="text"
              placeholder="Enter zip code"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm"
            />
          </div>

          {/* Specialty */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Specialty
            </label>
            <div className="space-y-2">
              {['Kitchen', 'Bathroom', 'Flooring', 'Painting', 'Electrical', 'Plumbing'].map((specialty) => (
                <label key={specialty} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary" />
                  <span className="text-sm text-gray-700">{specialty}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Budget */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Budget
            </label>
            <div className="space-y-2">
              {['$', '$$', '$$$', '$$$$', '$$$$$'].map((price) => (
                <label key={price} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary" />
                  <span className="text-sm text-gray-700">{price}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Rating */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Rating
            </label>
            <div className="flex items-center gap-2">
              {[5, 4, 3, 2, 1].map((rating) => (
                <button
                  key={rating}
                  className="flex items-center gap-1 px-2 py-1 bg-gray-100 hover:bg-primary hover:text-white rounded text-sm transition-colors"
                >
                  <Star className="w-3 h-3 fill-current" />
                  {rating}+
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="p-6">
          <button className="w-full px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium">
            Apply Filters
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center">
                <Briefcase className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Jobs & Contractors</h1>
                <p className="text-sm text-gray-500">Find professionals for your project</p>
              </div>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium shadow-md">
              <Plus className="w-5 h-5" />
              Post Job
            </button>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => setActiveTab('contractors')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'contractors'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Find Contractors
            </button>
            <button
              onClick={() => setActiveTab('jobs')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'jobs'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              My Jobs
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search contractors by name, specialty, or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
        </div>

        {/* Contractors List */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {mockContractors.map((contractor) => (
              <ContractorCard key={contractor.id} contractor={contractor} />
            ))}
          </div>

          {/* Load More */}
          <div className="text-center py-8">
            <button className="px-6 py-3 bg-white border-2 border-gray-200 rounded-lg hover:border-primary hover:text-primary transition-colors font-medium">
              Load More Contractors
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

interface ContractorCardProps {
  contractor: {
    id: number;
    name: string;
    specialty: string;
    location: string;
    priceRange: string;
    experience: string;
    rating: number;
    reviews: number;
    licensed: boolean;
    insured: boolean;
    verified: boolean;
    avatar: string;
  };
}

function ContractorCard({ contractor }: ContractorCardProps) {
  return (
    <div className="bg-white rounded-xl border-2 border-gray-100 hover:border-primary/20 hover:shadow-md transition-all p-6">
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="w-16 h-16 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center text-3xl flex-shrink-0">
          {contractor.avatar}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between mb-2">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">{contractor.name}</h3>
              <p className="text-sm text-gray-600 mb-2">{contractor.specialty}</p>
            </div>
            <div className="flex items-center gap-1">
              <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
              <span className="font-semibold text-gray-900">{contractor.rating}</span>
              <span className="text-sm text-gray-500">({contractor.reviews})</span>
            </div>
          </div>

          {/* Details */}
          <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
            <div className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {contractor.location}
            </div>
            <div className="flex items-center gap-1">
              <DollarSign className="w-4 h-4" />
              {contractor.priceRange}
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {contractor.experience}
            </div>
          </div>

          {/* Badges */}
          <div className="flex items-center gap-2 mb-4">
            {contractor.licensed && (
              <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                <CheckCircle className="w-3 h-3" />
                Licensed
              </span>
            )}
            {contractor.insured && (
              <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                <Shield className="w-3 h-3" />
                Insured
              </span>
            )}
            {contractor.verified && (
              <span className="flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                <CheckCircle className="w-3 h-3" />
                Verified
              </span>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium">
              Request Quote
            </button>
            <button className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium">
              <MessageSquare className="w-4 h-4" />
              Message
            </button>
            <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium">
              View Profile
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

