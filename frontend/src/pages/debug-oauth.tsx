'use client';

import { useState, useEffect } from 'react';

export default function DebugOAuth() {
  const [info, setInfo] = useState<any>({});

  useEffect(() => {
    // Gather all relevant info
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || 'NOT SET';
    const currentOrigin = typeof window !== 'undefined' ? window.location.origin : 'SSR';
    const currentHref = typeof window !== 'undefined' ? window.location.href : 'SSR';
    
    setInfo({
      clientId,
      clientIdFirst20: clientId.substring(0, 20) + '...',
      currentOrigin,
      currentHref,
      protocol: typeof window !== 'undefined' ? window.location.protocol : 'SSR',
      hostname: typeof window !== 'undefined' ? window.location.hostname : 'SSR',
      port: typeof window !== 'undefined' ? window.location.port : 'SSR',
    });
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-8">OAuth Debug Info</h1>
      
      <div className="space-y-6 max-w-2xl">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-yellow-400">Current Browser Info</h2>
          <div className="space-y-2 font-mono text-sm">
            <p><span className="text-gray-400">Origin:</span> <span className="text-green-400">{info.currentOrigin}</span></p>
            <p><span className="text-gray-400">Protocol:</span> {info.protocol}</p>
            <p><span className="text-gray-400">Hostname:</span> {info.hostname}</p>
            <p><span className="text-gray-400">Port:</span> {info.port || '(default)'}</p>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-yellow-400">Google OAuth Config</h2>
          <div className="space-y-2 font-mono text-sm">
            <p><span className="text-gray-400">Client ID:</span> <span className="text-blue-400">{info.clientIdFirst20}</span></p>
            <p><span className="text-gray-400">Full Client ID:</span></p>
            <p className="text-xs text-gray-500 break-all">{info.clientId}</p>
          </div>
        </div>

        <div className="bg-red-900/50 border border-red-500 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-red-400">⚠️ Required Google Cloud Console Settings</h2>
          <p className="mb-4 text-gray-300">Go to Google Cloud Console → APIs & Services → Credentials → Your OAuth 2.0 Client ID</p>
          
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-yellow-400">Authorized JavaScript Origins (add EXACTLY):</h3>
              <ul className="list-disc list-inside mt-2 space-y-1 font-mono text-sm">
                <li className="text-green-400">{info.currentOrigin}</li>
                <li>http://localhost:3000</li>
                <li>http://127.0.0.1:3001</li>
                <li>http://127.0.0.1:3000</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-yellow-400">Authorized Redirect URIs (add EXACTLY):</h3>
              <ul className="list-disc list-inside mt-2 space-y-1 font-mono text-sm">
                <li className="text-green-400">{info.currentOrigin}</li>
                <li>http://localhost:3000</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="bg-blue-900/50 border border-blue-500 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-blue-400">🔧 Troubleshooting Steps</h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-300">
            <li>Ensure OAuth client type is <strong>"Web application"</strong></li>
            <li>Copy the origin <span className="font-mono text-green-400">{info.currentOrigin}</span> EXACTLY</li>
            <li>No trailing slashes</li>
            <li>Use <strong>http</strong> not https for localhost</li>
            <li>After saving, wait 5-10 minutes</li>
            <li>Clear browser cache or use Incognito</li>
            <li>Hard refresh (Ctrl+Shift+R)</li>
          </ol>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-yellow-400">Quick Test</h2>
          <p className="mb-4 text-gray-300">While fixing Google OAuth, you can still use:</p>
          <ul className="list-disc list-inside space-y-2">
            <li><strong>Email/Password</strong>: Enter any email and password on login page</li>
            <li><strong>"Try Without Account"</strong>: Click for instant demo access</li>
          </ul>
          <a href="/login" className="inline-block mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg">
            Go to Login Page
          </a>
        </div>
      </div>
    </div>
  );
}
