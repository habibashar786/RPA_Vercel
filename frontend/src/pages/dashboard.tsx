import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import toast from 'react-hot-toast';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

type SubscriptionTier = 'free' | 'non_permanent' | 'permanent';

interface User {
  id: string;
  name: string;
  email: string;
  subscription_tier: SubscriptionTier;
}

interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_stage: string | null;
  stages_completed: string[];
  message: string;
  error: string | null;
}

interface ProposalResult {
  topic: string;
  word_count: number;
  sections: Array<{ title: string; content: string }>;
  generated_at: string;
  full_content?: string;
}

interface ScopusCompliance {
  overall_score: number;
  q1_ready: boolean;
  quality_level: string;
  acceptance_probability: { estimate: number; confidence_interval: number[]; confidence_level: number };
  criteria_scores: Record<string, number>;
  recommendations: string[];
}

interface ReviewerFeedback {
  persona_id: string;
  persona_name: string;
  focus_area: string;
  score: number;
  recommendation: string;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
}

interface ReviewResult {
  overall_assessment: 'accept' | 'minor_revision' | 'major_revision' | 'reject';
  consensus_score: number;
  agreement_level: string;
  reviewer_feedback: ReviewerFeedback[];
  aggregated_strengths: string[];
  aggregated_weaknesses: string[];
  priority_revisions: string[];
}

// Visualization Artifact Types
interface GanttPhase {
  id: string;
  name: string;
  start_month: number;
  duration_months: number;
  dependencies: string[];
  status: string;
}

interface WBSNode {
  id: string;
  name: string;
  deliverable: string;
  children?: WBSNode[];
}

interface RTMRequirement {
  id: string;
  description: string;
  source_section: string;
  delivered_by: string;
  status: string;
  verification: string;
}

interface KanbanCard {
  id: string;
  title: string;
  column: string;
  agent: string;
  priority: string;
}

interface VisualizationArtifact {
  type: string;
  title: string;
  format: string;
  content: any;
  mermaid_code?: string;
  placement: string;
}

interface ArtifactsResponse {
  proposal_id: string;
  topic: string;
  version: string;
  artifacts: {
    version: string;
    artifact_count: number;
    artifacts: VisualizationArtifact[];
  };
}

interface TOCEntry {
  title: string;
  level: string;
  page: string;
  number: string;
  indent: number;
}

interface StructuredTOC {
  version: string;
  title: string;
  entry_count: number;
  entries: TOCEntry[];
  rendering_instructions: {
    leader_style: string;
    font_family: string;
    font_size: string;
    line_spacing: number;
    indent_per_level: string;
    page_alignment: string;
  };
}

export default function Dashboard() {
  const router = useRouter();
  
  // Auth state
  const [user, setUser] = useState<User | null>(null);
  const [subscriptionTier, setSubscriptionTier] = useState<SubscriptionTier>('permanent');
  
  // Form state
  const [topic, setTopic] = useState('');
  const [keyPoints, setKeyPoints] = useState<string[]>(['', '', '']);
  const [citationStyle, setCitationStyle] = useState('harvard');
  const [targetWords, setTargetWords] = useState(15000);
  
  // System state
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [agentCount, setAgentCount] = useState(18);
  const [apiVersion, setApiVersion] = useState('2.4.0');
  
  // Job state
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const pollRef = useRef<NodeJS.Timeout | null>(null);
  
  // Result state
  const [result, setResult] = useState<ProposalResult | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewHtml, setPreviewHtml] = useState('');
  const [isDownloading, setIsDownloading] = useState(false);
  
  // Scopus and Review state
  const [scopusScore, setScopusScore] = useState<ScopusCompliance | null>(null);
  const [reviewResult, setReviewResult] = useState<ReviewResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // NEW: Visualization Artifacts state
  const [artifacts, setArtifacts] = useState<VisualizationArtifact[]>([]);
  const [structuredTOC, setStructuredTOC] = useState<StructuredTOC | null>(null);
  const [activeTab, setActiveTab] = useState<'export' | 'scopus' | 'review' | 'artifacts' | 'toc' | 'validation'>('export');
  const [selectedArtifact, setSelectedArtifact] = useState<string>('gantt_chart');
  const [isLoadingArtifacts, setIsLoadingArtifacts] = useState(false);
  
  // Mermaid rendering ref
  const mermaidRef = useRef<HTMLDivElement>(null);
  const [mermaidLoaded, setMermaidLoaded] = useState(false);

  // Load Mermaid.js dynamically
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
    script.async = true;
    script.onload = () => {
      (window as any).mermaid?.initialize({ 
        startOnLoad: false,
        theme: 'dark',
        themeVariables: {
          primaryColor: '#6366f1',
          primaryTextColor: '#fff',
          primaryBorderColor: '#818cf8',
          lineColor: '#818cf8',
          secondaryColor: '#1e1e2e',
          tertiaryColor: '#2a2a3e'
        }
      });
      setMermaidLoaded(true);
    };
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  // Render Mermaid diagram when artifact changes
  useEffect(() => {
    if (mermaidLoaded && mermaidRef.current && artifacts.length > 0) {
      const artifact = artifacts.find(a => a.type === selectedArtifact);
      if (artifact?.mermaid_code) {
        const mermaid = (window as any).mermaid;
        if (mermaid) {
          mermaidRef.current.innerHTML = '';
          const id = `mermaid-${Date.now()}`;
          mermaid.render(id, artifact.mermaid_code).then((result: any) => {
            if (mermaidRef.current) {
              mermaidRef.current.innerHTML = result.svg;
            }
          }).catch((err: any) => {
            console.error('Mermaid render error:', err);
            if (mermaidRef.current) {
              mermaidRef.current.innerHTML = `<pre style="color: #818cf8; font-size: 0.8rem;">${artifact.mermaid_code}</pre>`;
            }
          });
        }
      }
    }
  }, [mermaidLoaded, selectedArtifact, artifacts]);

  // Initialize
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      router.push('/login');
      return;
    }

    try {
      const userData = localStorage.getItem('user');
      if (userData) {
        const parsed = JSON.parse(userData) as User;
        setUser(parsed);
        setSubscriptionTier(parsed.subscription_tier || 'permanent');
      }
    } catch (e) {
      console.error('Failed to parse user data:', e);
    }

    fetch(`${API_URL}/health`)
      .then(res => res.json())
      .then(data => {
        setApiStatus('online');
        setAgentCount(data.agents_registered || 18);
        setApiVersion(data.version || '2.4.0');
      })
      .catch(() => setApiStatus('offline'));

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [router]);

  // Fetch artifacts after proposal completion
  const fetchArtifacts = useCallback(async (jobId: string) => {
    setIsLoadingArtifacts(true);
    try {
      // Fetch visualization artifacts
      const artifactsRes = await fetch(`${API_URL}/api/v2/artifacts/${jobId}`);
      if (artifactsRes.ok) {
        const data: ArtifactsResponse = await artifactsRes.json();
        setArtifacts(data.artifacts.artifacts || []);
      }
      
      // Fetch structured TOC
      const tocRes = await fetch(`${API_URL}/api/v2/toc/${jobId}`);
      if (tocRes.ok) {
        const tocData = await tocRes.json();
        setStructuredTOC(tocData.toc);
      }
    } catch (err) {
      console.error('Failed to fetch artifacts:', err);
    } finally {
      setIsLoadingArtifacts(false);
    }
  }, []);

  // Fetch Scopus score
  const fetchScopusScore = useCallback(async (jobId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v2/scopus/compliance/${jobId}`);
      if (res.ok) {
        const data = await res.json();
        setScopusScore(data.compliance);
      }
    } catch (err) {
      console.error('Failed to fetch Scopus score:', err);
    }
  }, []);

  // Fetch Review simulation
  const fetchReviewSimulation = useCallback(async (jobId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v2/review/simulate/${jobId}`);
      if (res.ok) {
        const data = await res.json();
        setReviewResult(data.review);
      }
    } catch (err) {
      console.error('Failed to fetch review:', err);
    }
  }, []);

  // Poll job status
  const startPolling = useCallback((jobId: string) => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }

    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/api/proposals/jobs/${jobId}`);
        if (!res.ok) throw new Error('Failed to fetch status');
        
        const data: JobStatus = await res.json();
        setJobStatus(data);

        if (data.status === 'completed') {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
          setIsGenerating(false);
          
          const resultRes = await fetch(`${API_URL}/api/proposals/jobs/${jobId}/result`);
          if (resultRes.ok) {
            const resultData = await resultRes.json();
            setResult(resultData.result);
            toast.success(`🎉 Done! ${resultData.result?.word_count?.toLocaleString() || '15,000+'} words generated`);
            
            // Fetch all analysis data
            await Promise.all([
              fetchArtifacts(jobId),
              fetchScopusScore(jobId),
              fetchReviewSimulation(jobId)
            ]);
          }
        } else if (data.status === 'failed') {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
          setIsGenerating(false);
          toast.error(data.error || 'Generation failed');
        }
      } catch (err) {
        console.error('Poll error:', err);
      }
    };

    poll();
    pollRef.current = setInterval(poll, 3000);
  }, [fetchArtifacts, fetchScopusScore, fetchReviewSimulation]);

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (apiStatus === 'offline') {
      toast.error('Backend is offline');
      return;
    }
    
    if (topic.length < 10) {
      toast.error('Topic must be at least 10 characters');
      return;
    }
    
    const validPoints = keyPoints.filter(k => k.trim().length > 0);
    if (validPoints.length < 3) {
      toast.error('Please provide at least 3 key points');
      return;
    }

    setIsGenerating(true);
    setJobStatus(null);
    setResult(null);
    setArtifacts([]);
    setScopusScore(null);
    setReviewResult(null);
    setStructuredTOC(null);

    try {
      const res = await fetch(`${API_URL}/api/proposals/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          key_points: validPoints,
          citation_style: citationStyle,
          target_word_count: targetWords,
          student_name: user?.name || 'Researcher'
        })
      });
      
      if (!res.ok) throw new Error('Failed to start generation');
      
      const data = await res.json();
      setCurrentJobId(data.job_id);
      toast.success(`Started! Estimated: ${data.estimated_time_minutes} minutes`);
      startPolling(data.job_id);
    } catch (err) {
      setIsGenerating(false);
      toast.error('Failed to start generation');
    }
  };

  // Reset
  const handleReset = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setCurrentJobId(null);
    setJobStatus(null);
    setResult(null);
    setArtifacts([]);
    setScopusScore(null);
    setReviewResult(null);
    setStructuredTOC(null);
    setIsGenerating(false);
    setActiveTab('export');
  };

  // Preview
  const handlePreview = async () => {
    const id = currentJobId;
    if (!id) {
      toast.error('No proposal to preview');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/proposals/${id}/preview?subscription_tier=${subscriptionTier}`);
      if (!res.ok) throw new Error('Preview failed');
      
      const data = await res.json();
      setPreviewHtml(data.html_preview || '');
      setShowPreview(true);
      
      if (data.is_limited) {
        toast('Free tier: 300 word preview limit', { icon: '⚠️' });
      }
    } catch {
      toast.error('Failed to load preview');
    }
  };

  // Download
  const handleDownload = async (format: 'pdf' | 'docx' | 'markdown' | 'latex' | 'overleaf') => {
    const id = currentJobId;
    if (!id) {
      toast.error('No proposal to download');
      return;
    }

    if (subscriptionTier === 'free' && format === 'pdf') {
      toast.error('Upgrade to Standard or Premium for PDF export');
      return;
    }

    setIsDownloading(true);
    const toastId = toast.loading(`Generating ${format.toUpperCase()}...`);

    try {
      const res = await fetch(`${API_URL}/api/proposals/${id}/export/${format}?subscription_tier=${subscriptionTier}`);
      if (!res.ok) throw new Error('Export failed');
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = format === 'markdown' ? 'md' : format === 'latex' ? 'tex' : format === 'overleaf' ? 'zip' : format;
      a.download = `research_proposal.${ext}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      const msg = subscriptionTier === 'non_permanent' && format === 'pdf' 
        ? 'Downloaded (with watermark)' 
        : 'Downloaded successfully!';
      toast.success(msg, { id: toastId });
    } catch {
      toast.error('Download failed', { id: toastId });
    } finally {
      setIsDownloading(false);
    }
  };

  // Logout
  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  // Update key point
  const updateKeyPoint = (index: number, value: string) => {
    const newKeyPoints = [...keyPoints];
    newKeyPoints[index] = value;
    setKeyPoints(newKeyPoints);
  };

  // Add key point
  const addKeyPoint = () => {
    if (keyPoints.length < 8) {
      setKeyPoints([...keyPoints, '']);
    }
  };

  // Remove key point
  const removeKeyPoint = (index: number) => {
    if (keyPoints.length > 3) {
      setKeyPoints(keyPoints.filter((_, i) => i !== index));
    }
  };

  // Tier info
  const getTierInfo = () => {
    const tiers = {
      free: { label: 'Free', color: '#9ca3af', bg: 'rgba(107, 114, 128, 0.2)' },
      non_permanent: { label: '✨ Standard', color: '#60a5fa', bg: 'rgba(59, 130, 246, 0.2)' },
      permanent: { label: '👑 Premium', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.2)' }
    };
    return tiers[subscriptionTier];
  };

  // Get current artifact
  const getCurrentArtifact = () => {
    return artifacts.find(a => a.type === selectedArtifact);
  };

  // Render RTM Table
  const renderRTMTable = (requirements: RTMRequirement[]) => (
    <div className="rtm-table-container">
      <table className="rtm-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Description</th>
            <th>Source</th>
            <th>Agent</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((req) => (
            <tr key={req.id}>
              <td className="rtm-id">{req.id}</td>
              <td>{req.description}</td>
              <td className="rtm-source">{req.source_section}</td>
              <td className="rtm-agent">{req.delivered_by}</td>
              <td className="rtm-status">{req.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  // Render Kanban Board
  const renderKanbanBoard = (content: { columns: string[]; cards: KanbanCard[]; stats: any }) => (
    <div className="kanban-board">
      {content.columns.map((column) => (
        <div key={column} className="kanban-column">
          <div className="kanban-column-header">
            <span>{column}</span>
            <span className="kanban-count">
              {content.cards.filter(c => c.column === column).length}
            </span>
          </div>
          <div className="kanban-cards">
            {content.cards
              .filter(c => c.column === column)
              .map((card) => (
                <div key={card.id} className={`kanban-card priority-${card.priority}`}>
                  <div className="kanban-card-title">{card.title}</div>
                  <div className="kanban-card-agent">{card.agent}</div>
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );

  // Render WBS Tree
  const renderWBSTree = (levels: any[]) => {
    const renderNode = (node: any, depth: number = 0) => (
      <div key={node.id} className="wbs-node" style={{ marginLeft: `${depth * 20}px` }}>
        <div className="wbs-node-header">
          <span className="wbs-id">{node.id}</span>
          <span className="wbs-name">{node.name}</span>
          {node.deliverable && <span className="wbs-deliverable">→ {node.deliverable}</span>}
        </div>
        {node.children?.map((child: any) => renderNode(child, depth + 1))}
      </div>
    );
    
    return (
      <div className="wbs-tree">
        {levels.map((level) => (
          <div key={level.id}>
            {level.children?.map((child: any) => renderNode(child, 0))}
          </div>
        ))}
      </div>
    );
  };

  const tierInfo = getTierInfo();
  const progress = result ? 100 : (jobStatus?.progress || 0);
  const currentArtifact = getCurrentArtifact();

  // =========================================================================
  // VALIDATION PANEL COMPONENT (v2.7.1) - Enhanced Turnitin Compliance
  // ContentSnapshot + MetricRows + Refinement Panel + Certificate Viewer
  // =========================================================================
  
  // MetricRow Sub-Component - Color-coded status display
  const MetricRow = ({ name, value, threshold, unit = '%' }: { 
    name: string; 
    value: number; 
    threshold: number; 
    unit?: string 
  }) => {
    const passed = value <= threshold;
    const nearThreshold = value > threshold * 0.8 && value <= threshold;
    const status = passed ? (nearThreshold ? 'warning' : 'pass') : 'fail';
    
    return (
      <div className={`metric-row metric-${status}`}>
        <div className="metric-name">{name}</div>
        <div className="metric-value">
          <span className="metric-number">{value.toFixed(1)}{unit}</span>
          <span className="metric-threshold">/ {threshold}{unit} max</span>
        </div>
        <div className={`metric-status status-${status}`}>
          {status === 'pass' && '✓ PASS'}
          {status === 'warning' && '⚠ NEAR'}
          {status === 'fail' && '✗ FAIL'}
        </div>
      </div>
    );
  };

  // Main ValidationPanel Component
  const ValidationPanel = ({ documentId, documentContent }: { documentId: string; documentContent: string }) => {
    const [validationState, setValidationState] = useState<'idle' | 'validating' | 'passed' | 'failed'>('idle');
    const [validationResult, setValidationResult] = useState<any>(null);
    const [validationError, setValidationError] = useState<string | null>(null);
    const [snapshotHash, setSnapshotHash] = useState<string | null>(null);
    const [snapshotTimestamp, setSnapshotTimestamp] = useState<string | null>(null);
    const [showRefinement, setShowRefinement] = useState(false);

    // Generate SHA-256 hash for ContentSnapshot
    const generateHash = async (content: string): Promise<string> => {
      const encoder = new TextEncoder();
      const data = encoder.encode(content);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    };

    const handleValidate = async () => {
      if (!documentId || !documentContent) {
        setValidationError('No document available for validation');
        return;
      }

      setValidationState('validating');
      setValidationError(null);
      setShowRefinement(false);

      try {
        // Create ContentSnapshot with hash and timestamp
        const hash = await generateHash(documentContent);
        const timestamp = new Date().toISOString();
        setSnapshotHash(hash);
        setSnapshotTimestamp(timestamp);

        const response = await fetch(`${API_URL}/api/v2/validation/validate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            document_id: documentId,
            content: documentContent,
            snapshot_hash: hash,
            snapshot_timestamp: timestamp,
            metadata: { 
              title: topic || 'Research Proposal',
              author: user?.name || 'Researcher'
            }
          })
        });

        const data = await response.json();
        setValidationResult(data);

        if (data.passed) {
          setValidationState('passed');
        } else if (data.success === false && data.error) {
          setValidationError(data.error);
          setValidationState('idle');
        } else {
          setValidationState('failed');
        }
      } catch (err) {
        setValidationError('Validation service unavailable. Please try again.');
        setValidationState('idle');
      }
    };

    const handleDownloadCertificate = async () => {
      if (!validationResult?.certificate?.pdf_base64) return;
      
      try {
        const byteCharacters = atob(validationResult.certificate.pdf_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-certificate-${validationResult.certificate.id}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Certificate download failed:', err);
      }
    };

    // Compute metrics for display
    const metrics = validationResult ? {
      similarity: validationResult.similarity_score || 0,
      singleSourceMax: Math.max(...(validationResult.source_breakdown?.map((s: any) => s.percentage) || [0])),
      aiProbability: validationResult.ai_detection_score || 0
    } : null;

    return (
      <div className="validation-panel-enhanced">
        {/* Header */}
        <div className="validation-header-enhanced">
          <div className="validation-icon-wrapper">
            <span className="validation-icon-large">🔍</span>
          </div>
          <div className="validation-title-section">
            <h3 className="validation-main-title">Originality Validation</h3>
            <p className="validation-sub-title">Pre-Submission Academic Screening</p>
          </div>
          {snapshotHash && (
            <div className="snapshot-badge">
              <span className="snapshot-icon">📎</span>
              <span className="snapshot-text">Snapshot Active</span>
            </div>
          )}
        </div>

        {/* Idle State - Initial View */}
        {validationState === 'idle' && !validationResult && (
          <div className="validation-idle-state">
            <div className="validation-description">
              <p>Validate your research proposal for originality and AI-generated content detection before institutional submission.</p>
            </div>
            
            <div className="threshold-cards">
              <div className="threshold-card">
                <div className="threshold-icon">📊</div>
                <div className="threshold-label">Similarity Index</div>
                <div className="threshold-value">≤15%</div>
              </div>
              <div className="threshold-card">
                <div className="threshold-icon">📄</div>
                <div className="threshold-label">Single Source</div>
                <div className="threshold-value">≤5%</div>
              </div>
              <div className="threshold-card">
                <div className="threshold-icon">🤖</div>
                <div className="threshold-label">AI Detection</div>
                <div className="threshold-value">≤20%</div>
              </div>
            </div>

            <div className="validation-disclaimer">
              <span className="disclaimer-icon">⚠️</span>
              <span>This validation does not replace official institutional plagiarism checks. Final evaluation remains the responsibility of the receiving institution.</span>
            </div>

            <button 
              onClick={handleValidate} 
              className="validate-btn-enhanced" 
              disabled={!documentContent}
            >
              <span className="btn-icon">✓</span>
              <span className="btn-text">Validate Originality</span>
            </button>
          </div>
        )}

        {/* Validating State - Progress */}
        {validationState === 'validating' && (
          <div className="validation-progress-enhanced">
            <div className="progress-spinner-container">
              <div className="progress-spinner-ring" />
              <div className="progress-spinner-core">🔍</div>
            </div>
            <h4 className="progress-title">Analyzing Document</h4>
            <p className="progress-subtitle">Creating immutable content snapshot...</p>
            
            <div className="progress-steps">
              <div className="progress-step active">
                <div className="step-indicator">1</div>
                <div className="step-label">Snapshot</div>
              </div>
              <div className="progress-step-connector" />
              <div className="progress-step">
                <div className="step-indicator">2</div>
                <div className="step-label">Analysis</div>
              </div>
              <div className="progress-step-connector" />
              <div className="progress-step">
                <div className="step-indicator">3</div>
                <div className="step-label">Evaluation</div>
              </div>
            </div>

            {snapshotHash && (
              <div className="snapshot-info">
                <div className="snapshot-hash">
                  <span className="hash-label">Document Hash:</span>
                  <span className="hash-value">{snapshotHash.substring(0, 16)}...{snapshotHash.substring(snapshotHash.length - 8)}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Passed State - Success */}
        {validationState === 'passed' && validationResult && metrics && (
          <div className="validation-result-enhanced passed">
            <div className="result-badge-container">
              <div className="result-badge passed">
                <span className="badge-icon">✅</span>
                <span className="badge-text">VALIDATION PASSED</span>
              </div>
            </div>
            
            <div className="result-message-box">
              <span className="message-icon">🎓</span>
              <span className="message-text">Ready for Institutional Submission</span>
            </div>

            {/* Metric Rows */}
            <div className="metrics-container">
              <h4 className="metrics-title">Validation Metrics</h4>
              <MetricRow name="Overall Similarity" value={metrics.similarity} threshold={15} />
              <MetricRow name="Single Source Max" value={metrics.singleSourceMax} threshold={5} />
              <MetricRow name="AI Detection" value={metrics.aiProbability} threshold={20} />
            </div>

            {/* Source Breakdown */}
            {validationResult.source_breakdown && validationResult.source_breakdown.length > 0 && (
              <div className="source-breakdown-enhanced">
                <h4 className="breakdown-title">📁 Source Distribution</h4>
                <div className="breakdown-list">
                  {validationResult.source_breakdown.slice(0, 5).map((source: any, i: number) => (
                    <div key={i} className="breakdown-item">
                      <span className="source-name">{source.source}</span>
                      <div className="source-bar-container">
                        <div className="source-bar" style={{ width: `${Math.min(source.percentage * 10, 100)}%` }} />
                      </div>
                      <span className="source-percentage">{source.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Certificate Section */}
            <div className="certificate-section">
              <div className="certificate-header">
                <span className="cert-icon">📜</span>
                <span className="cert-title">Compliance Certificate</span>
              </div>
              <div className="certificate-info">
                <div className="cert-detail">
                  <span className="detail-label">Certificate ID:</span>
                  <span className="detail-value">{validationResult.certificate?.id || 'N/A'}</span>
                </div>
                <div className="cert-detail">
                  <span className="detail-label">Document Hash:</span>
                  <span className="detail-value hash">{snapshotHash?.substring(0, 24)}...</span>
                </div>
                <div className="cert-detail">
                  <span className="detail-label">Validated:</span>
                  <span className="detail-value">{snapshotTimestamp ? new Date(snapshotTimestamp).toLocaleString() : 'N/A'}</span>
                </div>
              </div>
              <button onClick={handleDownloadCertificate} className="certificate-download-btn">
                <span>⬇</span> Download Certificate (PDF)
              </button>
            </div>

            {/* Read-only Notice */}
            <div className="readonly-notice">
              <span className="lock-icon">🔒</span>
              <div className="notice-content">
                <strong>Document Locked</strong>
                <p>Content is now read-only to preserve validation integrity.</p>
              </div>
            </div>
          </div>
        )}

        {/* Failed State - Needs Review */}
        {validationState === 'failed' && validationResult && metrics && (
          <div className="validation-result-enhanced failed">
            <div className="result-badge-container">
              <div className="result-badge failed">
                <span className="badge-icon">⚠️</span>
                <span className="badge-text">NEEDS REVIEW</span>
              </div>
            </div>

            {/* Metric Rows */}
            <div className="metrics-container">
              <h4 className="metrics-title">Validation Metrics</h4>
              <MetricRow name="Overall Similarity" value={metrics.similarity} threshold={15} />
              <MetricRow name="Single Source Max" value={metrics.singleSourceMax} threshold={5} />
              <MetricRow name="AI Detection" value={metrics.aiProbability} threshold={20} />
            </div>

            {/* Failure Reason */}
            <div className="failure-reason-box">
              <span className="reason-icon">❌</span>
              <span className="reason-text">{validationResult.failure_reason}</span>
            </div>

            {/* Source Breakdown */}
            {validationResult.source_breakdown && validationResult.source_breakdown.length > 0 && (
              <div className="source-breakdown-enhanced failed">
                <h4 className="breakdown-title">🚨 High Similarity Sources</h4>
                <div className="breakdown-list">
                  {validationResult.source_breakdown.map((source: any, i: number) => (
                    <div key={i} className="breakdown-item high">
                      <span className="source-name">{source.source}</span>
                      <div className="source-bar-container">
                        <div className="source-bar high" style={{ width: `${Math.min(source.percentage * 10, 100)}%` }} />
                      </div>
                      <span className="source-percentage high">{source.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Refinement Action Panel */}
            <div className="refinement-panel">
              <h4 className="refinement-title">🛠️ Controlled Refinement Options</h4>
              <p className="refinement-description">Manual refinement actions to improve originality scores:</p>
              
              <div className="refinement-actions">
                <button 
                  className="refinement-btn view-btn"
                  onClick={() => setShowRefinement(!showRefinement)}
                >
                  <span>🔍</span> View Highlighted Sections
                </button>
                <button className="refinement-btn apply-btn" disabled>
                  <span>✏️</span> Apply Controlled Refinement
                  <span className="coming-soon">Coming Soon</span>
                </button>
              </div>

              <div className="refinement-notice">
                <span>⚠️</span> Refinement does not auto-trigger re-validation. You must manually validate again.
              </div>
            </div>

            {/* Retry Button */}
            <button 
              onClick={() => { setValidationState('idle'); setValidationResult(null); setSnapshotHash(null); }} 
              className="retry-btn-enhanced"
            >
              <span>🔄</span> Reset & Validate Again
            </button>
          </div>
        )}

        {/* Error State */}
        {validationError && (
          <div className="validation-error-box">
            <span className="error-icon">⚠️</span>
            <span className="error-text">{validationError}</span>
          </div>
        )}
      </div>
    );
  };

  // Agent Animation Component - Shows visual storytelling of agent collaboration
  const AgentCollaborationAnimation = () => {
    const [activeAgent, setActiveAgent] = useState(0);
    const [phase, setPhase] = useState<'analysis' | 'synthesis' | 'validation' | 'assembly'>('analysis');
    
    const agents = [
      { name: 'Literature Review', icon: '📚', color: '#6366f1' },
      { name: 'Methodology', icon: '🔬', color: '#8b5cf6' },
      { name: 'Quality Assurance', icon: '✅', color: '#22c55e' },
      { name: 'Citation', icon: '📖', color: '#f59e0b' },
      { name: 'Visualization', icon: '📊', color: '#ec4899' },
      { name: 'Assembly', icon: '🏗️', color: '#14b8a6' },
    ];
    
    const phases = [
      { id: 'analysis', label: 'Analyzing Research Domain', icon: '🔍' },
      { id: 'synthesis', label: 'Synthesizing Knowledge', icon: '🧬' },
      { id: 'validation', label: 'Validating Q1 Standards', icon: '🎯' },
      { id: 'assembly', label: 'Assembling Proposal', icon: '📄' },
    ];
    
    useEffect(() => {
      // Rotate through agents
      const agentInterval = setInterval(() => {
        setActiveAgent((prev) => (prev + 1) % agents.length);
      }, 1500);
      
      // Rotate through phases
      const phaseInterval = setInterval(() => {
        setPhase((prev) => {
          const phaseOrder: ('analysis' | 'synthesis' | 'validation' | 'assembly')[] = ['analysis', 'synthesis', 'validation', 'assembly'];
          const currentIdx = phaseOrder.indexOf(prev);
          return phaseOrder[(currentIdx + 1) % phaseOrder.length];
        });
      }, 4000);
      
      return () => {
        clearInterval(agentInterval);
        clearInterval(phaseInterval);
      };
    }, []);
    
    return (
      <div className="agent-animation">
        <style jsx>{`
          .agent-animation {
            padding: 1.5rem;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
            border-radius: 16px;
            border: 1px solid rgba(99, 102, 241, 0.2);
            margin-bottom: 1.5rem;
          }
          .animation-header {
            text-align: center;
            margin-bottom: 1.5rem;
          }
          .animation-title {
            font-size: 1rem;
            font-weight: 600;
            color: #818cf8;
            margin-bottom: 0.5rem;
          }
          .animation-phase {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: rgba(255,255,255,0.8);
          }
          .phase-icon {
            animation: pulse 1s ease-in-out infinite;
          }
          @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
          }
          .agents-ring {
            display: flex;
            justify-content: center;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-bottom: 1.5rem;
          }
          .agent-node {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.05);
            border: 2px solid rgba(255,255,255,0.1);
          }
          .agent-node.active {
            transform: scale(1.15);
            box-shadow: 0 0 20px var(--glow-color);
            border-color: var(--glow-color);
            background: rgba(255,255,255,0.1);
          }
          .agent-label {
            text-align: center;
            font-size: 0.65rem;
            color: rgba(255,255,255,0.6);
            margin-top: 0.25rem;
            max-width: 60px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .agent-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
          }
          .connection-line {
            position: relative;
            height: 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 1rem;
          }
          .data-flow {
            display: flex;
            gap: 0.25rem;
            align-items: center;
          }
          .data-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #818cf8;
            animation: flowRight 1.5s ease-in-out infinite;
          }
          .data-dot:nth-child(2) { animation-delay: 0.2s; }
          .data-dot:nth-child(3) { animation-delay: 0.4s; }
          .data-dot:nth-child(4) { animation-delay: 0.6s; }
          .data-dot:nth-child(5) { animation-delay: 0.8s; }
          @keyframes flowRight {
            0% { opacity: 0; transform: translateX(-20px); }
            50% { opacity: 1; }
            100% { opacity: 0; transform: translateX(20px); }
          }
          .central-hub {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
            font-size: 1.75rem;
            animation: hubPulse 2s ease-in-out infinite;
            box-shadow: 0 0 30px rgba(99, 102, 241, 0.4);
          }
          @keyframes hubPulse {
            0%, 100% { box-shadow: 0 0 30px rgba(99, 102, 241, 0.4); }
            50% { box-shadow: 0 0 50px rgba(99, 102, 241, 0.6); }
          }
          .scopus-badge-anim {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 999px;
            font-size: 0.75rem;
            color: #22c55e;
            margin: 0 auto;
            width: fit-content;
          }
          .quality-indicator {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1rem;
          }
          .quality-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
          }
          .quality-dot.active {
            background: #22c55e;
            animation: qualityPulse 0.5s ease-out;
          }
          @keyframes qualityPulse {
            0% { transform: scale(1.5); opacity: 0.5; }
            100% { transform: scale(1); opacity: 1; }
          }
        `}</style>
        
        <div className="animation-header">
          <div className="animation-title">🧠 AI Agents Collaborating</div>
          <div className="animation-phase">
            <span className="phase-icon">{phases.find(p => p.id === phase)?.icon}</span>
            <span>{phases.find(p => p.id === phase)?.label}</span>
          </div>
        </div>
        
        <div className="central-hub">🎯</div>
        
        <div className="connection-line">
          <div className="data-flow">
            <div className="data-dot"></div>
            <div className="data-dot"></div>
            <div className="data-dot"></div>
            <div className="data-dot"></div>
            <div className="data-dot"></div>
          </div>
        </div>
        
        <div className="agents-ring">
          {agents.map((agent, idx) => (
            <div key={idx} className="agent-wrapper">
              <div 
                className={`agent-node ${activeAgent === idx ? 'active' : ''}`}
                style={{ '--glow-color': agent.color } as React.CSSProperties}
              >
                {agent.icon}
              </div>
              <div className="agent-label">{agent.name}</div>
            </div>
          ))}
        </div>
        
        <div className="scopus-badge-anim">
          ✨ Targeting Scopus Q1 Standards
        </div>
        
        <div className="quality-indicator">
          {[0,1,2,3,4].map((i) => (
            <div 
              key={i} 
              className={`quality-dot ${i <= Math.floor(progress / 20) ? 'active' : ''}`}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="dashboard">
      <style jsx>{`
        .dashboard {
          min-height: 100vh;
          background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
          font-family: system-ui, -apple-system, sans-serif;
          color: white;
        }
        .header {
          position: sticky;
          top: 0;
          z-index: 50;
          background: rgba(15, 15, 26, 0.95);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid rgba(255,255,255,0.1);
          padding: 1rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .header-left {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .logo-link {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          text-decoration: none;
          color: white;
        }
        .logo-icon {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
        }
        .logo-text {
          font-weight: bold;
          font-size: 1.25rem;
        }
        .logo-sub {
          font-size: 0.7rem;
          color: rgba(255,255,255,0.4);
        }
        .status-badge {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.4rem 0.75rem;
          border-radius: 999px;
          font-size: 0.75rem;
        }
        .status-online {
          background: rgba(34, 197, 94, 0.2);
          color: #22c55e;
        }
        .status-offline {
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
        }
        .status-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
        }
        .header-right {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .tier-badge {
          padding: 0.4rem 0.75rem;
          border-radius: 999px;
          font-size: 0.75rem;
          font-weight: 500;
        }
        .user-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .user-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 0.875rem;
        }
        .user-name {
          font-size: 0.875rem;
        }
        .logout-btn {
          background: none;
          border: none;
          color: rgba(255,255,255,0.5);
          cursor: pointer;
          font-size: 0.875rem;
          padding: 0.5rem;
        }
        .logout-btn:hover {
          color: white;
        }
        .main {
          max-width: 1400px;
          margin: 0 auto;
          padding: 2rem;
          display: grid;
          grid-template-columns: 1fr 1.2fr;
          gap: 2rem;
        }
        @media (max-width: 1024px) {
          .main {
            grid-template-columns: 1fr;
          }
        }
        .card {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 20px;
          padding: 2rem;
        }
        .card-title {
          font-size: 1.5rem;
          font-weight: bold;
          margin-bottom: 1.5rem;
        }
        .form-group {
          margin-bottom: 1.5rem;
        }
        .form-label {
          display: block;
          margin-bottom: 0.5rem;
          font-size: 0.875rem;
          color: rgba(255,255,255,0.8);
        }
        .form-textarea {
          width: 100%;
          min-height: 100px;
          padding: 1rem;
          border-radius: 12px;
          border: 1px solid rgba(255,255,255,0.1);
          background: rgba(255,255,255,0.05);
          color: white;
          font-size: 1rem;
          resize: vertical;
          box-sizing: border-box;
          font-family: inherit;
        }
        .form-textarea:focus {
          outline: none;
          border-color: rgba(99, 102, 241, 0.5);
        }
        .form-hint {
          font-size: 0.75rem;
          color: rgba(255,255,255,0.4);
          margin-top: 0.25rem;
        }
        .key-point-row {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 0.5rem;
        }
        .form-input {
          flex: 1;
          padding: 0.75rem 1rem;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.1);
          background: rgba(255,255,255,0.05);
          color: white;
          font-size: 0.9rem;
          font-family: inherit;
        }
        .form-input:focus {
          outline: none;
          border-color: rgba(99, 102, 241, 0.5);
        }
        .remove-btn {
          padding: 0.5rem 1rem;
          border-radius: 10px;
          border: none;
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
          cursor: pointer;
          font-size: 1rem;
        }
        .add-btn {
          background: none;
          border: none;
          color: #818cf8;
          cursor: pointer;
          font-size: 0.875rem;
          margin-top: 0.5rem;
          padding: 0;
        }
        .add-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .options-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }
        .form-select {
          width: 100%;
          padding: 0.75rem 1rem;
          border-radius: 10px;
          border: 1px solid rgba(139, 92, 246, 0.3);
          background: linear-gradient(135deg, rgba(30, 27, 46, 0.95), rgba(45, 40, 70, 0.95));
          color: #e2e8f0;
          font-size: 0.9rem;
          cursor: pointer;
          transition: all 0.15s ease;
          -webkit-appearance: none;
          -moz-appearance: none;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%238b5cf6' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 1rem center;
          padding-right: 2.5rem;
        }
        .form-select:hover {
          border-color: rgba(139, 92, 246, 0.5);
          background: linear-gradient(135deg, rgba(40, 35, 60, 0.98), rgba(55, 48, 85, 0.98));
          box-shadow: 0 0 15px rgba(139, 92, 246, 0.15);
        }
        .form-select:focus {
          outline: none;
          border-color: rgba(139, 92, 246, 0.7);
          box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2), 0 0 20px rgba(139, 92, 246, 0.15);
        }
        .form-select option {
          background: #1e1b2e;
          color: #e2e8f0;
          padding: 12px 16px;
          border: none;
        }
        .form-select option:hover,
        .form-select option:focus,
        .form-select option:checked {
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: white;
        }
        .submit-btn {
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
        .submit-btn:hover:not(:disabled) {
          transform: translateY(-1px);
        }
        .submit-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .progress-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }
        .new-btn {
          background: none;
          border: none;
          color: #818cf8;
          cursor: pointer;
          font-size: 0.875rem;
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }
        .empty-state {
          text-align: center;
          padding: 3rem 0;
        }
        .empty-icon {
          font-size: 4rem;
          margin-bottom: 1rem;
        }
        .empty-text {
          color: rgba(255,255,255,0.4);
        }
        .status-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          border-radius: 999px;
          font-size: 0.875rem;
          margin-bottom: 1.5rem;
        }
        .status-completed {
          background: rgba(34, 197, 94, 0.2);
          color: #22c55e;
        }
        .status-failed {
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
        }
        .status-running {
          background: rgba(99, 102, 241, 0.2);
          color: #818cf8;
        }
        .progress-section {
          margin-bottom: 1.5rem;
          padding: 1rem;
          background: rgba(0,0,0,0.2);
          border-radius: 12px;
        }
        .progress-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
        }
        .progress-label {
          font-size: 0.9rem;
          color: rgba(255,255,255,0.7);
          font-weight: 500;
        }
        .progress-value {
          font-size: 1rem;
          font-weight: bold;
          color: #a78bfa;
        }
        .progress-bar {
          height: 16px;
          border-radius: 8px;
          background: rgba(30, 30, 50, 0.9);
          overflow: hidden;
          position: relative;
          border: 1px solid rgba(99, 102, 241, 0.3);
        }
        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #4f46e5, #7c3aed, #a855f7);
          border-radius: 8px;
          transition: width 0.5s ease;
          position: relative;
          box-shadow: 0 0 15px rgba(124, 58, 237, 0.5);
        }
        @keyframes shimmer {
          0% { opacity: 0.5; }
          50% { opacity: 1; }
          100% { opacity: 0.5; }
        }
        .current-stage {
          padding: 1rem;
          border-radius: 12px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.3);
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .stage-icon {
          font-size: 1.25rem;
        }
        .stage-title {
          font-weight: 500;
          text-transform: capitalize;
        }
        .stage-message {
          font-size: 0.875rem;
          color: rgba(255,255,255,0.6);
        }
        .stats-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          margin-top: 1rem;
        }
        .stat-card {
          padding: 1.25rem;
          border-radius: 16px;
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05));
          border: 1px solid rgba(99, 102, 241, 0.2);
          text-align: center;
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;
        }
        .stat-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7);
        }
        .stat-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2);
        }
        .stat-value {
          font-size: 2.25rem;
          font-weight: bold;
          background: linear-gradient(135deg, #818cf8, #c084fc);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .stat-label {
          font-size: 0.875rem;
          color: rgba(255,255,255,0.7);
          font-weight: 500;
          margin-top: 0.25rem;
        }
        
        /* Tab Navigation */
        .tab-nav {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 1.5rem;
          border-bottom: 1px solid rgba(255,255,255,0.08);
          padding-bottom: 1rem;
          flex-wrap: wrap;
        }
        .tab-btn {
          padding: 0.6rem 1.1rem;
          border-radius: 10px;
          border: 1px solid transparent;
          background: transparent;
          color: rgba(255,255,255,0.5);
          cursor: pointer;
          font-size: 0.85rem;
          font-weight: 500;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
        }
        .tab-btn:hover {
          background: rgba(255,255,255,0.06);
          color: rgba(255,255,255,0.85);
          border-color: rgba(255,255,255,0.1);
        }
        .tab-btn.active {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.15));
          color: #a5b4fc;
          border-color: rgba(99, 102, 241, 0.4);
          box-shadow: 0 0 20px rgba(99, 102, 241, 0.15);
        }
        .tab-btn.active::after {
          content: '';
          position: absolute;
          bottom: -1rem;
          left: 50%;
          transform: translateX(-50%);
          width: 30px;
          height: 2px;
          background: linear-gradient(90deg, #6366f1, #8b5cf6);
          border-radius: 2px;
        }
        
        /* Download Card */
        .download-card {
          margin-top: 1.5rem;
          padding: 1.5rem;
          border-radius: 20px;
          background: linear-gradient(135deg, rgba(34, 197, 94, 0.08), rgba(16, 185, 129, 0.04));
          border: 1px solid rgba(34, 197, 94, 0.25);
          position: relative;
          overflow: hidden;
        }
        .download-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, #22c55e, #10b981, #06b6d4);
        }
        .download-header {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }
        .download-icon {
          font-size: 2.5rem;
          filter: drop-shadow(0 0 10px rgba(34, 197, 94, 0.5));
        }
        .download-title {
          font-size: 1.35rem;
          font-weight: bold;
          background: linear-gradient(135deg, #4ade80, #22d3ee);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .download-subtitle {
          font-size: 0.9rem;
          color: rgba(255,255,255,0.65);
          margin-top: 0.25rem;
        }
        .download-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          margin-bottom: 1rem;
        }
        .download-btn {
          padding: 1rem 1.5rem;
          border-radius: 14px;
          border: 1px solid rgba(255,255,255,0.15);
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.6rem;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          overflow: hidden;
          backdrop-filter: blur(12px);
          font-size: 1rem;
          letter-spacing: 0.02em;
          color: white;
          background: rgba(255,255,255,0.05);
          min-height: 52px;
        }
        .download-btn::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
          transition: left 0.6s ease;
        }
        .download-btn:hover::before {
          left: 100%;
        }
        .download-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
          transform: none !important;
          box-shadow: none !important;
        }
        .download-btn:hover:not(:disabled) {
          transform: translateY(-3px);
        }
        .download-btn:active:not(:disabled) {
          transform: translateY(-1px);
        }
        .btn-pdf {
          background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
          color: white;
          border: none;
          box-shadow: 
            0 4px 15px rgba(79, 70, 229, 0.4),
            0 0 30px rgba(124, 58, 237, 0.2),
            inset 0 1px 0 rgba(255,255,255,0.2);
        }
        .btn-pdf:hover:not(:disabled) {
          box-shadow: 
            0 8px 30px rgba(79, 70, 229, 0.5),
            0 0 50px rgba(124, 58, 237, 0.3),
            inset 0 1px 0 rgba(255,255,255,0.3);
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #c084fc 100%);
        }
        .btn-preview {
          background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(59, 130, 246, 0.2));
          border: 1px solid rgba(6, 182, 212, 0.5);
          color: #67e8f9;
          box-shadow: 
            0 4px 15px rgba(6, 182, 212, 0.25),
            inset 0 1px 0 rgba(255,255,255,0.1);
        }
        .btn-preview:hover:not(:disabled) {
          background: linear-gradient(135deg, rgba(6, 182, 212, 0.35), rgba(59, 130, 246, 0.35));
          border-color: rgba(6, 182, 212, 0.8);
          box-shadow: 
            0 8px 30px rgba(6, 182, 212, 0.35),
            0 0 40px rgba(6, 182, 212, 0.2),
            inset 0 1px 0 rgba(255,255,255,0.15);
          color: #a5f3fc;
        }
        .btn-secondary {
          padding: 1rem 1.25rem;
          border-radius: 12px;
          border: 1px solid rgba(255,255,255,0.15);
          background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
          color: rgba(255,255,255,0.9);
          cursor: pointer;
          font-size: 0.95rem;
          font-weight: 600;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          backdrop-filter: blur(10px);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          position: relative;
          overflow: hidden;
        }
        .btn-secondary::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
          transition: left 0.5s ease;
        }
        .btn-secondary:hover:not(:disabled)::before {
          left: 100%;
        }
        .btn-secondary:hover:not(:disabled) {
          background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.08));
          border-color: rgba(255,255,255,0.3);
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(0,0,0,0.3);
          color: white;
        }
        .btn-secondary:disabled {
          opacity: 0.35;
          cursor: not-allowed;
        }
        .tier-notice {
          margin-top: 1rem;
          padding: 0.75rem;
          border-radius: 10px;
          font-size: 0.875rem;
        }
        .tier-notice-free {
          background: rgba(245, 158, 11, 0.1);
          border: 1px solid rgba(245, 158, 11, 0.3);
          color: #f59e0b;
        }
        .tier-notice-standard {
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.3);
          color: #60a5fa;
        }
        
        /* Scopus Score Card */
        .scopus-card {
          padding: 1rem;
          border-radius: 12px;
          background: rgba(34, 197, 94, 0.1);
          border: 1px solid rgba(34, 197, 94, 0.3);
          margin-bottom: 1rem;
        }
        .scopus-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }
        .scopus-score {
          font-size: 2rem;
          font-weight: bold;
          color: #22c55e;
        }
        .scopus-badge {
          padding: 0.25rem 0.75rem;
          border-radius: 999px;
          font-size: 0.75rem;
          background: rgba(34, 197, 94, 0.2);
          color: #22c55e;
        }
        .scopus-bar {
          height: 8px;
          background: rgba(255,255,255,0.1);
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 1rem;
        }
        .scopus-bar-fill {
          height: 100%;
          background: linear-gradient(90deg, #22c55e, #16a34a);
          transition: width 0.5s;
        }
        .criteria-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 0.5rem;
        }
        .criteria-item {
          display: flex;
          justify-content: space-between;
          font-size: 0.8rem;
          padding: 0.5rem;
          background: rgba(255,255,255,0.05);
          border-radius: 6px;
        }
        .criteria-name {
          color: rgba(255,255,255,0.7);
        }
        .criteria-score {
          font-weight: bold;
          color: #22c55e;
        }
        
        /* Review Card */
        .review-card {
          padding: 1rem;
          border-radius: 12px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.3);
          margin-bottom: 1rem;
        }
        .review-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }
        .review-decision {
          font-size: 1.5rem;
          font-weight: bold;
          text-transform: uppercase;
        }
        .review-decision.accept {
          color: #22c55e;
        }
        .review-decision.minor_revision {
          color: #fbbf24;
        }
        .review-decision.major_revision {
          color: #f97316;
        }
        .review-decision.reject {
          color: #ef4444;
        }
        .reviewer-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .reviewer-item {
          padding: 0.75rem;
          background: rgba(255,255,255,0.05);
          border-radius: 8px;
        }
        .reviewer-name {
          font-weight: 500;
          margin-bottom: 0.25rem;
        }
        .reviewer-score {
          font-size: 0.8rem;
          color: rgba(255,255,255,0.6);
        }
        
        /* ================================================================
           VALIDATION PANEL STYLES (v2.7.1) - Enhanced Premium UI
           ContentSnapshot + MetricRows + Refinement Panel
           ================================================================ */
        
        /* Main Panel Container */
        .validation-panel-enhanced {
          padding: 0;
          border-radius: 20px;
          background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9));
          border: 1px solid rgba(99, 102, 241, 0.3);
          position: relative;
          overflow: hidden;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        .validation-panel-enhanced::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 4px;
          background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
        }
        
        /* Header */
        .validation-header-enhanced {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1.5rem;
          background: rgba(0, 0, 0, 0.2);
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .validation-icon-wrapper {
          width: 56px;
          height: 56px;
          border-radius: 16px;
          background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid rgba(99, 102, 241, 0.3);
        }
        .validation-icon-large {
          font-size: 1.75rem;
        }
        .validation-title-section {
          flex: 1;
        }
        .validation-main-title {
          font-size: 1.25rem;
          font-weight: 700;
          margin: 0;
          background: linear-gradient(135deg, #60a5fa, #c084fc);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .validation-sub-title {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.5);
          margin: 0.25rem 0 0 0;
        }
        .snapshot-badge {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: rgba(34, 197, 94, 0.15);
          border: 1px solid rgba(34, 197, 94, 0.3);
          border-radius: 20px;
          font-size: 0.75rem;
          color: #4ade80;
        }
        
        /* Idle State */
        .validation-idle-state {
          padding: 1.5rem;
        }
        .validation-description {
          margin-bottom: 1.5rem;
          color: rgba(255, 255, 255, 0.75);
          line-height: 1.6;
        }
        .validation-description p {
          margin: 0;
        }
        .threshold-cards {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
          margin-bottom: 1.5rem;
        }
        .threshold-card {
          padding: 1.25rem;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 14px;
          text-align: center;
          transition: all 0.3s ease;
        }
        .threshold-card:hover {
          background: rgba(255, 255, 255, 0.06);
          border-color: rgba(99, 102, 241, 0.3);
          transform: translateY(-2px);
        }
        .threshold-icon {
          font-size: 1.5rem;
          margin-bottom: 0.5rem;
        }
        .threshold-label {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.5);
          margin-bottom: 0.35rem;
        }
        .threshold-value {
          font-size: 1.25rem;
          font-weight: 700;
          color: #60a5fa;
        }
        .validation-disclaimer {
          display: flex;
          gap: 0.75rem;
          padding: 1rem;
          background: rgba(251, 191, 36, 0.08);
          border: 1px solid rgba(251, 191, 36, 0.2);
          border-radius: 12px;
          margin-bottom: 1.5rem;
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.7);
          line-height: 1.5;
        }
        .disclaimer-icon {
          flex-shrink: 0;
        }
        
        /* Validate Button */
        .validate-btn-enhanced {
          width: 100%;
          padding: 1rem 2rem;
          border-radius: 14px;
          border: none;
          background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
          color: white;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          box-shadow: 0 8px 20px rgba(59, 130, 246, 0.35);
        }
        .validate-btn-enhanced:hover:not(:disabled) {
          transform: translateY(-3px);
          box-shadow: 0 12px 30px rgba(59, 130, 246, 0.45);
        }
        .validate-btn-enhanced:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .btn-icon {
          font-size: 1.25rem;
        }
        
        /* Progress State */
        .validation-progress-enhanced {
          padding: 3rem 2rem;
          text-align: center;
        }
        .progress-spinner-container {
          position: relative;
          width: 80px;
          height: 80px;
          margin: 0 auto 1.5rem;
        }
        .progress-spinner-ring {
          position: absolute;
          inset: 0;
          border: 4px solid rgba(99, 102, 241, 0.2);
          border-top-color: #8b5cf6;
          border-radius: 50%;
          animation: spinRing 1.2s linear infinite;
        }
        @keyframes spinRing {
          to { transform: rotate(360deg); }
        }
        .progress-spinner-core {
          position: absolute;
          inset: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.75rem;
          animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.8; }
        }
        .progress-title {
          font-size: 1.25rem;
          font-weight: 600;
          margin: 0 0 0.5rem 0;
          color: white;
        }
        .progress-subtitle {
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.5);
          margin: 0 0 2rem 0;
        }
        .progress-steps {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0;
        }
        .progress-step {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
        }
        .step-indicator {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.1);
          border: 2px solid rgba(255, 255, 255, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.5);
          transition: all 0.3s ease;
        }
        .progress-step.active .step-indicator {
          background: linear-gradient(135deg, #3b82f6, #8b5cf6);
          border-color: transparent;
          color: white;
          box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
        }
        .step-label {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.4);
        }
        .progress-step.active .step-label {
          color: #a78bfa;
        }
        .progress-step-connector {
          width: 40px;
          height: 2px;
          background: rgba(255, 255, 255, 0.1);
          margin: 0 0.5rem;
          margin-bottom: 1.5rem;
        }
        .snapshot-info {
          margin-top: 2rem;
          padding: 1rem;
          background: rgba(0, 0, 0, 0.2);
          border-radius: 10px;
        }
        .snapshot-hash {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          font-family: monospace;
          font-size: 0.8rem;
        }
        .hash-label {
          color: rgba(255, 255, 255, 0.5);
        }
        .hash-value {
          color: #a78bfa;
        }
        
        /* Result States */
        .validation-result-enhanced {
          padding: 1.5rem;
        }
        .result-badge-container {
          display: flex;
          justify-content: center;
          margin-bottom: 1.25rem;
        }
        .result-badge {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1.5rem;
          border-radius: 30px;
          font-weight: 700;
          font-size: 1rem;
        }
        .result-badge.passed {
          background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.15));
          border: 1px solid rgba(34, 197, 94, 0.4);
          color: #4ade80;
        }
        .result-badge.failed {
          background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.15));
          border: 1px solid rgba(251, 191, 36, 0.4);
          color: #fbbf24;
        }
        .badge-icon {
          font-size: 1.25rem;
        }
        .result-message-box {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          padding: 1rem;
          background: rgba(34, 197, 94, 0.1);
          border-radius: 12px;
          margin-bottom: 1.5rem;
        }
        .message-icon {
          font-size: 1.5rem;
        }
        .message-text {
          font-size: 1rem;
          color: #86efac;
          font-weight: 500;
        }
        
        /* Metrics Container */
        .metrics-container {
          margin-bottom: 1.5rem;
          padding: 1.25rem;
          background: rgba(0, 0, 0, 0.2);
          border-radius: 14px;
        }
        .metrics-title {
          font-size: 0.9rem;
          font-weight: 600;
          margin: 0 0 1rem 0;
          color: rgba(255, 255, 255, 0.7);
        }
        
        /* Metric Row */
        .metric-row {
          display: flex;
          align-items: center;
          padding: 0.875rem 1rem;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 10px;
          margin-bottom: 0.5rem;
          border-left: 3px solid transparent;
        }
        .metric-row:last-child {
          margin-bottom: 0;
        }
        .metric-row.metric-pass {
          border-left-color: #22c55e;
        }
        .metric-row.metric-warning {
          border-left-color: #f59e0b;
        }
        .metric-row.metric-fail {
          border-left-color: #ef4444;
        }
        .metric-name {
          flex: 1;
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.85);
        }
        .metric-value {
          display: flex;
          align-items: baseline;
          gap: 0.35rem;
          margin-right: 1rem;
        }
        .metric-number {
          font-size: 1.1rem;
          font-weight: 700;
          color: white;
        }
        .metric-threshold {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.4);
        }
        .metric-status {
          font-size: 0.75rem;
          font-weight: 700;
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
        }
        .status-pass {
          background: rgba(34, 197, 94, 0.2);
          color: #4ade80;
        }
        .status-warning {
          background: rgba(245, 158, 11, 0.2);
          color: #fbbf24;
        }
        .status-fail {
          background: rgba(239, 68, 68, 0.2);
          color: #f87171;
        }
        
        /* Source Breakdown */
        .source-breakdown-enhanced {
          margin-bottom: 1.5rem;
          padding: 1.25rem;
          background: rgba(0, 0, 0, 0.15);
          border-radius: 14px;
        }
        .source-breakdown-enhanced .breakdown-title {
          font-size: 0.9rem;
          font-weight: 600;
          margin: 0 0 1rem 0;
          color: rgba(255, 255, 255, 0.7);
        }
        .breakdown-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .breakdown-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.625rem 0.875rem;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 8px;
        }
        .source-name {
          flex: 1;
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.75);
        }
        .source-bar-container {
          width: 80px;
          height: 6px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          overflow: hidden;
        }
        .source-bar {
          height: 100%;
          background: linear-gradient(90deg, #3b82f6, #8b5cf6);
          border-radius: 3px;
          transition: width 0.5s ease;
        }
        .source-bar.high {
          background: linear-gradient(90deg, #f59e0b, #ef4444);
        }
        .source-percentage {
          font-size: 0.85rem;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.85);
          min-width: 40px;
          text-align: right;
        }
        .source-percentage.high {
          color: #fbbf24;
        }
        
        /* Certificate Section */
        .certificate-section {
          padding: 1.25rem;
          background: linear-gradient(135deg, rgba(34, 197, 94, 0.08), rgba(16, 185, 129, 0.05));
          border: 1px solid rgba(34, 197, 94, 0.2);
          border-radius: 14px;
          margin-bottom: 1.5rem;
        }
        .certificate-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 1rem;
        }
        .cert-icon {
          font-size: 1.5rem;
        }
        .cert-title {
          font-size: 1rem;
          font-weight: 600;
          color: #4ade80;
        }
        .certificate-info {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }
        .cert-detail {
          display: flex;
          justify-content: space-between;
          font-size: 0.85rem;
        }
        .detail-label {
          color: rgba(255, 255, 255, 0.5);
        }
        .detail-value {
          color: rgba(255, 255, 255, 0.85);
        }
        .detail-value.hash {
          font-family: monospace;
          color: #a78bfa;
        }
        .certificate-download-btn {
          width: 100%;
          padding: 0.875rem;
          border-radius: 10px;
          border: 1px solid rgba(34, 197, 94, 0.4);
          background: rgba(34, 197, 94, 0.15);
          color: #4ade80;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          transition: all 0.3s ease;
        }
        .certificate-download-btn:hover {
          background: rgba(34, 197, 94, 0.25);
          transform: translateY(-2px);
        }
        
        /* Read-only Notice */
        .readonly-notice {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 1rem;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.2);
          border-radius: 12px;
        }
        .lock-icon {
          font-size: 1.25rem;
          flex-shrink: 0;
        }
        .notice-content strong {
          display: block;
          margin-bottom: 0.25rem;
          color: white;
        }
        .notice-content p {
          margin: 0;
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.6);
        }
        
        /* Failure Reason */
        .failure-reason-box {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 1rem;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.25);
          border-radius: 12px;
          margin-bottom: 1.5rem;
        }
        .reason-icon {
          font-size: 1.25rem;
          flex-shrink: 0;
        }
        .reason-text {
          font-size: 0.9rem;
          color: #fca5a5;
          line-height: 1.5;
        }
        
        /* Refinement Panel */
        .refinement-panel {
          padding: 1.25rem;
          background: rgba(251, 191, 36, 0.05);
          border: 1px solid rgba(251, 191, 36, 0.2);
          border-radius: 14px;
          margin-bottom: 1.5rem;
        }
        .refinement-title {
          font-size: 1rem;
          font-weight: 600;
          margin: 0 0 0.5rem 0;
          color: #fbbf24;
        }
        .refinement-description {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.6);
          margin: 0 0 1rem 0;
        }
        .refinement-actions {
          display: flex;
          gap: 0.75rem;
          margin-bottom: 1rem;
        }
        .refinement-btn {
          flex: 1;
          padding: 0.75rem 1rem;
          border-radius: 10px;
          border: 1px solid rgba(255, 255, 255, 0.15);
          background: rgba(255, 255, 255, 0.05);
          color: rgba(255, 255, 255, 0.85);
          font-size: 0.85rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          transition: all 0.3s ease;
        }
        .refinement-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.25);
        }
        .refinement-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .refinement-btn .coming-soon {
          font-size: 0.65rem;
          padding: 0.15rem 0.4rem;
          background: rgba(99, 102, 241, 0.3);
          border-radius: 4px;
          color: #a78bfa;
        }
        .refinement-notice {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.5);
        }
        
        /* Retry Button */
        .retry-btn-enhanced {
          width: 100%;
          padding: 1rem;
          border-radius: 12px;
          border: 1px solid rgba(251, 191, 36, 0.4);
          background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.1));
          color: #fbbf24;
          font-weight: 600;
          font-size: 1rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          transition: all 0.3s ease;
        }
        .retry-btn-enhanced:hover {
          background: linear-gradient(135deg, rgba(251, 191, 36, 0.25), rgba(245, 158, 11, 0.2));
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(251, 191, 36, 0.2);
        }
        
        /* Error Box */
        .validation-error-box {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin: 1.5rem;
          padding: 1rem;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 12px;
        }
        .error-icon {
          font-size: 1.25rem;
          flex-shrink: 0;
        }
        .error-text {
          font-size: 0.9rem;
          color: #fca5a5;
        }
        
        /* Artifact Viewer */
        .artifact-selector {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 1rem;
          flex-wrap: wrap;
        }
        .artifact-btn {
          padding: 0.5rem 0.75rem;
          border-radius: 8px;
          border: 1px solid rgba(255,255,255,0.1);
          background: transparent;
          color: rgba(255,255,255,0.6);
          cursor: pointer;
          font-size: 0.8rem;
          transition: all 0.2s;
        }
        .artifact-btn:hover {
          background: rgba(255,255,255,0.05);
          color: white;
        }
        .artifact-btn.active {
          background: rgba(99, 102, 241, 0.2);
          border-color: rgba(99, 102, 241, 0.5);
          color: #818cf8;
        }
        .artifact-viewer {
          background: rgba(0,0,0,0.3);
          border-radius: 12px;
          padding: 1.5rem;
          min-height: 300px;
          overflow: auto;
        }
        .artifact-title {
          font-size: 1rem;
          font-weight: 600;
          margin-bottom: 1rem;
          color: #818cf8;
        }
        .mermaid-container {
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 250px;
        }
        .mermaid-container :global(svg) {
          max-width: 100%;
          height: auto;
        }
        
        /* RTM Table */
        .rtm-table-container {
          overflow-x: auto;
        }
        .rtm-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.8rem;
        }
        .rtm-table th {
          background: rgba(99, 102, 241, 0.2);
          padding: 0.75rem;
          text-align: left;
          font-weight: 600;
        }
        .rtm-table td {
          padding: 0.75rem;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .rtm-id {
          font-family: monospace;
          color: #818cf8;
        }
        .rtm-source {
          font-size: 0.75rem;
          color: rgba(255,255,255,0.6);
        }
        .rtm-agent {
          font-size: 0.75rem;
          color: #22c55e;
        }
        .rtm-status {
          font-size: 0.9rem;
        }
        
        /* Kanban Board */
        .kanban-board {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
        }
        .kanban-column {
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          padding: 0.75rem;
        }
        .kanban-column-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
          font-weight: 600;
          font-size: 0.85rem;
        }
        .kanban-count {
          background: rgba(99, 102, 241, 0.3);
          padding: 0.2rem 0.5rem;
          border-radius: 999px;
          font-size: 0.7rem;
        }
        .kanban-cards {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .kanban-card {
          background: rgba(255,255,255,0.05);
          border-radius: 6px;
          padding: 0.5rem;
          border-left: 3px solid #6366f1;
        }
        .kanban-card.priority-high {
          border-left-color: #ef4444;
        }
        .kanban-card.priority-medium {
          border-left-color: #fbbf24;
        }
        .kanban-card-title {
          font-size: 0.75rem;
          font-weight: 500;
          margin-bottom: 0.25rem;
        }
        .kanban-card-agent {
          font-size: 0.65rem;
          color: rgba(255,255,255,0.5);
        }
        
        /* WBS Tree */
        .wbs-tree {
          font-size: 0.85rem;
        }
        .wbs-node {
          padding: 0.5rem 0;
        }
        .wbs-node-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.5rem;
          background: rgba(255,255,255,0.03);
          border-radius: 6px;
          margin-bottom: 0.25rem;
        }
        .wbs-id {
          font-family: monospace;
          color: #818cf8;
          font-size: 0.75rem;
        }
        .wbs-name {
          font-weight: 500;
        }
        .wbs-deliverable {
          font-size: 0.75rem;
          color: #22c55e;
          margin-left: auto;
        }
        
        /* Structured TOC */
        .toc-viewer {
          background: rgba(255,255,255,0.02);
          border-radius: 12px;
          padding: 1.5rem;
        }
        .toc-title {
          text-align: center;
          font-size: 1.25rem;
          font-weight: bold;
          margin-bottom: 1.5rem;
          border-bottom: 2px solid rgba(255,255,255,0.1);
          padding-bottom: 1rem;
        }
        .toc-entry {
          display: flex;
          align-items: baseline;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
        }
        .toc-entry-title {
          flex-shrink: 0;
        }
        .toc-leader {
          flex-grow: 1;
          border-bottom: 1px dotted rgba(255,255,255,0.3);
          margin: 0 0.5rem;
          height: 1em;
        }
        .toc-page {
          flex-shrink: 0;
          color: rgba(255,255,255,0.6);
        }
        .toc-chapter {
          font-weight: bold;
          color: white;
        }
        .toc-section {
          color: rgba(255,255,255,0.8);
        }
        
        /* Modal */
        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.8);
          backdrop-filter: blur(8px);
          z-index: 100;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
        }
        .modal-content {
          background: white;
          border-radius: 20px;
          width: 100%;
          max-width: 900px;
          max-height: 90vh;
          overflow: hidden;
        }
        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem;
          border-bottom: 1px solid #e5e7eb;
          background: #f9fafb;
        }
        .modal-title {
          font-size: 1.25rem;
          font-weight: bold;
          color: #111827;
        }
        .modal-close {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #6b7280;
        }
        .modal-body {
          padding: 1.5rem;
          overflow-y: auto;
          max-height: calc(90vh - 80px);
          color: #111827;
        }
        .right-column {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }
      `}</style>

      {/* Header */}
      <header className="header">
        <div className="header-left">
          <Link href="/" className="logo-link">
            <div className="logo-icon">🧠</div>
            <div>
              <div className="logo-text">ResearchAI</div>
              <div className="logo-sub">v{apiVersion} • {agentCount} Agents</div>
            </div>
          </Link>
          
          <div className={`status-badge ${apiStatus === 'online' ? 'status-online' : 'status-offline'}`}>
            <div className="status-dot" style={{ background: apiStatus === 'online' ? '#22c55e' : '#ef4444' }} />
            {apiStatus === 'online' ? 'Online' : 'Offline'}
          </div>
        </div>

        <div className="header-right">
          <div className="tier-badge" style={{ background: tierInfo.bg, color: tierInfo.color }}>
            {tierInfo.label}
          </div>
          <div className="user-info">
            <div className="user-avatar">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <span className="user-name">{user?.name || 'User'}</span>
          </div>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {/* Form Card */}
        <div className="card">
          <h2 className="card-title">Generate Research Proposal</h2>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Research Topic *</label>
              <textarea
                value={topic}
                onChange={e => setTopic(e.target.value)}
                placeholder="e.g., Machine Learning Applications in Early Cancer Detection and Diagnosis"
                disabled={isGenerating}
                className="form-textarea"
              />
              <div className="form-hint">{topic.length}/500 (min 10)</div>
            </div>

            <div className="form-group">
              <label className="form-label">Key Points * (min 3)</label>
              {keyPoints.map((kp, i) => (
                <div key={i} className="key-point-row">
                  <input
                    value={kp}
                    onChange={e => updateKeyPoint(i, e.target.value)}
                    placeholder={`Key point ${i + 1}`}
                    disabled={isGenerating}
                    className="form-input"
                  />
                  {keyPoints.length > 3 && (
                    <button type="button" onClick={() => removeKeyPoint(i)} className="remove-btn" disabled={isGenerating}>
                      ✕
                    </button>
                  )}
                </div>
              ))}
              {keyPoints.length < 8 && (
                <button type="button" onClick={addKeyPoint} className="add-btn" disabled={isGenerating}>
                  + Add Key Point
                </button>
              )}
            </div>

            <div className="options-grid">
              <div>
                <label className="form-label">Citation Style</label>
                <select value={citationStyle} onChange={e => setCitationStyle(e.target.value)} disabled={isGenerating} className="form-select">
                  <option value="harvard">Harvard</option>
                  <option value="apa">APA 7th</option>
                  <option value="mla">MLA</option>
                </select>
              </div>
              <div>
                <label className="form-label">Target Words</label>
                <select value={targetWords} onChange={e => setTargetWords(Number(e.target.value))} disabled={isGenerating} className="form-select">
                  <option value={3000}>3,000 (Express ~3min)</option>
                  <option value={5000}>5,000 (Brief ~5min)</option>
                  <option value={10000}>10,000 (Standard ~8min)</option>
                  <option value={15000}>15,000 (Comprehensive ~12min)</option>
                  <option value={20000}>20,000 (Extended ~18min)</option>
                </select>
              </div>
            </div>

            <button type="submit" className="submit-btn" disabled={isGenerating || apiStatus === 'offline'}>
              {isGenerating ? '⏳ Generating...' : '⚡ Generate Proposal'}
            </button>
          </form>
        </div>

        {/* Right Column */}
        <div className="right-column">
          {/* Progress Card */}
          <div className="card">
            <div className="progress-header">
              <h2 className="card-title" style={{ marginBottom: 0 }}>Progress</h2>
              {(jobStatus || result) && (
                <button onClick={handleReset} className="new-btn">
                  🔄 New
                </button>
              )}
            </div>

            {!jobStatus && !result && !isGenerating ? (
              <div className="empty-state">
                <div className="empty-icon">🧠</div>
                <p className="empty-text">Fill the form and click Generate</p>
              </div>
            ) : (
              <div>
                <div className={`status-pill ${result || jobStatus?.status === 'completed' ? 'status-completed' : jobStatus?.status === 'failed' ? 'status-failed' : 'status-running'}`}>
                  {result || jobStatus?.status === 'completed' ? '✅' : jobStatus?.status === 'failed' ? '❌' : '⏳'}
                  <span style={{ textTransform: 'capitalize' }}>{result ? 'Completed' : jobStatus?.status || 'Processing'}</span>
                </div>

                <div className="progress-section">
                  <div className="progress-header-row">
                    <span className="progress-label">Progress</span>
                    <span className="progress-value">{progress}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${progress}%` }} />
                  </div>
                </div>

                {/* Agent Collaboration Animation - Shows during GENERATING state */}
                {isGenerating && !result && jobStatus?.status !== 'failed' && (
                  <AgentCollaborationAnimation />
                )}

                {jobStatus?.current_stage && !result && (
                  <div className="current-stage">
                    <span className="stage-icon">⏳</span>
                    <div>
                      <div className="stage-title">{jobStatus.current_stage.replace(/_/g, ' ')}</div>
                      <div className="stage-message">{jobStatus.message}</div>
                    </div>
                  </div>
                )}

                {result && (
                  <div className="stats-grid">
                    <div className="stat-card">
                      <div className="stat-value">{result.sections?.length || 10}</div>
                      <div className="stat-label">Sections</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{result.word_count?.toLocaleString() || '15K+'}</div>
                      <div className="stat-label">Words</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Results Tabs Card */}
          {result && (
            <div className="card">
              {/* Tab Navigation */}
              <div className="tab-nav">
                <button 
                  className={`tab-btn ${activeTab === 'export' ? 'active' : ''}`}
                  onClick={() => setActiveTab('export')}
                >
                  📥 Export
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'artifacts' ? 'active' : ''}`}
                  onClick={() => setActiveTab('artifacts')}
                >
                  📊 Artifacts
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'toc' ? 'active' : ''}`}
                  onClick={() => setActiveTab('toc')}
                >
                  📋 TOC
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'scopus' ? 'active' : ''}`}
                  onClick={() => setActiveTab('scopus')}
                >
                  🎯 Scopus
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'review' ? 'active' : ''}`}
                  onClick={() => setActiveTab('review')}
                >
                  👥 Review
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'validation' ? 'active' : ''}`}
                  onClick={() => setActiveTab('validation')}
                >
                  🔍 Validation
                </button>
              </div>

              {/* Export Tab */}
              {activeTab === 'export' && (
                <div className="download-card">
                  <div className="download-header">
                    <span className="download-icon">✅</span>
                    <div>
                      <div className="download-title">Proposal Ready!</div>
                      <div className="download-subtitle">Download your research proposal</div>
                    </div>
                  </div>

                  <div className="download-grid">
                    <button 
                      onClick={() => handleDownload('pdf')} 
                      className="download-btn btn-pdf"
                      disabled={subscriptionTier === 'free' || isDownloading}
                    >
                      {subscriptionTier === 'free' ? '🔒 PDF' : '📄 PDF'}
                    </button>
                    <button onClick={handlePreview} className="download-btn btn-preview" disabled={isDownloading}>
                      👁️ Preview
                    </button>
                  </div>

                  <div className="download-grid">
                    <button onClick={() => handleDownload('docx')} className="btn-secondary" disabled={isDownloading}>
                      📝 DOCX
                    </button>
                    <button onClick={() => handleDownload('markdown')} className="btn-secondary" disabled={isDownloading}>
                      📋 Markdown
                    </button>
                  </div>
                  
                  <div className="download-grid">
                    <button onClick={() => handleDownload('latex')} className="btn-secondary" disabled={isDownloading}>
                      📐 LaTeX
                    </button>
                    <button onClick={() => handleDownload('overleaf')} className="btn-secondary" disabled={isDownloading}>
                      🍃 Overleaf
                    </button>
                  </div>

                  {subscriptionTier === 'free' && (
                    <div className="tier-notice tier-notice-free">
                      👑 Upgrade to Premium for PDF export
                    </div>
                  )}
                </div>
              )}

              {/* Artifacts Tab */}
              {activeTab === 'artifacts' && (
                <div>
                  {isLoadingArtifacts ? (
                    <div className="empty-state">
                      <div className="empty-icon">⏳</div>
                      <p className="empty-text">Loading artifacts...</p>
                    </div>
                  ) : artifacts.length === 0 ? (
                    <div className="empty-state">
                      <div className="empty-icon">📊</div>
                      <p className="empty-text">No artifacts available</p>
                    </div>
                  ) : (
                    <>
                      <div className="artifact-selector">
                        {artifacts.map((artifact) => (
                          <button
                            key={artifact.type}
                            className={`artifact-btn ${selectedArtifact === artifact.type ? 'active' : ''}`}
                            onClick={() => setSelectedArtifact(artifact.type)}
                          >
                            {artifact.type === 'gantt_chart' && '📅 Gantt'}
                            {artifact.type === 'work_breakdown_structure' && '🌳 WBS'}
                            {artifact.type === 'requirements_traceability_matrix' && '📋 RTM'}
                            {artifact.type === 'kanban_state_model' && '📌 Kanban'}
                            {artifact.type === 'methodology_flowchart' && '🔄 Methodology'}
                            {artifact.type === 'data_flow_diagram' && '📊 Data Flow'}
                          </button>
                        ))}
                      </div>
                      
                      <div className="artifact-viewer">
                        {currentArtifact && (
                          <>
                            <div className="artifact-title">{currentArtifact.title}</div>
                            
                            {/* Mermaid Diagrams */}
                            {currentArtifact.mermaid_code && (
                              <div className="mermaid-container" ref={mermaidRef}>
                                <p style={{ color: 'rgba(255,255,255,0.5)' }}>Loading diagram...</p>
                              </div>
                            )}
                            
                            {/* RTM Table */}
                            {currentArtifact.type === 'requirements_traceability_matrix' && (
                              renderRTMTable(currentArtifact.content.requirements || [])
                            )}
                            
                            {/* Kanban Board */}
                            {currentArtifact.type === 'kanban_state_model' && (
                              renderKanbanBoard(currentArtifact.content)
                            )}
                            
                            {/* WBS Tree (if no mermaid) */}
                            {currentArtifact.type === 'work_breakdown_structure' && !currentArtifact.mermaid_code && (
                              renderWBSTree(currentArtifact.content.levels || [])
                            )}
                          </>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* TOC Tab */}
              {activeTab === 'toc' && (
                <div>
                  {structuredTOC ? (
                    <div className="toc-viewer">
                      <div className="toc-title">{structuredTOC.title}</div>
                      {structuredTOC.entries.map((entry, idx) => (
                        <div 
                          key={idx} 
                          className="toc-entry"
                          style={{ paddingLeft: `${entry.indent * 1.5}rem` }}
                        >
                          <span className={`toc-entry-title ${entry.level === 'chapter' ? 'toc-chapter' : 'toc-section'}`}>
                            {entry.number && `${entry.number} `}{entry.title}
                          </span>
                          <span className="toc-leader"></span>
                          <span className="toc-page">{entry.page}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-icon">📋</div>
                      <p className="empty-text">Loading TOC...</p>
                    </div>
                  )}
                </div>
              )}

              {/* Scopus Tab */}
              {activeTab === 'scopus' && (
                <div>
                  {scopusScore ? (
                    <div className="scopus-card">
                      <div className="scopus-header">
                        <div>
                          <div className="scopus-score">{(scopusScore.overall_score * 100).toFixed(1)}%</div>
                          <div style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>
                            Q1 Compliance Score
                          </div>
                        </div>
                        <div className="scopus-badge">
                          {scopusScore.q1_ready ? '✅ Q1 Ready' : '⚠️ Needs Work'}
                        </div>
                      </div>
                      
                      <div className="scopus-bar">
                        <div 
                          className="scopus-bar-fill" 
                          style={{ width: `${scopusScore.overall_score * 100}%` }}
                        />
                      </div>
                      
                      <div className="criteria-grid">
                        {Object.entries(scopusScore.criteria_scores || {}).map(([key, value]) => {
                          // Handle nested score object from backend
                          const scoreValue = typeof value === 'object' && value !== null 
                            ? (value as any).score || (value as any).weighted_score || 0
                            : (typeof value === 'number' ? value : 0);
                          return (
                            <div key={key} className="criteria-item">
                              <span className="criteria-name">{key.replace(/_/g, ' ')}</span>
                              <span className="criteria-score">{(scoreValue * 100).toFixed(0)}%</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-icon">🎯</div>
                      <p className="empty-text">Loading Scopus analysis...</p>
                    </div>
                  )}
                </div>
              )}

              {/* Review Tab */}
              {activeTab === 'review' && (
                <div>
                  {reviewResult ? (
                    <div className="review-card">
                      <div className="review-header">
                        <div className={`review-decision ${reviewResult.overall_assessment}`}>
                          {reviewResult.overall_assessment.replace('_', ' ')}
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                            {reviewResult.consensus_score?.toFixed(1) || 0}%
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)' }}>
                            {reviewResult.agreement_level || 'consensus'}
                          </div>
                        </div>
                      </div>
                      
                      <div className="reviewer-list">
                        {(reviewResult.reviewer_feedback || []).slice(0, 4).map((reviewer, idx) => (
                          <div key={idx} className="reviewer-item">
                            <div className="reviewer-name">{reviewer.persona_name}</div>
                            <div className="reviewer-score">
                              {reviewer.recommendation} • {(reviewer.score * 100).toFixed(0)}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-icon">👥</div>
                      <p className="empty-text">Loading review simulation...</p>
                    </div>
                  )}
                </div>
              )}

              {/* Validation Tab - Turnitin Compliance (v2.7.0) */}
              {activeTab === 'validation' && (
                <ValidationPanel 
                  documentId={currentJobId || ''}
                  documentContent={result?.full_content || ''}
                />
              )}
            </div>
          )}
        </div>
      </main>

      {/* Preview Modal */}
      {showPreview && (
        <div className="modal-overlay" onClick={() => setShowPreview(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Proposal Preview</h2>
              <button onClick={() => setShowPreview(false)} className="modal-close">✕</button>
            </div>
            <div className="modal-body" dangerouslySetInnerHTML={{ __html: previewHtml }} />
          </div>
        </div>
      )}
    </div>
  );
}
