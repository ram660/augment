'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DollarSign, TrendingUp, TrendingDown, AlertCircle, ShoppingCart, Users } from 'lucide-react';
import { contractorAPI, materialsAPI } from '@/lib/api/projects';

interface MaterialItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  pricePerUnit: number;
  category: 'paint' | 'flooring' | 'furniture' | 'decor' | 'labor';
  optional: boolean;
}

interface BudgetEstimatorProps {
  spatialAnalysis?: {
    quantities?: {
      paint_gallons_two_coats?: number;
      flooring_sqft?: number;
      baseboard_linear_ft?: number;
      tile_30x60cm_count?: number;
    };
  };
  onBudgetUpdate?: (total: number) => void;
}

export default function BudgetEstimator({ spatialAnalysis, onBudgetUpdate }: BudgetEstimatorProps) {
  const [materials, setMaterials] = useState<MaterialItem[]>([]);
  const [budgetLevel, setBudgetLevel] = useState<'budget' | 'mid' | 'premium'>('mid');
  const [includeLaborCosts, setIncludeLaborCosts] = useState(false);
  const [isRequestingQuotes, setIsRequestingQuotes] = useState(false);
  const [showQuoteForm, setShowQuoteForm] = useState(false);

  // Price multipliers based on budget level
  const priceMultipliers = {
    budget: 0.7,
    mid: 1.0,
    premium: 1.5,
  };

  useEffect(() => {
    // Generate material list based on spatial analysis
    const items: MaterialItem[] = [];

    if (spatialAnalysis?.quantities?.paint_gallons_two_coats) {
      items.push({
        id: 'paint',
        name: 'Interior Paint (2 coats)',
        quantity: spatialAnalysis.quantities.paint_gallons_two_coats,
        unit: 'gallon',
        pricePerUnit: 45,
        category: 'paint',
        optional: false,
      });
      items.push({
        id: 'primer',
        name: 'Paint Primer',
        quantity: Math.ceil(spatialAnalysis.quantities.paint_gallons_two_coats / 2),
        unit: 'gallon',
        pricePerUnit: 30,
        category: 'paint',
        optional: true,
      });
      items.push({
        id: 'paint-supplies',
        name: 'Paint Supplies (brushes, rollers, tape)',
        quantity: 1,
        unit: 'set',
        pricePerUnit: 50,
        category: 'paint',
        optional: false,
      });
    }

    if (spatialAnalysis?.quantities?.flooring_sqft) {
      items.push({
        id: 'flooring',
        name: 'Flooring Material',
        quantity: spatialAnalysis.quantities.flooring_sqft,
        unit: 'sqft',
        pricePerUnit: 4.5,
        category: 'flooring',
        optional: false,
      });
      items.push({
        id: 'underlayment',
        name: 'Flooring Underlayment',
        quantity: spatialAnalysis.quantities.flooring_sqft,
        unit: 'sqft',
        pricePerUnit: 0.75,
        category: 'flooring',
        optional: true,
      });
    }

    if (spatialAnalysis?.quantities?.baseboard_linear_ft) {
      items.push({
        id: 'baseboard',
        name: 'Baseboard Trim',
        quantity: spatialAnalysis.quantities.baseboard_linear_ft,
        unit: 'ft',
        pricePerUnit: 2.5,
        category: 'decor',
        optional: true,
      });
    }

    // Add furniture estimates
    items.push(
      {
        id: 'sofa',
        name: 'Sofa/Couch',
        quantity: 1,
        unit: 'piece',
        pricePerUnit: 800,
        category: 'furniture',
        optional: true,
      },
      {
        id: 'coffee-table',
        name: 'Coffee Table',
        quantity: 1,
        unit: 'piece',
        pricePerUnit: 250,
        category: 'furniture',
        optional: true,
      },
      {
        id: 'lighting',
        name: 'Light Fixtures',
        quantity: 2,
        unit: 'piece',
        pricePerUnit: 120,
        category: 'decor',
        optional: true,
      },
      {
        id: 'decor',
        name: 'Decorative Items (art, pillows, etc)',
        quantity: 1,
        unit: 'set',
        pricePerUnit: 300,
        category: 'decor',
        optional: true,
      }
    );

    // Add labor costs
    if (includeLaborCosts) {
      const paintLaborHours = (spatialAnalysis?.quantities?.paint_gallons_two_coats || 0) * 4;
      const flooringLaborHours = (spatialAnalysis?.quantities?.flooring_sqft || 0) * 0.5;
      
      if (paintLaborHours > 0) {
        items.push({
          id: 'paint-labor',
          name: 'Painting Labor',
          quantity: paintLaborHours,
          unit: 'hour',
          pricePerUnit: 50,
          category: 'labor',
          optional: false,
        });
      }
      
      if (flooringLaborHours > 0) {
        items.push({
          id: 'flooring-labor',
          name: 'Flooring Installation Labor',
          quantity: flooringLaborHours,
          unit: 'hour',
          pricePerUnit: 65,
          category: 'labor',
          optional: false,
        });
      }
    }

    setMaterials(items);
  }, [spatialAnalysis, includeLaborCosts]);

  const toggleItem = (itemId: string) => {
    setMaterials(prev => 
      prev.map(item => 
        item.id === itemId ? { ...item, optional: !item.optional } : item
      )
    );
  };

  const calculateTotal = () => {
    const multiplier = priceMultipliers[budgetLevel];
    return materials
      .filter(item => !item.optional || item.category === 'labor')
      .reduce((sum, item) => sum + (item.quantity * item.pricePerUnit * multiplier), 0);
  };

  const total = calculateTotal();

  useEffect(() => {
    onBudgetUpdate?.(total);
  }, [total, onBudgetUpdate]);

  const categoryTotals = {
    paint: materials.filter(m => m.category === 'paint' && !m.optional).reduce((s, m) => s + m.quantity * m.pricePerUnit * priceMultipliers[budgetLevel], 0),
    flooring: materials.filter(m => m.category === 'flooring' && !m.optional).reduce((s, m) => s + m.quantity * m.pricePerUnit * priceMultipliers[budgetLevel], 0),
    furniture: materials.filter(m => m.category === 'furniture' && !m.optional).reduce((s, m) => s + m.quantity * m.pricePerUnit * priceMultipliers[budgetLevel], 0),
    decor: materials.filter(m => m.category === 'decor' && !m.optional).reduce((s, m) => s + m.quantity * m.pricePerUnit * priceMultipliers[budgetLevel], 0),
    labor: materials.filter(m => m.category === 'labor').reduce((s, m) => s + m.quantity * m.pricePerUnit * priceMultipliers[budgetLevel], 0),
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h3 className="text-lg font-bold text-gray-800 mb-1">Budget Estimator</h3>
        <p className="text-sm text-gray-600">Get a detailed cost breakdown for your project</p>
      </div>

      {/* Budget Level Selector */}
      <Card>
        <CardContent className="p-4">
          <div className="text-sm font-semibold text-gray-700 mb-3">Select Budget Level</div>
          <div className="grid grid-cols-3 gap-2">
            {(['budget', 'mid', 'premium'] as const).map(level => (
              <button
                key={level}
                onClick={() => setBudgetLevel(level)}
                className={`p-3 rounded-lg border-2 transition-all ${
                  budgetLevel === level
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-xs font-bold text-gray-800 capitalize">{level}</div>
                <div className="text-[10px] text-gray-600 mt-1">
                  {level === 'budget' && '30% savings'}
                  {level === 'mid' && 'Best value'}
                  {level === 'premium' && '+50% quality'}
                </div>
              </button>
            ))}
          </div>

          {/* Labor Toggle */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeLaborCosts}
                onChange={(e) => setIncludeLaborCosts(e.target.checked)}
                className="w-4 h-4 text-purple-600 rounded"
              />
              <span className="text-sm text-gray-700">Include professional labor costs</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Total Budget Card */}
      <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 mb-1">Estimated Total</div>
              <div className="text-3xl font-bold text-green-700">
                ${total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {includeLaborCosts ? 'Including labor' : 'Materials only'}
              </div>
            </div>
            <div className="w-16 h-16 rounded-full bg-green-500 flex items-center justify-center">
              <DollarSign className="w-8 h-8 text-white" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Category Breakdown */}
      <Card>
        <CardContent className="p-4">
          <div className="text-sm font-semibold text-gray-700 mb-3">Cost Breakdown</div>
          <div className="space-y-2">
            {Object.entries(categoryTotals).map(([category, amount]) => {
              if (amount === 0) return null;
              const percentage = (amount / total) * 100;
              
              return (
                <div key={category}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-600 capitalize">{category}</span>
                    <span className="text-xs font-bold text-gray-800">
                      ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${
                        category === 'paint' ? 'bg-purple-500' :
                        category === 'flooring' ? 'bg-amber-500' :
                        category === 'furniture' ? 'bg-blue-500' :
                        category === 'decor' ? 'bg-pink-500' :
                        'bg-gray-500'
                      }`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.open('/dashboard/materials', '_blank')}
        >
          <ShoppingCart className="w-4 h-4 mr-2" />
          View Products
        </Button>
        <Button
          size="sm"
          className="bg-gradient-to-r from-purple-500 to-pink-500"
          onClick={() => setShowQuoteForm(true)}
          disabled={isRequestingQuotes}
        >
          <Users className="w-4 h-4 mr-2" />
          {isRequestingQuotes ? 'Requesting...' : 'Get Quotes'}
        </Button>
      </div>

      {/* Contractor Quote Form Modal */}
      {showQuoteForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md max-h-[90vh] overflow-y-auto">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-800">Request Contractor Quotes</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowQuoteForm(false)}
                >
                  ✕
                </Button>
              </div>

              <form onSubmit={async (e) => {
                e.preventDefault();
                setIsRequestingQuotes(true);

                const formData = new FormData(e.currentTarget);
                try {
                  await contractorAPI.requestQuotes({
                    room_type: 'Living Room',
                    project_description: `Budget: $${total.toLocaleString()}. Materials needed: ${materials.map(m => m.name).join(', ')}`,
                    budget_range: { min: total * 0.9, max: total * 1.1 },
                    location: {
                      zip_code: formData.get('zip_code') as string,
                      city: formData.get('city') as string,
                      state: formData.get('state') as string,
                    },
                    contact_info: {
                      name: formData.get('name') as string,
                      email: formData.get('email') as string,
                      phone: formData.get('phone') as string,
                    },
                  });

                  alert('Quote request submitted! Contractors will contact you soon.');
                  setShowQuoteForm(false);
                } catch (error) {
                  console.error('Failed to request quotes:', error);
                  alert('Failed to submit request. Please try again.');
                } finally {
                  setIsRequestingQuotes(false);
                }
              }}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Your Name *
                    </label>
                    <input
                      type="text"
                      name="name"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="John Doe"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email *
                    </label>
                    <input
                      type="email"
                      name="email"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="john@example.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone
                    </label>
                    <input
                      type="tel"
                      name="phone"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="(555) 123-4567"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ZIP Code *
                    </label>
                    <input
                      type="text"
                      name="zip_code"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="12345"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        City
                      </label>
                      <input
                        type="text"
                        name="city"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        placeholder="New York"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        State
                      </label>
                      <input
                        type="text"
                        name="state"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        placeholder="NY"
                      />
                    </div>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="text-sm text-blue-900">
                      <strong>Estimated Budget:</strong> ${total.toLocaleString()}
                    </div>
                    <div className="text-xs text-blue-700 mt-1">
                      Up to 3 local contractors will contact you with quotes
                    </div>
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-gradient-to-r from-purple-500 to-pink-500"
                    disabled={isRequestingQuotes}
                  >
                    {isRequestingQuotes ? 'Submitting...' : 'Request Quotes'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

