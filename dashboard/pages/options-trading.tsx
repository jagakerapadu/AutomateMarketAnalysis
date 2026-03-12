import React, { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown, TrendingUp, DollarSign, Target, AlertTriangle } from 'lucide-react';
import Head from 'next/head';
import Link from 'next/link';

interface OptionsPortfolio {
  total_capital: number;
  available_cash: number;
  invested_amount: number;
  total_pnl: number;
  today_pnl: number;
  total_premium_paid: number;
  total_premium_received: number;
  positions_count: number;
  updated_at: string;
}

interface OptionsPosition {
  id: number;
  symbol: string;
  strike: number;
  option_type: string; // CE or PE
  expiry_date: string;
  quantity: number;
  entry_premium: number;
  current_premium: number | null;
  invested_value: number;
  current_value: number | null;
  pnl: number | null;
  pnl_percent: number | null;
  position_type: string;
  strategy: string | null;
  days_to_expiry: number | null;
  opened_at: string;
  updated_at: string;
}

interface OptionsOrder {
  order_id: string;
  symbol: string;
  strike: number;
  option_type: string;
  expiry_date: string;
  order_type: string;
  quantity: number;
  executed_premium: number | null;
  total_cost: number | null;
  status: string;
  strategy: string | null;
  confidence: number | null;
  placed_at: string;
}

interface OptionsSignal {
  id: number;
  symbol: string;
  strike: number;
  option_type: string;
  expiry_date: string;
  signal_type: string;
  strategy: string;
  entry_premium: number;
  target_premium: number | null;
  stop_loss_premium: number | null;
  confidence: number | null;
  status: string;
  reason: string | null;
  timestamp: string;
}

export default function OptionsTrading() {
  const [portfolio, setPortfolio] = useState<OptionsPortfolio | null>(null);
  const [positions, setPositions] = useState<OptionsPosition[]>([]);
  const [orders, setOrders] = useState<OptionsOrder[]>([]);
  const [signals, setSignals] = useState<OptionsSignal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [portfolioRes, positionsRes, ordersRes, signalsRes] = await Promise.all([
        fetch('http://localhost:8000/api/options-trading/portfolio'),
        fetch('http://localhost:8000/api/options-trading/positions'),
        fetch('http://localhost:8000/api/options-trading/orders?limit=10'),
        fetch('http://localhost:8000/api/options-trading/signals?status=PENDING&limit=5')
      ]);

      setPortfolio(await portfolioRes.json());
      setPositions(await positionsRes.json());
      setOrders(await ordersRes.json());
      setSignals(await signalsRes.json());
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch options trading data:', error);
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-IN', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading Options Trading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Head>
        <title>Index Options Trading | Trading System</title>
      </Head>

      {/* Header Navigation */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold">Trading System</h1>
            <nav className="flex space-x-6">
              <Link href="/" className="hover:text-blue-400">Dashboard</Link>
              <Link href="/signals" className="hover:text-blue-400">Signals</Link>
              <Link href="/trades" className="hover:text-blue-400">Trades</Link>
              <Link href="/paper-trading" className="hover:text-blue-400">Stock Trading</Link>
              <Link href="/position-analysis" className="hover:text-blue-400">📊 Analysis</Link>
              <Link href="/options-trading" className="text-yellow-400 font-semibold">Nifty 50 Options</Link>
              <Link href="/backtest" className="hover:text-blue-400">Backtest</Link>
            </nav>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">📊 Index Options Trading</h1>
            <p className="text-sm text-gray-400 mt-1">Nifty 50 & Bank Nifty Options Paper Trading</p>
          </div>
          <div className="text-sm text-gray-400">
            Last updated: {portfolio?.updated_at ? formatDateTime(portfolio.updated_at) : 'Never'}
          </div>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-900 border border-blue-700 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-300">Index Options Only</h3>
              <div className="mt-1 text-sm text-blue-200">
                Currently trading <strong>Nifty 50</strong> and <strong>Bank Nifty</strong> index options. Stock options (Reliance, TCS, etc.) not yet supported.
              </div>
            </div>
          </div>
        </div>

        {/* Portfolio Summary Cards */}
        {portfolio && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Total Capital</span>
                <DollarSign className="w-5 h-5 text-blue-400" />
              </div>
              <div className="text-2xl font-bold">{formatCurrency(portfolio.total_capital)}</div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Available Cash</span>
                <DollarSign className="w-5 h-5 text-green-400" />
              </div>
              <div className="text-2xl font-bold">{formatCurrency(portfolio.available_cash)}</div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Invested</span>
                <TrendingUp className="w-5 h-5 text-orange-400" />
              </div>
              <div className="text-2xl font-bold">{formatCurrency(portfolio.invested_amount)}</div>
            </div>

            <div className={`bg-gray-800 rounded-lg p-6 border ${portfolio.total_pnl >= 0 ? 'border-green-500' : 'border-red-500'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Total P&L</span>
                {portfolio.total_pnl >= 0 ? 
                  <ArrowUp className="w-5 h-5 text-green-400" /> : 
                  <ArrowDown className="w-5 h-5 text-red-400" />
                }
              </div>
              <div className={`text-2xl font-bold ${portfolio.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {formatCurrency(portfolio.total_pnl)}
              </div>
            </div>
          </div>
        )}

        {/* Active Positions */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8 border border-gray-700">
          <h2 className="text-xl font-bold mb-4 flex items-center">
            <Target className="w-6 h-6 mr-2 text-blue-400" />
            Active Options Positions ({positions.length})
          </h2>
          {positions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-gray-700">
                  <tr className="text-left text-gray-400 text-sm">
                    <th className="pb-3">Symbol</th>
                    <th className="pb-3">Strike</th>
                    <th className="pb-3">Type</th>
                    <th className="pb-3">Expiry</th>
                    <th className="pb-3">Qty</th>
                    <th className="pb-3">Entry</th>
                    <th className="pb-3">Current</th>
                    <th className="pb-3">P&L</th>
                    <th className="pb-3">Strategy</th>
                    <th className="pb-3">Days Left</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.id} className="border-b border-gray-700 hover:bg-gray-750">
                      <td className="py-4 font-medium">{pos.symbol}</td>
                      <td className="py-4">{pos.strike}</td>
                      <td className="py-4">
                        <span className={`px-2 py-1 rounded text-xs ${pos.option_type === 'CE' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                          {pos.option_type}
                        </span>
                      </td>
                      <td className="py-4 text-sm">{new Date(pos.expiry_date).toLocaleDateString('en-IN')}</td>
                      <td className="py-4">{pos.quantity} lots</td>
                      <td className="py-4">₹{pos.entry_premium.toFixed(2)}</td>
                      <td className="py-4">₹{(pos.current_premium || 0).toFixed(2)}</td>
                      <td className={`py-4 font-medium ${(pos.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {pos.pnl !== null ? formatCurrency(pos.pnl) : 'N/A'}
                        {pos.pnl_percent !== null && ` (${formatPercent(pos.pnl_percent)})`}
                      </td>
                      <td className="py-4">
                        <span className="px-2 py-1 rounded bg-blue-900 text-blue-300 text-xs">
                          {pos.strategy || 'Manual'}
                        </span>
                      </td>
                      <td className="py-4">
                        <span className={`px-2 py-1 rounded text-xs ${(pos.days_to_expiry || 0) <= 1 ? 'bg-red-900 text-red-300' : 'bg-gray-700 text-gray-300'}`}>
                          {pos.days_to_expiry || 0} days
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">
              No active options positions
            </div>
          )}
        </div>

        {/* Pending Signals */}
        {signals.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8 border border-yellow-700">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <AlertTriangle className="w-6 h-6 mr-2 text-yellow-400" />
              Pending Signals ({signals.length})
            </h2>
            <div className="space-y-3">
              {signals.map((signal) => (
                <div key={signal.id} className="bg-gray-750 rounded p-4 border border-gray-700">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-lg">
                        {signal.symbol} {signal.strike} {signal.option_type}
                        <span className="ml-3 px-2 py-1 rounded bg-blue-900 text-blue-300 text-xs">
                          {signal.strategy}
                        </span>
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        Entry: ₹{signal.entry_premium.toFixed(2)} | 
                        Target: ₹{(signal.target_premium || 0).toFixed(2)} | 
                        SL: ₹{(signal.stop_loss_premium || 0).toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{signal.reason}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-yellow-400">
                        {signal.confidence?.toFixed(0)}% Confidence
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDateTime(signal.timestamp)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Orders */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-bold mb-4">Recent Orders</h2>
          {orders.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-gray-700">
                  <tr className="text-left text-gray-400 text-sm">
                    <th className="pb-3">Order ID</th>
                    <th className="pb-3">Symbol</th>
                    <th className="pb-3">Strike/Type</th>
                    <th className="pb-3">Action</th>
                    <th className="pb-3">Qty</th>
                    <th className="pb-3">Premium</th>
                    <th className="pb-3">Total Cost</th>
                    <th className="pb-3">Strategy</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.order_id} className="border-b border-gray-700 hover:bg-gray-750">
                      <td className="py-3 text-sm font-mono">{order.order_id.slice(-10)}</td>
                      <td className="py-3 font-medium">{order.symbol}</td>
                      <td className="py-3">
                        {order.strike} 
                        <span className={`ml-2 px-2 py-1 rounded text-xs ${order.option_type === 'CE' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                          {order.option_type}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs ${order.order_type === 'BUY' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                          {order.order_type}
                        </span>
                      </td>
                      <td className="py-3">{order.quantity} lots</td>
                      <td className="py-3">₹{(order.executed_premium || 0).toFixed(2)}</td>
                      <td className="py-3 font-medium">{formatCurrency(order.total_cost || 0)}</td>
                      <td className="py-3">
                        <span className="px-2 py-1 rounded bg-blue-900 text-blue-300 text-xs">
                          {order.strategy || 'Manual'}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs ${order.status === 'EXECUTED' ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'}`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-400">{formatDateTime(order.placed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">
              No orders yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
