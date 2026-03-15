import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';

interface Position {
  id: number;
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  invested: number;
  current_value: number;
  opened_at: string;
  duration_hours: number;
  duration_days: number;
}

interface Signal {
  type: string;
  strategy: string;
  confidence: number;
  entry_price: number;
  target_price: number;
  stop_loss: number;
  reason: string;
  risk_reward: number;
  target_pct: number;
  sl_pct: number;
  sl_proximity_pct: number;
}

interface Issue {
  severity: string;
  type: string;
  description: string;
  lesson: string;
}

interface Recommendation {
  priority: string;
  action: string;
  description: string;
  reason: string;
}

interface PositionAnalysis {
  position: Position;
  signal: Signal | null;
  issues: Issue[];
  recommendations: Recommendation[];
  assessment: string;
}

interface CommonIssue {
  type: string;
  count: number;
  description: string;
  lesson: string;
  severity: string;
}

interface Analysis {
  total_positions: number;
  total_unrealized_loss: number;
  positions: PositionAnalysis[];
  common_issues: CommonIssue[];
  key_lessons: string[];
}

export default function PositionAnalysis() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPosition, setExpandedPosition] = useState<number | null>(null);

  useEffect(() => {
    fetchAnalysis();
    const interval = setInterval(fetchAnalysis, 60000); // Refresh every 60s
    return () => clearInterval(interval);
  }, []);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/paper-trading/analysis/positions');
      
      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
        // Auto-expand first position
        if (data.positions && data.positions.length > 0 && expandedPosition === null) {
          setExpandedPosition(data.positions[0].position.id);
        }
        setError(null);
      } else {
        setError('Failed to fetch analysis');
      }
    } catch (err) {
      setError('Failed to connect to API');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'HIGH': return 'text-red-600 bg-red-50 border-red-200';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'LOW': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getAssessmentColor = (assessment: string) => {
    switch (assessment) {
      case 'EXIT_NOW':
      case 'EXIT_SOON': return 'bg-red-100 text-red-800 border-red-300';
      case 'MONITOR':
      case 'CONSIDER_EXIT': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'HOLD': return 'bg-green-100 text-green-800 border-green-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'CRITICAL': return '🔴';
      case 'HIGH': return '🟠';
      case 'MEDIUM': return '🟡';
      case 'LOW': return '🟢';
      default: return '⚪';
    }
  };

  const getProximityColor = (proximity: number) => {
    if (proximity >= 100) return 'text-red-700 font-bold';
    if (proximity >= 80) return 'text-red-600 font-semibold';
    if (proximity >= 50) return 'text-yellow-600 font-semibold';
    return 'text-green-600';
  };

  if (loading && !analysis) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Head>
          <title>Position Analysis - Trading System</title>
        </Head>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Analyzing positions...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !analysis) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Head>
          <title>Position Analysis - Trading System</title>
        </Head>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Position Analysis - What Went Wrong?</title>
      </Head>

      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-white">Trading System</h1>
            <nav className="flex space-x-6">
              <Link href="/" className="hover:text-blue-400 text-gray-300">Dashboard</Link>
              <Link href="/signals" className="hover:text-blue-400 text-gray-300">Signals</Link>
              <Link href="/trades" className="hover:text-blue-400 text-gray-300">Trades</Link>
              <Link href="/paper-trading" className="hover:text-blue-400 text-gray-300">Stock Trading</Link>
              <Link href="/position-analysis" className="text-blue-400 font-semibold">📊 Analysis</Link>
              <Link href="/options-trading" className="hover:text-blue-400 text-yellow-400">Nifty 50 Options</Link>
              <Link href="/backtest" className="hover:text-blue-400 text-gray-300">Backtest</Link>
            </nav>
          </div>
        </div>
      </header>
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">📊 Position Analysis</h2>
              <p className="mt-1 text-sm text-gray-500">Understanding what went wrong and why</p>
            </div>
            <Link href="/paper-trading" className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
              ← Back to Trading
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {analysis && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500">Total Positions</h3>
                <p className="mt-2 text-3xl font-bold text-gray-900">{analysis.total_positions}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500">Unrealized Loss</h3>
                <p className="mt-2 text-3xl font-bold text-red-600">
                  {formatCurrency(analysis.total_unrealized_loss)}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500">Common Issues</h3>
                <p className="mt-2 text-3xl font-bold text-orange-600">
                  {analysis.common_issues.length}
                </p>
              </div>
            </div>

            {/* Common Issues */}
            {analysis.common_issues.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">🔍 Common Issues Across All Positions</h2>
                <div className="space-y-3">
                  {analysis.common_issues.map((issue, idx) => (
                    <div key={idx} className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${getSeverityColor(issue.severity)}`}>
                              {issue.severity}
                            </span>
                            <span className="font-semibold">{issue.type.replace(/_/g, ' ')}</span>
                            <span className="text-sm">({issue.count} position{issue.count > 1 ? 's' : ''})</span>
                          </div>
                          <p className="mt-2 text-sm">{issue.description}</p>
                          <p className="mt-2 text-sm font-medium">💡 Lesson: {issue.lesson}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Individual Positions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">📈 Individual Position Analysis</h2>
              <div className="space-y-4">
                {analysis.positions.map((posAnalysis, idx) => {
                  const pos = posAnalysis.position;
                  const sig = posAnalysis.signal;
                  const isExpanded = expandedPosition === pos.id;

                  return (
                    <div key={pos.id} className="border rounded-lg overflow-hidden">
                      {/* Position Header */}
                      <div
                        className="bg-gray-50 p-4 cursor-pointer hover:bg-gray-100"
                        onClick={() => setExpandedPosition(isExpanded ? null : pos.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <span className="text-2xl font-bold text-gray-700">{idx + 1}</span>
                            <div>
                              <h3 className="text-lg font-bold text-gray-900">{pos.symbol}</h3>
                              <p className="text-sm text-gray-500">
                                Entry: {formatCurrency(pos.entry_price)} → Current: {formatCurrency(pos.current_price)}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-xl font-bold text-red-600">
                              {formatCurrency(pos.pnl)} ({formatPercent(pos.pnl_percent)})
                            </p>
                            <span className={`inline-block mt-1 px-3 py-1 rounded-full text-xs font-semibold border ${getAssessmentColor(posAnalysis.assessment)}`}>
                              {posAnalysis.assessment.replace(/_/g, ' ')}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="p-6 space-y-6">
                          {/* Signal Details */}
                          {sig && (
                            <div className="bg-blue-50 rounded-lg p-4">
                              <h4 className="font-bold text-blue-900 mb-3">📊 Entry Signal</h4>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <p className="text-blue-700 font-medium">Strategy</p>
                                  <p className="text-blue-900 font-semibold">{sig.strategy}</p>
                                </div>
                                <div>
                                  <p className="text-blue-700 font-medium">Confidence</p>
                                  <p className="text-blue-900 font-semibold">{sig.confidence}%</p>
                                </div>
                                <div>
                                  <p className="text-blue-700 font-medium">Risk:Reward</p>
                                  <p className="text-blue-900 font-semibold">1:{sig.risk_reward}</p>
                                </div>
                                <div>
                                  <p className="text-blue-700 font-medium">SL Proximity</p>
                                  <p className={getProximityColor(sig.sl_proximity_pct)}>{sig.sl_proximity_pct}%</p>
                                </div>
                              </div>
                              <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <p className="text-blue-700 font-medium">Target</p>
                                  <p className="text-blue-900">{formatCurrency(sig.target_price)} ({formatPercent(sig.target_pct)})</p>
                                </div>
                                <div>
                                  <p className="text-blue-700 font-medium">Stop Loss</p>
                                  <p className="text-blue-900">{formatCurrency(sig.stop_loss)} ({formatPercent(sig.sl_pct)})</p>
                                </div>
                              </div>
                              <div className="mt-3">
                                <p className="text-blue-700 font-medium text-sm">Reason</p>
                                <p className="text-blue-900 text-sm">{sig.reason}</p>
                              </div>
                            </div>
                          )}

                          {/* Issues */}
                          {posAnalysis.issues.length > 0 && (
                            <div>
                              <h4 className="font-bold text-gray-900 mb-3">❌ What Went Wrong</h4>
                              <div className="space-y-2">
                                {posAnalysis.issues.map((issue, i) => (
                                  <div key={i} className={`border rounded p-3 ${getSeverityColor(issue.severity)}`}>
                                    <div className="flex items-start space-x-2">
                                      <span className="text-xs font-semibold px-2 py-1 rounded bg-white">
                                        {issue.severity}
                                      </span>
                                      <div className="flex-1">
                                        <p className="font-medium">{issue.description}</p>
                                        <p className="text-sm mt-1">💡 {issue.lesson}</p>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Recommendations */}
                          {posAnalysis.recommendations.length > 0 && (
                            <div>
                              <h4 className="font-bold text-gray-900 mb-3">💡 Recommendation</h4>
                              {posAnalysis.recommendations.map((rec, i) => (
                                <div key={i} className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                                  <div className="flex items-start space-x-3">
                                    <span className="text-2xl">{getPriorityIcon(rec.priority)}</span>
                                    <div className="flex-1">
                                      <p className="font-bold text-indigo-900">
                                        {rec.action.replace(/_/g, ' ')}
                                      </p>
                                      <p className="text-indigo-800 mt-1">{rec.description}</p>
                                      <p className="text-sm text-indigo-700 mt-2">Why: {rec.reason}</p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Position Details */}
                          <div className="bg-gray-50 rounded-lg p-4">
                            <h4 className="font-bold text-gray-900 mb-3">📋 Position Details</h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <p className="text-gray-600">Quantity</p>
                                <p className="font-semibold text-gray-900">{pos.quantity}</p>
                              </div>
                              <div>
                                <p className="text-gray-600">Invested</p>
                                <p className="font-semibold text-gray-900">{formatCurrency(pos.invested)}</p>
                              </div>
                              <div>
                                <p className="text-gray-600">Current Value</p>
                                <p className="font-semibold text-gray-900">{formatCurrency(pos.current_value)}</p>
                              </div>
                              <div>
                                <p className="text-gray-600">Duration</p>
                                <p className="font-semibold text-gray-900">{pos.duration_hours.toFixed(1)} hrs</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Key Lessons */}
            <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg shadow p-6 text-white">
              <h2 className="text-xl font-bold mb-4">🎯 Key Lessons Learned</h2>
              <ul className="space-y-2">
                {analysis.key_lessons.map((lesson, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="mr-2">✓</span>
                    <span>{lesson}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
