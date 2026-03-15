import { useEffect, useState } from 'react'
import Link from 'next/link'
import { marketAPI, signalsAPI, tradesAPI, portfolioAPI } from '@/lib/api'

export default function Dashboard() {
  const [marketData, setMarketData] = useState<any>(null)
  const [signals, setSignals] = useState<any[]>([])
  const [portfolio, setPortfolio] = useState<any>(null)
  const [tradeStats, setTradeStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
    const interval = setInterval(loadDashboardData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadDashboardData = async () => {
    try {
      const [marketRes, signalsRes, portfolioRes, tradesRes] = await Promise.all([
        marketAPI.getOverview(),
        signalsAPI.getLatest(10, 70),
        portfolioAPI.getCombinedSummary(),  // Use combined summary for stocks + options
        tradesAPI.getStats(30)
      ])

      setMarketData(marketRes.data)
      setSignals(signalsRes.data)
      setPortfolio(portfolioRes.data)
      setTradeStats(tradesRes.data)
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
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
              <Link href="/trades" className="hover:text-blue-400">Trades</Link>
              <Link href="/paper-trading" className="hover:text-blue-400">Stock Trading</Link>
              <Link href="/position-analysis" className="hover:text-blue-400">📊 Analysis</Link>
              <Link href="/options-trading" className="hover:text-blue-400 text-yellow-400">Nifty 50 Options</Link>
              <Link href="/backtest" className="hover:text-blue-400">Backtest</Link>
            </nav>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Market Overview */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="text-gray-400 text-sm">NIFTY 50</div>
              <div className="text-2xl font-bold">{marketData?.nifty_price?.toFixed(2)}</div>
              <div className={`text-sm ${marketData?.nifty_change >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
                {marketData?.nifty_change >= 0 ? '+' : ''}{marketData?.nifty_change?.toFixed(2)}%
              </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="text-gray-400 text-sm">BANK NIFTY</div>
              <div className="text-2xl font-bold">{marketData?.banknifty_price?.toFixed(2)}</div>
              <div className={`text-sm ${marketData?.banknifty_change >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
                {marketData?.banknifty_change >= 0 ? '+' : ''}{marketData?.banknifty_change?.toFixed(2)}%
              </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="text-gray-400 text-sm">INDIA VIX</div>
              <div className="text-2xl font-bold">{marketData?.india_vix?.toFixed(2)}</div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="text-gray-400 text-sm">Portfolio P&L</div>
              <div className={`text-2xl font-bold ${portfolio?.total_pnl >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
                ₹{portfolio?.total_pnl?.toLocaleString()}
              </div>
            </div>
          </div>
        </section>

        {/* Trading Stats */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Trading Statistics (30 Days)</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="text-gray-400 text-sm">Total Trades</div>
              <div className="text-2xl font-bold">{tradeStats?.total_trades}</div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="text-gray-400 text-sm">Win Rate</div>
              <div className="text-2xl font-bold text-bull-green">{tradeStats?.win_rate?.toFixed(1)}%</div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="text-gray-400 text-sm">Avg Win</div>
              <div className="text-2xl font-bold text-bull-green">₹{tradeStats?.avg_win?.toFixed(0)}</div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="text-gray-400 text-sm">Avg Loss</div>
              <div className="text-2xl font-bold text-bear-red">₹{tradeStats?.avg_loss?.toFixed(0)}</div>
            </div>
          </div>
        </section>

        {/* Latest Signals */}
        <section>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Top Signals (Today)</h2>
            <Link href="/signals" className="text-blue-400 hover:text-blue-300">View All →</Link>
          </div>
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left">Symbol</th>
                  <th className="px-4 py-3 text-left">Strategy</th>
                  <th className="px-4 py-3 text-left">Signal</th>
                  <th className="px-4 py-3 text-right">Entry</th>
                  <th className="px-4 py-3 text-right">Target</th>
                  <th className="px-4 py-3 text-right">SL</th>
                  <th className="px-4 py-3 text-right">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {signals.map((signal, idx) => (
                  <tr key={idx} className="border-t border-gray-700">
                    <td className="px-4 py-3 font-medium">{signal.symbol}</td>
                    <td className="px-4 py-3 text-sm text-gray-400">{signal.strategy}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        signal.signal_type === 'BUY' ? 'bg-bull-green/20 text-bull-green' : 'bg-bear-red/20 text-bear-red'
                      }`}>
                        {signal.signal_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">₹{signal.entry_price?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-bull-green">₹{signal.target_price?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-bear-red">₹{signal.stop_loss?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right">
                      <span className={`font-medium ${
                        signal.confidence >= 80 ? 'text-bull-green' : signal.confidence >= 60 ? 'text-yellow-400' : 'text-gray-400'
                      }`}>
                        {signal.confidence?.toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}
