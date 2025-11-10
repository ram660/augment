'use client';

import { useEffect, useState } from 'react';
import { TrendingUp, MessageSquare, ThumbsUp, Star, Activity } from 'lucide-react';

interface DashboardData {
  agent_lightning: {
    enabled: boolean;
    total_interactions: number;
    avg_reward: number;
  };
  feedback_summary: {
    total_feedback_7d: number;
    avg_reward_7d: number;
    submission_rate_pct: number;
    distribution: {
      excellent: number;
      good: number;
      poor: number;
    };
  };
  phase2_progress: {
    interactions: {
      current: number;
      goal: number;
      progress_pct: number;
    };
    feedback: {
      current: number;
      goal: number;
      progress_pct: number;
    };
    submission_rate: {
      current: number;
      goal: number;
      on_track: boolean;
    };
  };
  timestamp: string;
}

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/v1/admin/dashboard');
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }
      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-900 font-semibold mb-2">Error Loading Dashboard</h2>
          <p className="text-red-700 text-sm">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { agent_lightning, feedback_summary, phase2_progress } = data;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Agent Lightning Dashboard</h1>
          <p className="text-gray-600">
            Monitor AI agent performance and data collection progress
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Last updated: {new Date(data.timestamp).toLocaleString()}
          </p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Interactions */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Total Interactions</h3>
              <MessageSquare className="w-5 h-5 text-blue-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {agent_lightning.total_interactions.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Goal: 1,000 ({phase2_progress.interactions.progress_pct.toFixed(1)}%)
            </p>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${Math.min(100, phase2_progress.interactions.progress_pct)}%` }}
              />
            </div>
          </div>

          {/* Total Feedback */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Feedback (7d)</h3>
              <ThumbsUp className="w-5 h-5 text-green-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {feedback_summary.total_feedback_7d.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Goal: 200 ({phase2_progress.feedback.progress_pct.toFixed(1)}%)
            </p>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all"
                style={{ width: `${Math.min(100, phase2_progress.feedback.progress_pct)}%` }}
              />
            </div>
          </div>

          {/* Average Reward */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Avg Reward (7d)</h3>
              <Star className="w-5 h-5 text-yellow-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {feedback_summary.avg_reward_7d.toFixed(2)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Scale: 0.0 - 1.0
            </p>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-yellow-500 h-2 rounded-full transition-all"
                style={{ width: `${feedback_summary.avg_reward_7d * 100}%` }}
              />
            </div>
          </div>

          {/* Submission Rate */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Submission Rate</h3>
              <TrendingUp className="w-5 h-5 text-purple-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {feedback_summary.submission_rate_pct.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Goal: 20% {phase2_progress.submission_rate.on_track ? '✅' : '⏳'}
            </p>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  phase2_progress.submission_rate.on_track ? 'bg-green-500' : 'bg-purple-500'
                }`}
                style={{ width: `${Math.min(100, feedback_summary.submission_rate_pct * 5)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Reward Distribution */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Reward Distribution (Last 7 Days)</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {feedback_summary.distribution.excellent}
              </div>
              <div className="text-sm text-gray-600 mt-1">Excellent (≥0.8)</div>
              <div className="text-xs text-gray-500">
                {feedback_summary.total_feedback_7d > 0
                  ? ((feedback_summary.distribution.excellent / feedback_summary.total_feedback_7d) * 100).toFixed(1)
                  : 0}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">
                {feedback_summary.distribution.good}
              </div>
              <div className="text-sm text-gray-600 mt-1">Good (0.5-0.8)</div>
              <div className="text-xs text-gray-500">
                {feedback_summary.total_feedback_7d > 0
                  ? ((feedback_summary.distribution.good / feedback_summary.total_feedback_7d) * 100).toFixed(1)
                  : 0}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {feedback_summary.distribution.poor}
              </div>
              <div className="text-sm text-gray-600 mt-1">Poor (&lt;0.5)</div>
              <div className="text-xs text-gray-500">
                {feedback_summary.total_feedback_7d > 0
                  ? ((feedback_summary.distribution.poor / feedback_summary.total_feedback_7d) * 100).toFixed(1)
                  : 0}%
              </div>
            </div>
          </div>
        </div>

        {/* Phase 2 Progress */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Phase 2: Data Collection Progress</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Interactions Collected</span>
                <span className="text-sm text-gray-600">
                  {phase2_progress.interactions.current} / {phase2_progress.interactions.goal}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-500 h-3 rounded-full transition-all"
                  style={{ width: `${Math.min(100, phase2_progress.interactions.progress_pct)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Feedback Collected</span>
                <span className="text-sm text-gray-600">
                  {phase2_progress.feedback.current} / {phase2_progress.feedback.goal}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-green-500 h-3 rounded-full transition-all"
                  style={{ width: `${Math.min(100, phase2_progress.feedback.progress_pct)}%` }}
                />
              </div>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                <strong>Status:</strong>{' '}
                {phase2_progress.interactions.progress_pct >= 100 && phase2_progress.feedback.progress_pct >= 100
                  ? '✅ Phase 2 Complete! Ready for training.'
                  : phase2_progress.interactions.progress_pct >= 50
                  ? '⏳ Data collection in progress...'
                  : '🚀 Just getting started!'}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Target: 1,000 interactions with 200+ feedback submissions (20% rate) over 3-6 weeks
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

