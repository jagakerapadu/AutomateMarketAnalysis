import Link from 'next/link'

export default function ServerError() {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-red-500 mb-4">500</h1>
        <p className="text-2xl text-gray-400 mb-8">Server Error</p>
        <p className="text-gray-500 mb-8">
          Something went wrong on our end. Please try again later.
        </p>
        <Link
          href="/"
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Go back home
        </Link>
      </div>
    </div>
  )
}
