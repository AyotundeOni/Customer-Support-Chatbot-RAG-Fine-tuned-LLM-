"""
Gmail SMTP email service for sending support ticket notifications.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import config
from tickets.models import Ticket


class EmailService:
    """Gmail SMTP email service."""
    
    def __init__(self):
        """Initialize with Gmail credentials from config."""
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.sender_email = config.GMAIL_EMAIL
        self.sender_password = config.GMAIL_APP_PASSWORD
        self.support_email = config.SUPPORT_EMAIL
    
    def send_ticket_notification(self, ticket: Ticket) -> bool:
        """Send email notification for a new support ticket.
        
        Args:
            ticket: The ticket to send notification for
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Support Ticket #{ticket.id}] {self._get_priority_emoji(ticket.priority)} {ticket.problem_summary[:50]}..."
            msg["From"] = self.sender_email
            msg["To"] = self.support_email
            
            # Create email content
            text_content = self._create_text_content(ticket)
            html_content = self._create_html_content(ticket)
            
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email, 
                    self.support_email, 
                    msg.as_string()
                )
            
            print(f"✅ Email sent for ticket #{ticket.id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def _get_priority_emoji(self, priority) -> str:
        """Get emoji for priority level."""
        priority_emojis = {
            "urgent": "🚨",
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }
        priority_value = priority.value if hasattr(priority, 'value') else str(priority)
        return priority_emojis.get(priority_value, "📝")
    
    def _create_text_content(self, ticket: Ticket) -> str:
        """Create plain text email content."""
        created_time = ticket.created_at.strftime('%Y-%m-%d %H:%M UTC') if ticket.created_at else 'N/A'
        priority_str = ticket.priority.value.upper() if ticket.priority else 'N/A'
        sentiment_score_str = f"{ticket.sentiment_score:.2f}" if ticket.sentiment_score else 'N/A'
        
        return f"""
New Support Ticket #{ticket.id}
================================

Created: {created_time}
Priority: {priority_str}
Sentiment: {ticket.sentiment_label or 'N/A'} (Score: {sentiment_score_str})

PROBLEM SUMMARY
---------------
{ticket.problem_summary}

CONVERSATION SUMMARY
--------------------
{ticket.conversation_summary or 'N/A'}

ADVICE GIVEN
------------
{ticket.advice_given or 'N/A'}

---
This ticket was automatically created by the Shopify Support Chatbot.
        """
    
    def _create_html_content(self, ticket: Ticket) -> str:
        """Create HTML email content."""
        priority_colors = {
            "urgent": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745"
        }
        priority_value = ticket.priority.value if ticket.priority else "medium"
        priority_color = priority_colors.get(priority_value, "#6c757d")
        
        created_time = ticket.created_at.strftime('%Y-%m-%d %H:%M UTC') if ticket.created_at else 'N/A'
        sentiment_score_str = f"{ticket.sentiment_score:.2f}" if ticket.sentiment_score else 'N/A'
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
        .section {{ background: white; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #667eea; }}
        .priority {{ display: inline-block; padding: 4px 12px; border-radius: 20px; color: white; font-weight: bold; background: {priority_color}; }}
        .label {{ font-weight: bold; color: #495057; }}
        .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">🎫 Support Ticket #{ticket.id}</h1>
            <p style="margin: 5px 0 0 0;">Shopify Support Chatbot</p>
        </div>
        <div class="content">
            <p>
                <span class="priority">{priority_value.upper()}</span>
                <span style="margin-left: 10px;">Created: {created_time}</span>
            </p>
            <p>
                <span class="label">Sentiment:</span> {ticket.sentiment_label or 'N/A'} 
                ({sentiment_score_str})
            </p>
            
            <div class="section">
                <h3 style="margin-top: 0;">🎯 Problem Summary</h3>
                <p>{ticket.problem_summary}</p>
            </div>
            
            <div class="section">
                <h3 style="margin-top: 0;">💬 Conversation Summary</h3>
                <p>{ticket.conversation_summary or 'No summary available'}</p>
            </div>
            
            <div class="section">
                <h3 style="margin-top: 0;">💡 Advice Given</h3>
                <p>{ticket.advice_given or 'No advice recorded'}</p>
            </div>
        </div>
        <div class="footer">
            <p>This ticket was automatically created by the Shopify Support Chatbot.</p>
        </div>
    </div>
</body>
</html>
        """


def send_ticket_email(ticket: Ticket) -> bool:
    """Send email notification for a ticket.
    
    Args:
        ticket: The ticket to notify about
        
    Returns:
        True if successful
    """
    service = EmailService()
    return service.send_ticket_notification(ticket)
