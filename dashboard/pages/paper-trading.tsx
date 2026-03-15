import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';

interface Portfolio {
  total_capital: number;
  available_cash: number;
  invested_amount: number;
  total_pnl: number;
  today_pnl: number;
  positions_count: number;
  updated_at: string;
}

interface Position {
  id: number;
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number | null;
  invested_value: number;
  current_value: number | null;
  pnl: number | null;
  pnl_percent: number | null;
  position_type: string;
  opened_at: string;
}

interface Order {
  order_id: string;
  symbol: string;
  order_type: string;
  quantity: number;
  executed_price: number;
  status: string;
  placed_at: string;
  executed_at: string;
}

interface Stats {
  total_orders: number;
  buy_orders: number;
  sell_orders: number;
  total_pnl: number;
  today_pnl: number;
  active_positions: number;
  capital_deployed: number;
  available_cash: number;
}

export default function PaperTrading() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const [portfolioRes, positionsRes, ordersRes, statsRes] = await Promise.all([
        fetch('http://localhost:8000/api/paper-trading/portfolio'),
        fetch('http://localhost:8000/api/paper-trading/positions'),
        fetch('http://localhost:8000/api/paper-trading/orders?limit=10'),
        fetch('http://localhost:8000/api/paper-trading/stats')
      ]);

      if (portfolioRes.ok) setPortfolio(await portfolioRes.json());
      if (positionsRes.ok) setPositions(await positionsRes.json());
      if (ordersRes.ok) setOrders(await ordersRes.json());
      if (statsRes.ok) setStats(await statsRes.json());

      setError(null);
    } catch (err) {
      setError('Failed to fetch data');
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

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    // Format: "12 Mar 2026, 3:25 PM IST" - matches Kite format
    const day = date.getDate();
    const month = date.toLocaleString('en-US', { month: 'short' });
    const year = date.getFullYear();
    const time = date.toLocaleString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
    return `${day} ${month} ${year}, ${time} IST`;
  };

  return (
    <>
      <Head>
        <title>Stock Trading | Trading System</title>
      </Head>

      <div className="min-h-screen bg-gray-900 text-white">
        {/* Header Navigation */}
        <header className="bg-gray-800 border-b border-gray-700">
          <div className="container mx-auto px-4 py-4">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold">Trading System</h1>
              <nav className="flex space-x-6">
                <Link href="/" className="hover:text-blue-400">Dashboard</Link>
                <Link href="/signals" className="hover:text-blue-400">Signals</Link>
                <Link href="/trades" className="hover:text-blue-400">Trades</Link>
                <Link href="/paper-trading" className="text-blue-400 font-semibold">Stock Trading</Link>
                <Link href="/position-analysis" className="hover:text-blue-400">📊 Analysis</Link>
                <Link href="/options-trading" className="hover:text-blue-400 text-yellow-400">Nifty 50 Options</Link>
                <Link href="/backtest" className="hover:text-blue-400">Backtest</Link>
              </nav>
            </div>
          </div>
        </header>

        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold mb-2">📊 Stock Paper Trading</h1>
              <p className="text-gray-400">Virtual stock trading with live market data</p>
            </div>

          {loading && !portfolio && (
            <div className="text-center text-gray-400 py-8">Loading paper trading data...</div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-3 rounded mb-6">⚠️ {error}</div>
          )}

          {/* Portfolio Summary */}
          {portfolio && (
          <section className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Portfolio Summary</h2>
              <div className="text-sm text-gray-400">
                Last updated: {(() => {
                  const date = new Date(portfolio.updated_at);
                  const day = date.getDate();
                  const month = date.toLocaleString('en-US', { month: 'short' });
                  const time = date.toLocaleString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true
                  }).toLowerCase();
                  return `${day} ${month}, ${time}`;
                })()}
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Total Capital</h3>
                <p className="text-2xl font-bold">{formatCurrency(portfolio.total_capital)}</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Available Cash</h3>
                <p className="text-2xl font-bold">{formatCurrency(portfolio.available_cash)}</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Invested</h3>
                <p className="text-2xl font-bold">{formatCurrency(portfolio.invested_amount)}</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Total P&L</h3>
                <p className={`text-2xl font-bold ${portfolio.total_pnl >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
                  {formatCurrency(portfolio.total_pnl)}
                </p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Today P&L</h3>
                <p className={`text-2xl font-bold ${portfolio.today_pnl >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
                  {formatCurrency(portfolio.today_pnl)}
                </p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Active Positions</h3>
                <p className="text-2xl font-bold">{portfolio.positions_count}</p>
              </div>
            </div>
          </section>
          )}

          {/* Statistics */}
          {stats && (
          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Trading Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Total Orders</h3>
                <p className="text-2xl font-bold">{stats.total_orders}</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Buy Orders</h3>
                <p className="text-2xl font-bold">{stats.buy_orders}</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Sell Orders</h3>
                <p className="text-2xl font-bold">{stats.sell_orders}</p>
              </div>
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-gray-400 text-sm mb-2">Capital Deployed</h3>
                <p className="text-2xl font-bold">{formatCurrency(stats.capital_deployed)}</p>
              </div>
            </div>
          </section>
          )}

          {/* Current Positions */}
          <section className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Current Positions ({positions.length})</h2>
            {positions.length > 0 && (
              <Link href="/position-analysis" className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium transition-colors">
                📊 Analyze Positions
              </Link>
            )}
          </div>
          {positions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-800">
                    <th className="text-left p-3 border-b border-gray-700">Symbol</th>
                    <th className="text-left p-3 border-b border-gray-700">Quantity</th>
                    <th className="text-left p-3 border-b border-gray-700">Avg Price</th>
                    <th className="text-left p-3 border-b border-gray-700">Current Price</th>
                    <th className="text-left p-3 border-b border-gray-700">Invested</th>
                    <th className="text-left p-3 border-b border-gray-700">Current Value</th>
                    <th className="text-left p-3 border-b border-gray-700">P&L</th>
                    <th className="text-left p-3 border-b border-gray-700">P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                      <td className="p-3"><strong>{pos.symbol}</strong></td>
                      <td className="p-3">{pos.quantity}</td>
                      <td className="p-3">{formatCurrency(pos.avg_price)}</td>
                      <td className="p-3">{pos.current_price ? formatCurrency(pos.current_price) : '-'}</td>
                      <td className="p-3">{formatCurrency(pos.invested_value)}</td>
                      <td className="p-3">{pos.current_value ? formatCurrency(pos.current_value) : '-'}</td>
                      <td className={`p-3 ${pos.pnl && pos.pnl >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
                        {pos.pnl ? formatCurrency(pos.pnl) : '-'}
                      </td>
                      <td className={`p-3 ${pos.pnl_percent && pos.pnl_percent >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
                        {pos.pnl_percent ? formatPercent(pos.pnl_percent) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">No open positions</div>
          )}
          </section>

          {/* Order History */}
          <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Recent Orders</h2>
          {orders.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-800">
                    <th className="text-left p-3 border-b border-gray-700">Time</th>
                    <th className="text-left p-3 border-b border-gray-700">Symbol</th>
                    <th className="text-left p-3 border-b border-gray-700">Type</th>
                    <th className="text-left p-3 border-b border-gray-700">Quantity</th>
                    <th className="text-left p-3 border-b border-gray-700">Price</th>
                    <th className="text-left p-3 border-b border-gray-700">Status</th>
                    <th className="text-left p-3 border-b border-gray-700">Order ID</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.order_id} className="border-b border-gray-800 hover:bg-gray-800/50">
                      <td className="p-3">{formatDateTime(order.executed_at || order.placed_at)}</td>
                      <td className="p-3"><strong>{order.symbol}</strong></td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-sm ${order.order_type === 'BUY' ? 'bg-bull-green/20 text-bull-green' : 'bg-bear-red/20 text-bear-red'}`}>
                          {order.order_type}
                        </span>
                      </td>
                      <td className="p-3">{order.quantity}</td>
                      <td className="p-3">{formatCurrency(order.executed_price)}</td>
                      <td className="p-3">
                        <span className="px-2 py-1 rounded text-sm bg-green-900/20 text-green-400">{order.status}</span>
                      </td>
                      <td className="p-3 text-gray-400 text-xs">{order.order_id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">No orders yet</div>
          )}
          </section>

          {/* Instructions */}
          <section className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">💡 How to Use</h2>
            <div className="space-y-4">
              <p><strong>Paper trading</strong> lets you test your strategies with virtual money and real market data.</p>
              <ul className="list-disc pl-6 space-y-2 my-4">
                <li>✅ Start with ₹10,00,000 virtual capital</li>
                <li>✅ All trading signals automatically executed</li>
                <li>✅ Live market prices from Zerodha</li>
                <li>✅ Automatic stop-loss (-2%) and target (+3%)</li>
                <li>✅ Risk management: Max 20% per trade</li>
              </ul>
              <p><strong>To start paper trading:</strong></p>
              <code className="block bg-gray-900 text-bull-green p-4 rounded mt-2 font-mono text-sm">
                python start_paper_trading.py
              </code>
            </div>
          </section>
          </div>
        </main>
      </div>
    </>
  );
}
