import { NextPageContext } from 'next'

interface ErrorProps {
  statusCode?: number
  message?: string
}

function Error({ statusCode, message }: ErrorProps) {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-white mb-4">
          {statusCode || 'Error'}
        </h1>
        <p className="text-xl text-gray-400 mb-8">
          {message || 
            (statusCode
              ? `An error ${statusCode} occurred on server`
              : 'An error occurred on client')}
        </p>
        <a
          href="/"
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Go back home
        </a>
      </div>
    </div>
  )
}

Error.getInitialProps = ({ res, err }: NextPageContext) => {
  const statusCode = res ? res.statusCode : err ? err.statusCode : 404
  return { statusCode }
}

export default Error
