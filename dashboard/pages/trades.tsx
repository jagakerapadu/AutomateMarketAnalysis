import { useEffect, useState } from 'react'
import Link from 'next/link'
import { tradesAPI } from '@/lib/api'

export default function TradesPage() {
  const [trades, setTrades] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [filter])

  const loadData = async () => {
    try {
      setLoading(true)
      const [tradesRes, statsRes] = await Promise.all([
        tradesAPI.getAll(100, filter === 'ALL' ? undefined : filter),
        tradesAPI.getStats(30)
      ])
      setTrades(tradesRes.data)
      setStats(statsRes.data)
    } catch (error) {
      console.error('Error loading trades:', error)
    } finally {
      setLoading(false)
    }
  }

  const getPnlColor = (pnl: number) => {
    return pnl >= 0 ? 'text-green-400' : 'text-red-400'
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold">Trading System</h1>
            <nav className="flex space-x-6">
              <Link href="/" className="hover:text-blue-400">Dashboard</Link>
              <Link href="/signals" className="hover:text-blue-400">Signals</Link>
              <Link href="/trades" className="text-blue-400 font-semibold">Trades</Link>
              <Link href="/paper-trading" className="hover:text-blue-400">Stock Trading</Link>
              <Link href="/position-analysis" className="hover:text-blue-400">📊 Analysis</Link>
              <Link href="/options-trading" className="hover:text-blue-400 text-yellow-400">Nifty 50 Options</Link>
              <Link href="/backtest" className="hover:text-blue-400">Backtest</Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Trade History</h1>
          <p className="text-gray-400">All executed trades with P&L</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400">Total Trades</div>
              <div className="text-2xl font-bold">{stats.total_trades || 0}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400">Win Rate</div>
              <div className="text-2xl font-bold text-green-400">
                {stats.win_rate ? (stats.win_rate * 100).toFixed(1) : 0}%
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400">Total P&L</div>
              <div className={`text-2xl font-bold ${getPnlColor(stats.total_pnl || 0)}`}>
                ₹{(stats.total_pnl || 0).toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400">Avg P&L per Trade</div>
              <div className={`text-2xl font-bold ${getPnlColor(stats.avg_pnl || 0)}`}>
                ₹{(stats.avg_pnl || 0).toFixed(2)}
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-4">
            <label className="text-sm text-gray-400">Filter:</label>
            <div className="flex gap-2">
              {['ALL', 'OPEN', 'CLOSED', 'CANCELLED'].map((status) => (
                <button
                  key={status}
                  onClick={() => setFilter(status)}
                  className={`px-4 py-2 rounded ${
                    filter === status
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
            <div className="text-sm text-gray-400 ml-auto">
              Showing: {trades.length} trades
            </div>
          </div>
        </div>

        {/* Trades Table */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-400">Loading trades...</div>
          </div>
        ) : trades.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <p className="text-gray-400 text-lg">No trades found</p>
            <p className="text-gray-500 text-sm mt-2">Start trading or generate sample data</p>
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Trade ID</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Symbol</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Type</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Qty</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Entry</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Exit</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Entry Time</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Exit Time</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">P&L</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {trades.map((trade, index) => (
                  <tr key={trade.id || index} className="hover:bg-gray-750">
                    <td className="px-4 py-3 text-sm text-gray-400 font-mono">
                      {trade.trade_id || `#${trade.id}`}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium">{trade.symbol}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`font-semibold ${
                        trade.order_type === 'BUY' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {trade.order_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right">{trade.quantity}</td>
                    <td className="px-4 py-3 text-sm text-right">₹{trade.entry_price?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-right">
                      {trade.exit_price ? `₹${trade.exit_price.toFixed(2)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {new Date(trade.entry_time).toLocaleString('en-IN', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {trade.exit_time 
                        ? new Date(trade.exit_time).toLocaleString('en-IN', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })
                        : '-'
                      }
                    </td>
                    <td className={`px-4 py-3 text-sm text-right font-bold ${getPnlColor(trade.pnl || 0)}`}>
                      {trade.pnl !== null && trade.pnl !== undefined 
                        ? `₹${trade.pnl.toFixed(2)}`
                        : '-'
                      }
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${
                        trade.status === 'CLOSED' ? 'bg-gray-700 text-gray-300' :
                        trade.status === 'OPEN' ? 'bg-blue-900 text-blue-300' :
                        'bg-red-900 text-red-300'
                      }`}>
                        {trade.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}
