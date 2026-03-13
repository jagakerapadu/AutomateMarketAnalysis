import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import Head from 'next/head'
import { useEffect } from 'react'

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    // Prevent hydration errors
    if (typeof window !== 'undefined') {
      // Client-side-only code
    }
  }, [])

  return (
    <>
      <Head>
        <title>Trading System Dashboard</title>
        <meta name="description" content="Hedge Fund Style Trading System" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <Component {...pageProps} />
    </>
  )
}
