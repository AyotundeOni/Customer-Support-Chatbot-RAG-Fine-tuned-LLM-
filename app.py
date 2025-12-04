"""
Shopify Concierge - Premium Customer Support Chatbot
"""
import streamlit as st
import os
from agents.support_agent import SupportAgent
from tickets.database import init_db
from tickets.models import TicketPriority

# Page configuration
st.set_page_config(
    page_title="Shopify Concierge",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    """Load custom CSS."""
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables."""
    if "agent" not in st.session_state:
        # Generate a session ID if not exists
        if "session_id" not in st.session_state:
            import uuid
            st.session_state.session_id = str(uuid.uuid4())
            
        st.session_state.agent = SupportAgent(session_id=st.session_state.session_id)
        st.session_state.messages = []
        st.session_state.ticket_created = False
        st.session_state.show_ticket_form = False
        st.session_state.last_sentiment = None

def render_sidebar():
    """Render the premium sidebar."""
    with st.sidebar:
        # Branding
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 20px; margin: 0; color: #fff;">🛍️ Shopify Concierge</h1>
            <p style="font-size: 10px; color: #10B981; margin: 0;">● SYSTEM OPERATIONAL</p>
        </div>
        """, unsafe_allow_html=True)
        
        # User Profile Card
        st.markdown("""
        <div class="profile-card">
            <div class="avatar">
                SJ
                <div class="vip-badge">VIP</div>
            </div>
            <div class="profile-info">
                <h3>Sarah Jenkins</h3>
                <p>sarah.j@example.com</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats
        st.markdown("""
        <div class="stats-container">
            <div class="stat-box">
                <div class="stat-label">CUSTOMER SINCE</div>
                <div class="stat-value">Oct 2021</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">LIFETIME VALUE</div>
                <div class="stat-value green">$1,240.50</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Live Sentiment
        if st.session_state.agent:
            sentiment_summary = st.session_state.agent.get_sentiment_summary()
            # Determine dominant sentiment
            neg = sentiment_summary.get('negative', 0)
            pos = sentiment_summary.get('positive', 0)
            
            if neg > 0.5:
                icon, label, color = "😔", "Negative", "#EF4444"
            elif pos > 0.5:
                icon, label, color = "😊", "Positive", "#10B981"
            else:
                icon, label, color = "😐", "Neutral", "#9CA3AF"
                
            st.markdown(f"""
            <div class="sentiment-card">
                <div class="sentiment-header">
                    <div class="sentiment-icon">{icon}</div>
                    <div>
                        <div class="sentiment-label">CURRENT SENTIMENT</div>
                        <div class="sentiment-value" style="color: {color}">{label}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent Orders
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 12px; font-weight: 600; color: #9CA3AF;">RECENT ORDERS</span>
            <span style="font-size: 10px; color: #6366F1; cursor: pointer;">View All</span>
        </div>
        
        <div class="order-card">
            <div class="order-header">
                <span class="order-id">#SH-90210</span>
                <span class="order-status">IN TRANSIT</span>
            </div>
            <div class="order-item">
                <div class="item-icon">🧶</div>
                <div class="item-details">
                    <h4>Merino Wool Sweater</h4>
                    <p>Oatmeal / M</p>
                </div>
            </div>
            <div class="order-item">
                <div class="item-icon">🧵</div>
                <div class="item-details">
                    <h4>Classic Leather Belt</h4>
                    <p>Black / S</p>
                </div>
            </div>
            <div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 11px; color: #10B981;">🕒 Arriving Thursday</span>
                <span style="font-size: 11px; text-decoration: underline; color: #9CA3AF;">Track Package</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tickets created in this session
        if st.session_state.agent and st.session_state.agent.get_created_tickets():
            tickets = st.session_state.agent.get_created_tickets()
            st.markdown("### 🎫 Active Tickets")
            for tid in tickets:
                st.markdown(f"""
                <div style="background: #1F232E; padding: 8px; border-radius: 6px; margin-bottom: 8px; border: 1px solid #2D3240;">
                    <span style="color: #F59E0B;">Ticket #{tid}</span>
                    <span style="float: right; font-size: 10px; color: #9CA3AF;">OPEN</span>
                </div>
                """, unsafe_allow_html=True)

def main():
    """Main application function."""
    # Load styles
    load_css()
    
    # Initialize
    init_db()
    init_session_state()
    
    # Render Sidebar
    render_sidebar()
    
    # Main Chat Area Header
    st.markdown(f"""
    <div class="chat-header">
        <div class="session-badge">
            <div class="status-dot"></div>
            Live Session ID: #{st.session_state.session_id[:6].upper()}
        </div>
        <div class="encrypted-badge">
            🔒 End-to-End Encrypted
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat Input
    if prompt := st.chat_input("Ask about orders, returns, or shipping..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.agent.chat(prompt)
                    response = result["response"]
                    
                    st.write(response)
                    
                    # Handle ticket creation
                    if result.get("ticket_created"):
                        ticket_info = result["ticket_created"]
                        st.markdown(f"""
                        <div style="background: #1F232E; border: 1px solid #10B981; padding: 16px; border-radius: 12px; margin-top: 10px;">
                            <h3 style="margin: 0; color: #10B981;">✅ Ticket Created</h3>
                            <p style="margin: 5px 0 0 0; color: #E5E7EB;">Ticket #{ticket_info['ticket_id']} has been logged.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state.ticket_created = True
                        st.balloons()
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Footer
    st.markdown('<div class="footer-text">AI Assistance enabled • Personal info is masked</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
