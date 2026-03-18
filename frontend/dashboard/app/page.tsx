'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState({
    revenue: 0,
    conversions: 0,
    aov: 0,
    recoveredCart: 0,
    revenueTrend: 0,
    conversionsTrend: 0,
    aovTrend: 0,
    recoveredCartTrend: 0
  });
  const [chartData, setChartData] = useState<Array<{ date: string; revenue: number; decisions: number; conversions: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  async function fetchDashboardData() {
    try {
      // Get API URL from environment
      // In Docker: NEXT_PUBLIC_API_URL=http://api:8000
      // Locally: NEXT_PUBLIC_API_URL=http://localhost:8000
      // Default fallback: http://localhost:8000
      let apiUrl = process.env.NEXT_PUBLIC_API_URL;
      
      // If not set in env, detect environment
      if (!apiUrl) {
        // Check if we're in Docker (hostname contains 'docker' or 'container')
        if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
          apiUrl = 'http://localhost:8000';
        } else {
          apiUrl = 'http://localhost:8000'; // Default fallback
        }
      }
      
      // Get store ID from session/auth
      const response = await axios.get(`${apiUrl}/api/v1/dashboard/overview`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setStats(response.data.stats);
      setChartData(response.data.chart_data || []);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      
      // Load sample data for demonstration
      const sampleData = {
        revenue: 45230,
        conversions: 3.2,
        aov: 142.50,
        recoveredCart: 8940,
        revenueTrend: 12.5,
        conversionsTrend: 2.1,
        aovTrend: 5.8,
        recoveredCartTrend: 18.3
      };
      
      setStats(sampleData);
      setChartData([
        { date: 'Mar 08', revenue: 4200, decisions: 240, conversions: 24 },
        { date: 'Mar 09', revenue: 3000, decisions: 221, conversions: 22 },
        { date: 'Mar 10', revenue: 2000, decisions: 229, conversions: 20 },
        { date: 'Mar 11', revenue: 2780, decisions: 200, conversions: 26 },
        { date: 'Mar 12', revenue: 1890, decisions: 218, conversions: 21 },
        { date: 'Mar 13', revenue: 2390, decisions: 250, conversions: 25 },
        { date: 'Mar 14', revenue: 3490, decisions: 210, conversions: 29 }
      ]);
      
      setError('Demo mode: Showing sample data. Backend API not yet available.');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">NeuroCommerce Dashboard</h1>
        <p className="text-gray-600 mt-1">AI Revenue Operating System</p>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Error Banner */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="text-red-800">{error}</p>
          </div>
        )}
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <KPICard
            title="Total Revenue"
            value={`$${stats.revenue.toLocaleString()}`}
            change={`${stats.revenueTrend >= 0 ? '+' : ''}${stats.revenueTrend.toFixed(1)}%`}
            trend={stats.revenueTrend >= 0 ? "up" : "down"}
          />
          <KPICard
            title="Conversion Rate"
            value={`${stats.conversions}%`}
            change={`${stats.conversionsTrend >= 0 ? '+' : ''}${stats.conversionsTrend.toFixed(1)}%`}
            trend={stats.conversionsTrend >= 0 ? "up" : "down"}
          />
          <KPICard
            title="Avg Order Value"
            value={`$${stats.aov.toFixed(2)}`}
            change={`${stats.aovTrend >= 0 ? '+' : ''}${stats.aovTrend.toFixed(1)}%`}
            trend={stats.aovTrend >= 0 ? "up" : "down"}
          />
          <KPICard
            title="Recovered Revenue"
            value={`$${stats.recoveredCart.toLocaleString()}`}
            change={`${stats.recoveredCartTrend >= 0 ? '+' : ''}${stats.recoveredCartTrend.toFixed(1)}%`}
            trend={stats.recoveredCartTrend >= 0 ? "up" : "down"}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Revenue Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="revenue" stroke="#3b82f6" name="Revenue" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Agent Decisions Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Decisions</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="decisions" fill="#10b981" name="Decisions" />
                <Bar dataKey="conversions" fill="#f59e0b" name="Conversions" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sections Navigation */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <SectionCard
            title="Campaigns"
            description="Email, SMS, WhatsApp recovery campaigns"
            link="/campaigns"
          />
          <SectionCard
            title="Experiments"
            description="A/B tests and optimization experiments"
            link="/experiments"
          />
          <SectionCard
            title="Settings"
            description="Store configuration and integrations"
            link="/settings"
          />
        </div>
      </main>
    </div>
  );
}

interface KPICardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
}

function KPICard({ title, value, change, trend }: KPICardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <p className="text-gray-600 text-sm font-medium">{title}</p>
      <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
      <p className={`text-sm mt-2 ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
        {trend === 'up' ? '↑' : '↓'} {change}
      </p>
    </div>
  );
}

interface SectionCardProps {
  title: string;
  description: string;
  link: string;
}

function SectionCard({ title, description, link }: SectionCardProps) {
  return (
    <a
      href={link}
      className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
    >
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="text-gray-600 text-sm mt-2">{description}</p>
      <p className="text-blue-600 text-sm mt-4 font-medium">View →</p>
    </a>
  );
}
