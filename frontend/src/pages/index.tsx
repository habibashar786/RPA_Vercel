import Link from 'next/link';

export default function Home() {
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%)',
      color: 'white',
      fontFamily: 'system-ui, sans-serif'
    }}>
      {/* Navigation */}
      <nav style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1.5rem 2rem',
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.5rem'
          }}>🧠</div>
          <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>ResearchAI</span>
        </div>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          <Link href="/login" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none' }}>
            Sign In
          </Link>
          <Link href="/dashboard" style={{
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            padding: '0.75rem 1.5rem',
            borderRadius: '12px',
            textDecoration: 'none',
            color: 'white',
            fontWeight: '600'
          }}>
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main style={{
        maxWidth: '1000px',
        margin: '0 auto',
        padding: '4rem 2rem',
        textAlign: 'center'
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          background: 'rgba(99, 102, 241, 0.2)',
          padding: '0.5rem 1rem',
          borderRadius: '999px',
          marginBottom: '2rem',
          fontSize: '0.875rem'
        }}>
          ✨ Powered by 12 Specialized AI Agents
        </div>

        <h1 style={{
          fontSize: 'clamp(2.5rem, 8vw, 4.5rem)',
          fontWeight: 'bold',
          marginBottom: '1.5rem',
          lineHeight: '1.1'
        }}>
          Generate <span style={{
            background: 'linear-gradient(135deg, #6366f1, #ec4899, #06b6d4)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>Q1 Journal</span>
          <br />Research Proposals
        </h1>

        <p style={{
          fontSize: '1.25rem',
          color: 'rgba(255,255,255,0.6)',
          maxWidth: '600px',
          margin: '0 auto 2.5rem',
          lineHeight: '1.6'
        }}>
          Transform your research idea into a comprehensive, publication-ready 
          proposal using our multi-agent AI system.
        </p>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link href="/login" style={{
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            padding: '1rem 2rem',
            borderRadius: '12px',
            textDecoration: 'none',
            color: 'white',
            fontWeight: '600',
            fontSize: '1.1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            Start Generating →
          </Link>
        </div>

        {/* Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '1.5rem',
          marginTop: '4rem'
        }}>
          {[
            { value: '12', label: 'AI Agents', icon: '🤖' },
            { value: '15K+', label: 'Words Generated', icon: '📄' },
            { value: 'Q1', label: 'Journal Standard', icon: '🎯' },
            { value: '100%', label: 'Harvard Citations', icon: '📚' },
          ].map((stat) => (
            <div key={stat.label} style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '16px',
              padding: '1.5rem',
              backdropFilter: 'blur(10px)'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{stat.icon}</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{stat.value}</div>
              <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.875rem' }}>{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Features */}
        <div style={{
          marginTop: '5rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1.5rem',
          textAlign: 'left'
        }}>
          {[
            { title: 'Literature Review', desc: 'Comprehensive analysis of 30+ research papers', icon: '📖' },
            { title: 'Methodology Design', desc: 'AI-powered research methodology generation', icon: '🔬' },
            { title: 'Multiple Formats', desc: 'Export as PDF, DOCX, or Markdown', icon: '📁' },
            { title: 'Subscription Tiers', desc: 'Free, Standard, and Premium plans', icon: '👑' },
            { title: 'Proofreading Agent', desc: 'Automatic validation and consistency checks', icon: '✅' },
            { title: 'Watermark Control', desc: 'Clean PDFs for premium subscribers', icon: '🔐' },
          ].map((feature) => (
            <div key={feature.title} style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '16px',
              padding: '1.5rem',
              backdropFilter: 'blur(10px)'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>{feature.icon}</div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}>{feature.title}</h3>
              <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem' }}>{feature.desc}</p>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid rgba(255,255,255,0.1)',
        padding: '2rem',
        textAlign: 'center',
        color: 'rgba(255,255,255,0.4)',
        fontSize: '0.875rem'
      }}>
        © 2024 ResearchAI by FOMA Digital Solution • v2.1.0 • 12 AI Agents
      </footer>
    </div>
  );
}
