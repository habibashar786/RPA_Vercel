import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import toast from 'react-hot-toast';
import Script from 'next/script';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

// Declare google global
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          renderButton: (element: HTMLElement, config: any) => void;
        };
      };
    };
  }
}

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [googleReady, setGoogleReady] = useState(false);

  // Check API
  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then(res => res.ok ? setApiStatus('online') : setApiStatus('offline'))
      .catch(() => setApiStatus('offline'));
      
    // Check if already logged in
    const token = localStorage.getItem('auth_token');
    if (token) {
      router.push('/dashboard');
    }
  }, [router]);

  // Google OAuth callback
  const handleGoogleCallback = async (response: any) => {
    if (!response.credential) {
      toast.error('Google sign-in failed');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: response.credential })
      });
      const data = await res.json();
      
      if (data.access_token) {
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        toast.success(`Welcome, ${data.user.name}!`);
        router.push('/dashboard');
      } else {
        toast.error(data.detail || 'Google auth failed');
      }
    } catch (err) {
      toast.error('Google sign-in failed');
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize Google Sign-In
  useEffect(() => {
    if (googleReady && window.google && GOOGLE_CLIENT_ID) {
      try {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCallback,
          auto_select: false,
        });

        const buttonDiv = document.getElementById('google-btn');
        if (buttonDiv) {
          window.google.accounts.id.renderButton(buttonDiv, {
            theme: 'filled_black',
            size: 'large',
            width: 350,
            text: 'continue_with',
          });
        }
      } catch (e) {
        console.error('Google init error:', e);
      }
    }
  }, [googleReady]);

  // Email/Password login
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (apiStatus === 'offline') {
      toast.error('Backend offline');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email || 'demo@test.com', password: password || 'demo' })
      });
      const data = await res.json();
      
      if (data.access_token) {
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        toast.success('Welcome to ResearchAI!');
        router.push('/dashboard');
      }
    } catch (err) {
      toast.error('Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  // Demo login
  const handleDemoLogin = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'demo@researchai.app', password: 'demo123' })
      });
      const data = await res.json();
      
      if (data.access_token) {
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        toast.success('Welcome to ResearchAI!');
        router.push('/dashboard');
      }
    } catch (err) {
      toast.error('Demo login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Google Script */}
      {GOOGLE_CLIENT_ID && (
        <Script
          src="https://accounts.google.com/gsi/client"
          onLoad={() => setGoogleReady(true)}
          strategy="afterInteractive"
        />
      )}

      <div className="login-page">
        <style jsx>{`
          .login-page {
            min-height: 100vh;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            font-family: system-ui, -apple-system, sans-serif;
          }
          .login-container {
            width: 100%;
            max-width: 420px;
          }
          .logo-section {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            justify-content: center;
            margin-bottom: 2rem;
            text-decoration: none;
            color: white;
          }
          .logo-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.75rem;
          }
          .logo-text {
            font-size: 1.5rem;
            font-weight: bold;
          }
          .logo-sub {
            font-size: 0.75rem;
            color: rgba(255,255,255,0.4);
          }
          .status-badge {
            display: flex;
            justify-content: center;
            margin-bottom: 1.5rem;
          }
          .status-pill {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 999px;
            font-size: 0.875rem;
          }
          .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
          }
          .status-online {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
          }
          .status-online .status-dot {
            background: #22c55e;
          }
          .status-offline {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
          }
          .status-offline .status-dot {
            background: #ef4444;
          }
          .login-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 2rem;
            backdrop-filter: blur(10px);
          }
          .card-title {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 0.5rem;
          }
          .card-subtitle {
            color: rgba(255,255,255,0.6);
            text-align: center;
            margin-bottom: 2rem;
          }
          .google-section {
            margin-bottom: 1.5rem;
          }
          #google-btn {
            display: flex;
            justify-content: center;
            min-height: 44px;
          }
          .divider {
            display: flex;
            align-items: center;
            margin: 1.5rem 0;
            color: rgba(255,255,255,0.4);
            font-size: 0.875rem;
          }
          .divider::before,
          .divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(255,255,255,0.1);
          }
          .divider span {
            padding: 0 1rem;
          }
          .form-group {
            margin-bottom: 1rem;
          }
          .form-label {
            display: block;
            color: rgba(255,255,255,0.8);
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
          }
          .form-input {
            width: 100%;
            padding: 0.875rem 1rem;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.05);
            color: white;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
            box-sizing: border-box;
          }
          .form-input:focus {
            border-color: rgba(99, 102, 241, 0.5);
          }
          .form-input::placeholder {
            color: rgba(255,255,255,0.3);
          }
          .btn-primary {
            width: 100%;
            padding: 1rem;
            border-radius: 12px;
            border: none;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: opacity 0.2s, transform 0.2s;
          }
          .btn-primary:hover:not(:disabled) {
            transform: translateY(-1px);
          }
          .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .demo-section {
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(255,255,255,0.1);
          }
          .btn-demo {
            width: 100%;
            padding: 0.875rem;
            border-radius: 12px;
            border: 1px solid rgba(99, 102, 241, 0.3);
            background: rgba(99, 102, 241, 0.1);
            color: #818cf8;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: background 0.2s;
          }
          .btn-demo:hover:not(:disabled) {
            background: rgba(99, 102, 241, 0.2);
          }
          .btn-demo:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .demo-hint {
            color: rgba(255,255,255,0.4);
            font-size: 0.75rem;
            text-align: center;
            margin-top: 0.5rem;
          }
          .signup-link {
            color: rgba(255,255,255,0.6);
            text-align: center;
            margin-top: 1.5rem;
          }
          .signup-link a {
            color: #818cf8;
            text-decoration: none;
          }
          .features-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-top: 2rem;
          }
          .feature-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            color: white;
          }
          .feature-icon {
            font-size: 1.5rem;
            margin-bottom: 0.25rem;
          }
          .feature-label {
            font-size: 0.75rem;
            color: rgba(255,255,255,0.6);
          }
          .no-google-warning {
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            color: #f59e0b;
            font-size: 0.875rem;
            text-align: center;
          }
        `}</style>

        <div className="login-container">
          {/* Logo */}
          <Link href="/" className="logo-section">
            <div className="logo-icon">🧠</div>
            <div>
              <div className="logo-text">ResearchAI</div>
              <div className="logo-sub">v2.1 • 12 AI Agents</div>
            </div>
          </Link>

          {/* API Status */}
          <div className="status-badge">
            <div className={`status-pill ${apiStatus === 'online' ? 'status-online' : 'status-offline'}`}>
              <div className="status-dot" />
              {apiStatus === 'online' ? 'Backend Online' : apiStatus === 'offline' ? 'Backend Offline' : 'Checking...'}
            </div>
          </div>

          {/* Login Card */}
          <div className="login-card">
            <h2 className="card-title">Welcome Back</h2>
            <p className="card-subtitle">Sign in to generate research proposals</p>

            {/* Google Sign-In */}
            {GOOGLE_CLIENT_ID ? (
              <div className="google-section">
                <div id="google-btn"></div>
              </div>
            ) : (
              <div className="no-google-warning">
                ⚠️ Google OAuth not configured.<br />
                <small>Set NEXT_PUBLIC_GOOGLE_CLIENT_ID in .env.local</small>
              </div>
            )}

            {/* Divider */}
            <div className="divider">
              <span>or continue with email</span>
            </div>

            {/* Email Form */}
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="form-input"
                  disabled={isLoading}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="form-input"
                  disabled={isLoading}
                />
              </div>

              <button type="submit" className="btn-primary" disabled={isLoading || apiStatus === 'offline'}>
                {isLoading ? '⏳ Signing in...' : 'Sign In →'}
              </button>
            </form>

            {/* Demo Login */}
            <div className="demo-section">
              <button onClick={handleDemoLogin} className="btn-demo" disabled={isLoading || apiStatus === 'offline'}>
                ✨ Try Demo (No Account Needed)
              </button>
              <p className="demo-hint">Instant access with Premium features</p>
            </div>

            {/* Signup Link */}
            <p className="signup-link">
              New to ResearchAI? <Link href="/signup">Create account</Link>
            </p>
          </div>

          {/* Features Grid */}
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">📄</div>
              <div className="feature-label">15,000+ Words</div>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <div className="feature-label">Q1 Standard</div>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <div className="feature-label">12 AI Agents</div>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📚</div>
              <div className="feature-label">Harvard Style</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
