"""
ResearchAI v2.3.0 - Email Notification Agent
=============================================

Async email notification system with template-based messaging.
Supports multiple notification events with HTML templates.

Architecture:
- Event-driven notifications
- Template-based email generation
- Async SMTP delivery with retry logic
- Notification history tracking
"""

import os
import re
import asyncio
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from string import Template

logger = logging.getLogger(__name__)


# ============================================================================
# Notification Types
# ============================================================================

class NotificationType(Enum):
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    REVIEW_READY = "review_ready"
    SCOPUS_SCORE = "scopus_score"


@dataclass
class NotificationEvent:
    """Notification event data."""
    event_type: NotificationType
    user_email: str
    user_name: str
    job_id: str
    topic: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class NotificationResult:
    """Result of notification attempt."""
    success: bool
    event_type: NotificationType
    recipient: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    sent_at: Optional[str] = None


# ============================================================================
# Email Templates (HTML)
# ============================================================================

class EmailTemplates:
    """HTML email templates for various notification types."""
    
    BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .header p { margin: 10px 0 0; opacity: 0.9; }
        .content { padding: 30px; }
        .content h2 { color: #667eea; margin-top: 0; }
        .info-box { background: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0; }
        .score-box { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }
        .score-box .score { font-size: 48px; font-weight: bold; }
        .score-box .label { font-size: 14px; opacity: 0.9; }
        .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: 600; margin: 20px 0; }
        .button:hover { background: #5a6fd6; }
        .progress-bar { background: #e9ecef; border-radius: 10px; height: 20px; overflow: hidden; margin: 15px 0; }
        .progress-fill { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; border-radius: 10px; transition: width 0.3s; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .footer a { color: #667eea; text-decoration: none; }
        .checklist { list-style: none; padding: 0; }
        .checklist li { padding: 8px 0; border-bottom: 1px solid #eee; }
        .checklist li:before { content: "✓"; color: #38ef7d; margin-right: 10px; font-weight: bold; }
        .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0; }
        .error { background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0; }
    </style>
</head>
<body>
    <div class="container">
        $content
        <div class="footer">
            <p>© 2024 ResearchAI by FOMA Digital Solution</p>
            <p><a href="https://researchai.app">researchai.app</a> | <a href="mailto:support@researchai.app">support@researchai.app</a></p>
            <p style="margin-top: 15px; font-size: 11px; color: #999;">
                You received this email because you're using ResearchAI. 
                <a href="${unsubscribe_url}">Unsubscribe</a>
            </p>
        </div>
    </div>
</body>
</html>
"""

    JOB_STARTED = """
        <div class="header">
            <h1>🚀 Proposal Generation Started</h1>
            <p>Your research proposal is being created</p>
        </div>
        <div class="content">
            <h2>Hello ${user_name}!</h2>
            <p>Great news! We've started generating your research proposal. Our AI agents are working hard to create a Q1 journal-standard document for you.</p>
            
            <div class="info-box">
                <strong>📋 Topic:</strong><br>
                ${topic}
            </div>
            
            <div class="info-box">
                <strong>🔑 Job ID:</strong> ${job_id}<br>
                <strong>⏱️ Estimated Time:</strong> 10-15 minutes<br>
                <strong>📧 Status Updates:</strong> You'll receive an email when complete
            </div>
            
            <h3>What's happening now?</h3>
            <ul class="checklist">
                <li>14 AI agents are collaborating on your proposal</li>
                <li>Literature review is being synthesized</li>
                <li>Methodology section is being crafted</li>
                <li>Citations are being formatted in Harvard style</li>
            </ul>
            
            <center>
                <a href="${dashboard_url}" class="button">View Progress →</a>
            </center>
        </div>
"""

    JOB_PROGRESS = """
        <div class="header">
            <h1>📊 Generation Progress Update</h1>
            <p>Your proposal is ${progress}% complete</p>
        </div>
        <div class="content">
            <h2>Progress Update</h2>
            <p>Your research proposal generation is progressing well!</p>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
            <p style="text-align: center; color: #667eea; font-weight: bold;">${progress}% Complete</p>
            
            <div class="info-box">
                <strong>Current Stage:</strong> ${current_stage}<br>
                <strong>Job ID:</strong> ${job_id}
            </div>
            
            <p>Estimated remaining time: ${remaining_time}</p>
            
            <center>
                <a href="${dashboard_url}" class="button">View Live Progress →</a>
            </center>
        </div>
"""

    JOB_COMPLETED = """
        <div class="header">
            <h1>✅ Proposal Complete!</h1>
            <p>Your research proposal is ready for download</p>
        </div>
        <div class="content">
            <h2>Congratulations, ${user_name}! 🎉</h2>
            <p>Your Q1 journal-standard research proposal has been successfully generated!</p>
            
            <div class="info-box">
                <strong>📋 Topic:</strong><br>
                ${topic}
            </div>
            
            <div class="score-box">
                <div class="label">Word Count</div>
                <div class="score">${word_count}</div>
                <div class="label">words generated</div>
            </div>
            
            <h3>Document Highlights</h3>
            <ul class="checklist">
                <li>${sections_count} comprehensive sections</li>
                <li>Harvard citation style with 40+ references</li>
                <li>Professional formatting ready for submission</li>
                <li>Scopus Q1 compliance verified</li>
            </ul>
            
            <h3>Available Export Formats</h3>
            <p>📄 PDF | 📝 DOCX | 📋 Markdown | 🔬 LaTeX | ☁️ Overleaf</p>
            
            <center>
                <a href="${download_url}" class="button">Download Proposal →</a>
            </center>
            
            <div class="info-box" style="margin-top: 30px;">
                <strong>💡 Pro Tip:</strong> Use the Scopus Compliance Score to identify areas for improvement before submission.
            </div>
        </div>
"""

    JOB_FAILED = """
        <div class="header" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">
            <h1>⚠️ Generation Failed</h1>
            <p>We encountered an issue with your proposal</p>
        </div>
        <div class="content">
            <h2>We're Sorry, ${user_name}</h2>
            <p>Unfortunately, we encountered an error while generating your research proposal.</p>
            
            <div class="error">
                <strong>Error Details:</strong><br>
                ${error_message}
            </div>
            
            <div class="info-box">
                <strong>Job ID:</strong> ${job_id}<br>
                <strong>Topic:</strong> ${topic}
            </div>
            
            <h3>What You Can Do</h3>
            <ul class="checklist">
                <li>Try generating the proposal again</li>
                <li>Simplify or rephrase your research topic</li>
                <li>Contact support if the issue persists</li>
            </ul>
            
            <center>
                <a href="${retry_url}" class="button">Try Again →</a>
            </center>
            
            <p style="margin-top: 20px; font-size: 14px; color: #666;">
                Need help? Contact us at <a href="mailto:support@researchai.app">support@researchai.app</a>
            </p>
        </div>
"""

    REVIEW_READY = """
        <div class="header">
            <h1>👥 Peer Review Complete</h1>
            <p>7 expert reviewers have evaluated your proposal</p>
        </div>
        <div class="content">
            <h2>Review Results Ready, ${user_name}!</h2>
            <p>Our AI reviewer simulation has completed a comprehensive evaluation of your research proposal.</p>
            
            <div class="score-box" style="background: ${decision_color};">
                <div class="label">Editorial Decision</div>
                <div class="score" style="font-size: 24px;">${decision}</div>
                <div class="label">Consensus Score: ${consensus_score}%</div>
            </div>
            
            <div class="info-box">
                <strong>📋 Topic:</strong> ${topic}<br>
                <strong>👥 Reviewers:</strong> ${reviewer_count}<br>
                <strong>📊 Agreement:</strong> ${agreement_level}
            </div>
            
            <h3>Key Strengths</h3>
            <ul class="checklist">
                ${strengths_html}
            </ul>
            
            <h3>Priority Revisions</h3>
            <div class="warning">
                ${revisions_html}
            </div>
            
            <center>
                <a href="${review_url}" class="button">View Full Review →</a>
            </center>
        </div>
"""

    SCOPUS_SCORE = """
        <div class="header">
            <h1>📊 Scopus Q1 Compliance Score</h1>
            <p>Your proposal has been evaluated for Q1 journal readiness</p>
        </div>
        <div class="content">
            <h2>Compliance Assessment Complete!</h2>
            
            <div class="score-box">
                <div class="label">Overall Score</div>
                <div class="score">${overall_score}%</div>
                <div class="label">${quality_level}</div>
            </div>
            
            <div class="info-box">
                <strong>📋 Topic:</strong> ${topic}<br>
                <strong>✅ Q1 Ready:</strong> ${q1_ready}<br>
                <strong>📈 Acceptance Probability:</strong> ${acceptance_prob}%
            </div>
            
            <h3>Criteria Breakdown</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #f8f9fa;">
                    <th style="padding: 10px; text-align: left;">Criterion</th>
                    <th style="padding: 10px; text-align: right;">Score</th>
                </tr>
                ${criteria_html}
            </table>
            
            <h3>Recommendations</h3>
            <ul class="checklist">
                ${recommendations_html}
            </ul>
            
            <center>
                <a href="${dashboard_url}" class="button">View Detailed Report →</a>
            </center>
        </div>
"""


# ============================================================================
# Email Configuration
# ============================================================================

@dataclass
class EmailConfig:
    """SMTP email configuration."""
    smtp_host: str = "smtp.sendgrid.net"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@researchai.app"
    from_name: str = "ResearchAI"
    use_tls: bool = True
    
    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Load configuration from environment variables."""
        return cls(
            smtp_host=os.getenv('SMTP_HOST', 'smtp.sendgrid.net'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_user=os.getenv('SMTP_USER', ''),
            smtp_password=os.getenv('SMTP_PASSWORD', ''),
            from_email=os.getenv('FROM_EMAIL', 'noreply@researchai.app'),
            from_name=os.getenv('FROM_NAME', 'ResearchAI'),
            use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        )


# ============================================================================
# Email Notification Agent
# ============================================================================

class EmailNotificationAgent:
    """
    Email Notification Agent v2.0
    
    Handles async email delivery with template rendering and retry logic.
    Supports multiple notification types with rich HTML formatting.
    """
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.name = "EmailNotificationAgent"
        self.version = "2.0.0"
        self.config = config or EmailConfig.from_env()
        self.templates = EmailTemplates()
        self._notification_history: List[NotificationResult] = []
        self._enabled = bool(self.config.smtp_user and self.config.smtp_password)
        
        if not self._enabled:
            logger.warning("Email notifications disabled: SMTP credentials not configured")
    
    @property
    def is_enabled(self) -> bool:
        """Check if email notifications are enabled."""
        return self._enabled
    
    def _render_template(
        self, 
        template_type: NotificationType, 
        data: Dict[str, Any]
    ) -> str:
        """Render email template with data."""
        # Get template content
        template_map = {
            NotificationType.JOB_STARTED: self.templates.JOB_STARTED,
            NotificationType.JOB_PROGRESS: self.templates.JOB_PROGRESS,
            NotificationType.JOB_COMPLETED: self.templates.JOB_COMPLETED,
            NotificationType.JOB_FAILED: self.templates.JOB_FAILED,
            NotificationType.REVIEW_READY: self.templates.REVIEW_READY,
            NotificationType.SCOPUS_SCORE: self.templates.SCOPUS_SCORE,
        }
        
        content_template = template_map.get(template_type, "")
        
        # Set defaults
        defaults = {
            'unsubscribe_url': 'https://researchai.app/settings/notifications',
            'dashboard_url': 'https://researchai.app/dashboard',
            'download_url': 'https://researchai.app/proposals',
            'retry_url': 'https://researchai.app/generate',
            'review_url': 'https://researchai.app/review',
        }
        data = {**defaults, **data}
        
        # Render content template
        try:
            content = Template(content_template).safe_substitute(data)
            # Render full email
            full_html = Template(self.templates.BASE_TEMPLATE).safe_substitute(
                content=content, **data
            )
            return full_html
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return f"<html><body><p>Error rendering email template</p></body></html>"
    
    def _get_subject(self, event_type: NotificationType, data: Dict[str, Any]) -> str:
        """Get email subject based on event type."""
        subjects = {
            NotificationType.JOB_STARTED: "🚀 Your Research Proposal Generation Has Started",
            NotificationType.JOB_PROGRESS: f"📊 Progress Update: {data.get('progress', 0)}% Complete",
            NotificationType.JOB_COMPLETED: "✅ Your Research Proposal is Ready!",
            NotificationType.JOB_FAILED: "⚠️ Proposal Generation Failed",
            NotificationType.REVIEW_READY: "👥 Peer Review Results Ready",
            NotificationType.SCOPUS_SCORE: f"📊 Scopus Score: {data.get('overall_score', 'N/A')}%",
        }
        return subjects.get(event_type, "ResearchAI Notification")
    
    async def _send_email_async(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> NotificationResult:
        """Send email asynchronously with retry logic."""
        if not self._enabled:
            return NotificationResult(
                success=False,
                event_type=NotificationType.JOB_STARTED,
                recipient=to_email,
                error="Email notifications not configured"
            )
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
        msg['To'] = to_email
        
        # Plain text fallback
        plain_text = re.sub('<[^<]+?>', '', html_content)
        plain_text = re.sub(r'\s+', ' ', plain_text).strip()
        
        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._send_smtp, msg)
                
                return NotificationResult(
                    success=True,
                    event_type=NotificationType.JOB_STARTED,
                    recipient=to_email,
                    message_id=msg.get('Message-ID'),
                    sent_at=datetime.utcnow().isoformat()
                )
            except Exception as e:
                logger.warning(f"Email send attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return NotificationResult(
            success=False,
            event_type=NotificationType.JOB_STARTED,
            recipient=to_email,
            error=f"Failed after {max_retries} attempts"
        )
    
    def _send_smtp(self, msg: MIMEMultipart) -> None:
        """Send email via SMTP (blocking)."""
        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.smtp_user, self.config.smtp_password)
            server.send_message(msg)
    
    async def notify(self, event: NotificationEvent) -> NotificationResult:
        """
        Send notification for an event.
        
        Args:
            event: NotificationEvent with all required data
            
        Returns:
            NotificationResult with success status
        """
        # Prepare template data
        template_data = {
            'user_name': event.user_name,
            'user_email': event.user_email,
            'job_id': event.job_id[:8] + '...' if len(event.job_id) > 8 else event.job_id,
            'topic': event.topic[:100] + '...' if len(event.topic) > 100 else event.topic,
            **event.data
        }
        
        # Render template
        html_content = self._render_template(event.event_type, template_data)
        subject = self._get_subject(event.event_type, template_data)
        
        # Send email
        result = await self._send_email_async(event.user_email, subject, html_content)
        result.event_type = event.event_type
        
        # Track history
        self._notification_history.append(result)
        
        return result
    
    async def notify_job_started(
        self,
        user_email: str,
        user_name: str,
        job_id: str,
        topic: str
    ) -> NotificationResult:
        """Send job started notification."""
        event = NotificationEvent(
            event_type=NotificationType.JOB_STARTED,
            user_email=user_email,
            user_name=user_name,
            job_id=job_id,
            topic=topic
        )
        return await self.notify(event)
    
    async def notify_job_completed(
        self,
        user_email: str,
        user_name: str,
        job_id: str,
        topic: str,
        word_count: int,
        sections_count: int
    ) -> NotificationResult:
        """Send job completed notification."""
        event = NotificationEvent(
            event_type=NotificationType.JOB_COMPLETED,
            user_email=user_email,
            user_name=user_name,
            job_id=job_id,
            topic=topic,
            data={
                'word_count': f"{word_count:,}",
                'sections_count': sections_count
            }
        )
        return await self.notify(event)
    
    async def notify_job_failed(
        self,
        user_email: str,
        user_name: str,
        job_id: str,
        topic: str,
        error_message: str
    ) -> NotificationResult:
        """Send job failed notification."""
        event = NotificationEvent(
            event_type=NotificationType.JOB_FAILED,
            user_email=user_email,
            user_name=user_name,
            job_id=job_id,
            topic=topic,
            data={'error_message': error_message}
        )
        return await self.notify(event)
    
    async def notify_review_ready(
        self,
        user_email: str,
        user_name: str,
        job_id: str,
        topic: str,
        review_data: Dict[str, Any]
    ) -> NotificationResult:
        """Send review ready notification."""
        # Format review data for template
        decision = review_data.get('overall_assessment', 'pending')
        decision_colors = {
            'accept': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
            'minor_revision': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'major_revision': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'reject': 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)'
        }
        
        strengths = review_data.get('aggregated_strengths', [])[:3]
        revisions = review_data.get('priority_revisions', [])[:3]
        
        event = NotificationEvent(
            event_type=NotificationType.REVIEW_READY,
            user_email=user_email,
            user_name=user_name,
            job_id=job_id,
            topic=topic,
            data={
                'decision': decision.upper().replace('_', ' '),
                'decision_color': decision_colors.get(decision, decision_colors['minor_revision']),
                'consensus_score': review_data.get('consensus_score', 0),
                'reviewer_count': review_data.get('reviewer_count', 7),
                'agreement_level': review_data.get('agreement_level', 'majority'),
                'strengths_html': ''.join(f'<li>{s}</li>' for s in strengths),
                'revisions_html': '<br>'.join(f"• {r}" for r in revisions)
            }
        )
        return await self.notify(event)
    
    async def notify_scopus_score(
        self,
        user_email: str,
        user_name: str,
        job_id: str,
        topic: str,
        score_data: Dict[str, Any]
    ) -> NotificationResult:
        """Send Scopus score notification."""
        criteria = score_data.get('criteria_scores', {})
        criteria_html = ''
        for name, data in criteria.items():
            score = data.get('score', 0) if isinstance(data, dict) else data
            criteria_html += f'<tr><td style="padding: 8px;">{name.replace("_", " ").title()}</td>'
            criteria_html += f'<td style="padding: 8px; text-align: right;">{score*100:.0f}%</td></tr>'
        
        recommendations = score_data.get('recommendations', [])[:4]
        
        event = NotificationEvent(
            event_type=NotificationType.SCOPUS_SCORE,
            user_email=user_email,
            user_name=user_name,
            job_id=job_id,
            topic=topic,
            data={
                'overall_score': f"{score_data.get('overall_score', 0)*100:.0f}",
                'quality_level': score_data.get('quality_level', 'Q1 Ready').replace('_', ' ').title(),
                'q1_ready': '✅ Yes' if score_data.get('q1_ready', False) else '❌ No',
                'acceptance_prob': f"{score_data.get('acceptance_probability', {}).get('estimate', 0)*100:.0f}",
                'criteria_html': criteria_html,
                'recommendations_html': ''.join(f'<li>{r}</li>' for r in recommendations)
            }
        )
        return await self.notify(event)
    
    def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent notification history."""
        return [
            {
                'success': r.success,
                'event_type': r.event_type.value,
                'recipient': r.recipient,
                'sent_at': r.sent_at,
                'error': r.error
            }
            for r in self._notification_history[-limit:]
        ]


# Singleton instance
email_notification_agent = EmailNotificationAgent()
