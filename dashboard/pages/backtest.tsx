import { useEffect, useState } from 'react'
import Link from 'next/link'
import { backtestAPI } from '@/lib/api'

export default function BacktestPage() {
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadBacktests()
  }, [])

  const loadBacktests = async () => {
    try {
      const response = await backtestAPI.getResults(20)
      setResults(response.data)
    } catch (error) {
      console.error('Error loading backtests:', error)
    } finally {
      setLoading(false)
    }
  }

  const getMetricColor = (value: number, isPositive: boolean = true) => {
    if (isPositive) {
      return value >= 0 ? 'text-green-400' : 'text-red-400'
    }
    return value <= 0.5 ? 'text-red-400' : value <= 0.7 ? 'text-yellow-400' : 'text-green-400'
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-6">
              <Link href="/" className="text-2xl font-bold">Trading System</Link>
              <nav className="flex gap-4">
                <Link href="/" className="text-gray-400 hover:text-white">Dashboard</Link>
                <Link href="/signals" className="text-gray-400 hover:text-white">Signals</Link>
                <Link href="/trades" className="text-gray-400 hover:text-white">Trades</Link>
                <Link href="/paper-trading" className="text-gray-400 hover:text-white">Stock Trading</Link>
                <Link href="/position-analysis" className="text-gray-400 hover:text-white">📊 Analysis</Link>
                <Link href="/options-trading" className="text-yellow-400 hover:text-white">Nifty 50 Options</Link>
                <Link href="/backtest" className="text-white border-b-2 border-blue-500">Backtest</Link>
              </nav>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Strategy Backtests</h1>
          <p className="text-gray-400">Historical performance analysis of trading strategies</p>
        </div>

        {/* Info Box */}
        <div className="bg-blue-900 border border-blue-700 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <div className="text-blue-400 text-xl">ℹ️</div>
            <div>
              <h3 className="font-semibold text-blue-200 mb-1">No Backtest Results Yet</h3>
              <p className="text-blue-300 text-sm">
                Run backtests to evaluate strategy performance on historical data. 
                This helps validate strategies before live trading.
              </p>
              <div className="mt-3 text-sm text-blue-300">
                <p className="font-mono">Run: py services\backtest\backtest_engine.py</p>
              </div>
            </div>
          </div>
        </div>

        {/* Backtest Results */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-400">Loading backtest results...</div>
          </div>
        ) : results.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <p className="text-gray-400 text-lg mb-4">No backtest results found</p>
            <p className="text-gray-500 text-sm mb-6">
              Backtests test your strategies against historical data to measure performance
            </p>
            <div className="bg-gray-700 rounded-lg p-6 max-w-2xl mx-auto text-left">
              <h3 className="font-semibold mb-3">How to run a backtest:</h3>
              <ol className="space-y-2 text-sm text-gray-300">
                <li>1. Ensure you have historical data in the database</li>
                <li>2. Run: <code className="bg-gray-800 px-2 py-1 rounded">py services\backtest\backtest_engine.py</code></li>
                <li>3. Results will appear here with key metrics:
                  <ul className="ml-6 mt-2 space-y-1 text-gray-400">
                    <li>• Total Return %</li>
                    <li>• Sharpe Ratio</li>
                    <li>• Max Drawdown</li>
                    <li>• Win Rate</li>
                    <li>• Profit Factor</li>
                  </ul>
                </li>
              </ol>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={result.id || index} className="bg-gray-800 rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold">{result.strategy_name}</h3>
                    <p className="text-sm text-gray-400">
                      {result.symbol} | {result.start_date} to {result.end_date}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-400">Total Return</div>
                    <div className={`text-2xl font-bold ${getMetricColor(result.total_return)}`}>
                      {(result.total_return * 100).toFixed(2)}%
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div>
                    <div className="text-sm text-gray-400">Total Trades</div>
                    <div className="text-lg font-semibold">{result.total_trades}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">Win Rate</div>
                    <div className={`text-lg font-semibold ${getMetricColor(result.win_rate, false)}`}>
                      {(result.win_rate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">Sharpe Ratio</div>
                    <div className={`text-lg font-semibold ${
                      result.sharpe_ratio >= 1.5 ? 'text-green-400' :
                      result.sharpe_ratio >= 1 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {result.sharpe_ratio?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">Max Drawdown</div>
                    <div className="text-lg font-semibold text-red-400">
                      {(result.max_drawdown * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">Profit Factor</div>
                    <div className={`text-lg font-semibold ${
                      result.profit_factor >= 2 ? 'text-green-400' :
                      result.profit_factor >= 1 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {result.profit_factor?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-700 grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Avg Win:</span>{' '}
                    <span className="text-green-400">₹{result.avg_win?.toFixed(2) || 0}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Avg Loss:</span>{' '}
                    <span className="text-red-400">₹{result.avg_loss?.toFixed(2) || 0}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Total P&L:</span>{' '}
                    <span className={getMetricColor(result.total_pnl)}>
                      ₹{result.total_pnl?.toFixed(2) || 0}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
