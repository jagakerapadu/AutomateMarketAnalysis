import { useEffect, useState } from 'react'
import Link from 'next/link'
import { signalsAPI } from '@/lib/api'

export default function SignalsPage() {
  const [signals, setSignals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [minConfidence, setMinConfidence] = useState(70)

  useEffect(() => {
    loadSignals()
  }, [minConfidence])

  const loadSignals = async () => {
    try {
      setLoading(true)
      const response = await signalsAPI.getLatest(50, minConfidence)
      setSignals(response.data)
    } catch (error) {
      console.error('Error loading signals:', error)
    } finally {
      setLoading(false)
    }
  }

  const getSignalColor = (type: string) => {
    return type === 'BUY' ? 'text-green-400' : 'text-red-400'
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return 'text-green-400'
    if (confidence >= 75) return 'text-yellow-400'
    return 'text-gray-400'
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
                <Link href="/signals" className="text-white border-b-2 border-blue-500">Signals</Link>
                <Link href="/trades" className="text-gray-400 hover:text-white">Trades</Link>
                <Link href="/paper-trading" className="text-gray-400 hover:text-white">Stock Trading</Link>
                <Link href="/position-analysis" className="text-gray-400 hover:text-white">📊 Analysis</Link>
                <Link href="/options-trading" className="text-yellow-400 hover:text-white">Nifty 50 Options</Link>
                <Link href="/backtest" className="text-gray-400 hover:text-white">Backtest</Link>
              </nav>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Trading Signals</h1>
          <p className="text-gray-400">Latest signals from all strategies</p>
        </div>

        {/* Filters */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-4">
            <label className="text-sm text-gray-400">Min Confidence:</label>
            <select
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            >
              <option value={60}>60%</option>
              <option value={70}>70%</option>
              <option value={75}>75%</option>
              <option value={80}>80%</option>
              <option value={85}>85%</option>
              <option value={90}>90%</option>
            </select>
            <div className="text-sm text-gray-400 ml-auto">
              Total Signals: {signals.length}
            </div>
          </div>
        </div>

        {/* Signals Table */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-400">Loading signals...</div>
          </div>
        ) : signals.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <p className="text-gray-400 text-lg">No signals found</p>
            <p className="text-gray-500 text-sm mt-2">Lower the minimum confidence or run the data pipeline</p>
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Time</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Symbol</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Signal</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Strategy</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Confidence</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Entry</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Target</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Stop Loss</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {signals.map((signal, index) => (
                  <tr key={signal.id || index} className="hover:bg-gray-750">
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {new Date(signal.timestamp).toLocaleString('en-IN', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium">{signal.symbol}</td>
                    <td className={`px-4 py-3 text-sm font-bold ${getSignalColor(signal.signal_type)}`}>
                      {signal.signal_type}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">{signal.strategy}</td>
                    <td className={`px-4 py-3 text-sm font-semibold ${getConfidenceColor(signal.confidence)}`}>
                      {signal.confidence}%
                    </td>
                    <td className="px-4 py-3 text-sm text-right">₹{signal.entry_price?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-right text-green-400">₹{signal.target_price?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-right text-red-400">₹{signal.stop_loss?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${
                        signal.status === 'ACTIVE' ? 'bg-blue-900 text-blue-300' :
                        signal.status === 'FILLED' ? 'bg-green-900 text-green-300' :
                        'bg-gray-700 text-gray-400'
                      }`}>
                        {signal.status}
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
