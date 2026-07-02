import streamlit as st
import yfinance as yf
from textblob import TextBlob
import plotly.graph_objects as go
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io
import pytz
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# Force rebuild - v1.0.2

# Page Config
st.set_page_config(
    page_title="SentiStock Analytics - AI-Powered Stock Analysis", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"  # Open sidebar by default on mobile
)

# Custom CSS
st.markdown("""
<style>
    /* Glassmorphism cards */
    .metric-card {
        background: rgba(30, 30, 30, 0.7);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 215, 0, 0.2);
        margin-bottom: 15px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(255, 215, 0, 0.3);
    }
    
    /* Enhanced metrics */
    .stMetric {
        background: linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #FFD700;
    }
    
    /* Bullish/Bearish badges */
    .bullish {
        color: #00FF88;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    .bearish {
        color: #FF4444;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
    }
    
    /* Gold accent for headers */
    h1, h2, h3 {
        color: #FFD700 !important;
    }
    
    /* Smooth transitions */
    * {
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def get_sentiment_color(score):
    if score > 0.1: return "green"
    elif score < -0.1: return "red"
    else: return "orange"

def get_sentiment_label(score):
    if score > 0.1: return "BULLISH 🚀"
    elif score < -0.1: return "BEARISH 📉"
    else: return "NEUTRAL 😐"

def format_large_number(num):
    if num is None: return "N/A"
    if num >= 1_000_000_000_000: return f"${num/1_000_000_000_000:.2f}T"
    if num >= 1_000_000_000: return f"${num/1_000_000_000:.2f}B"
    if num >= 1_000_000: return f"${num/1_000_000:.2f}M"
    return f"${num:.2f}"

def as_number(value, fallback=0.0):
    """Return a numeric quote value, or a fallback when providers return null data."""
    try:
        if value is None:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback

def apply_scenario(base_sentiment, scenario):
    """Apply scenario adjustments to sentiment"""
    scenarios = {
        "None": 1.0,
        "Interest Rates +1%": 0.75,
        "Tech Acquisition Announced": 1.3,
        "Global Recession Fear": 0.5,
        "Earnings Beat Expectation": 1.4,
        "Supply Chain Disruption": 0.65
    }
    return base_sentiment * scenarios.get(scenario, 1.0)

def generate_certificate(ticker, price, recommendation, sentiment_score, pe_ratio, market_cap):
    """Generate a professional analysis certificate"""
    # Create image
    img = Image.new('RGB', (1200, 800), color='#0E1117')
    draw = ImageDraw.Draw(img)
    
    # Try to use default font, fallback to basic if not available
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
        header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        body_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        title_font = header_font = body_font = small_font = ImageFont.load_default()
    
    # Gold border
    draw.rectangle([20, 20, 1180, 780], outline='#FFD700', width=5)
    draw.rectangle([30, 30, 1170, 770], outline='#FFD700', width=2)
    
    # Title
    draw.text((600, 80), "STOCK ANALYSIS CERTIFICATE", fill='#FFD700', font=title_font, anchor='mm')
    draw.text((600, 150), f"Analysis Report: {ticker}", fill='#FFFFFF', font=header_font, anchor='mm')
    
    # Divider line
    draw.line([(100, 190), (1100, 190)], fill='#FFD700', width=3)
    
    # Main recommendation
    rec_color = '#00FF88' if 'BUY' in recommendation else '#FF4444' if 'SELL' in recommendation else '#FFD700'
    draw.text((600, 280), f"RECOMMENDATION: {recommendation}", fill=rec_color, font=header_font, anchor='mm')
    
    # Metrics
    y_pos = 360
    metrics = [
        f"Current Price: ${price:.2f}",
        f"Sentiment Score: {sentiment_score:.2f}",
        f"P/E Ratio: {pe_ratio}",
        f"Market Cap: {market_cap}"
    ]
    
    for metric in metrics:
        draw.text((600, y_pos), metric, fill='#FFFFFF', font=body_font, anchor='mm')
        y_pos += 50
    
    # Footer
    draw.line([(100, 640), (1100, 640)], fill='#FFD700', width=2)
    draw.text((600, 690), "Analyzed by Abhi Bhardwaj - SentiStock Analytics", fill='#888888', font=body_font, anchor='mm')
    draw.text((600, 740), f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", fill='#666666', font=small_font, anchor='mm')
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def generate_pdf_report(ticker, info, hist, news, analyzed_news, recommendation, target_price, risk_rating, beta, sentiment_score, social_buzz, buzz_mentions):
    """Generate comprehensive PDF stock report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1E40AF'), spaceAfter=30)
    story.append(Paragraph(f"Stock Analysis Report: {ticker}", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    current_price = as_number(info.get('currentPrice') or info.get('regularMarketPrice'))
    summary_data = [
        ['Recommendation', recommendation],
        ['Current Price', f"${current_price:.2f}"],
        ['Target Price', f"${target_price:.2f}"],
        ['Risk Level', f"{risk_rating} (Beta: {beta:.2f})"],
        ['Sentiment Score', f"{sentiment_score:.2f}"],
        ['Social Buzz', f"{social_buzz} ({buzz_mentions} mentions)"]
    ]
    summary_table = Table(summary_data, colWidths=[2.5*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E5E7EB')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT')
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Fundamentals
    story.append(Paragraph("Fundamental Analysis", styles['Heading2']))
    fund_data = [
        ['Metric', 'Value'],
        ['Market Cap', format_large_number(info.get('marketCap'))],
        ['P/E Ratio', str(info.get('trailingPE', 'N/A'))],
        ['52-Week High', f"${info.get('fiftyTwoWeekHigh', 0):.2f}"],
        ['52-Week Low', f"${info.get('fiftyTwoWeekLow', 0):.2f}"],
        ['Average Volume', format_large_number(info.get('averageVolume'))]
    ]
    fund_table = Table(fund_data, colWidths=[2.5*inch, 3*inch])
    fund_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10)
    ]))
    story.append(fund_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Sentiment Analysis
    story.append(Paragraph("News Sentiment Analysis", styles['Heading2']))
    if analyzed_news:
        avg_sentiment = sum(n['polarity'] for n in analyzed_news) / len(analyzed_news)
        story.append(Paragraph(f"Average Sentiment: {avg_sentiment:.2f} ({len(analyzed_news)} articles analyzed)", styles['Normal']))
    else:
        story.append(Paragraph("No news data available.", styles['Normal']))
    
    # Footer
    story.append(PageBreak())
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("Disclaimer", styles['Heading3']))
    story.append(Paragraph("This report is for informational purposes only and does not constitute financial advice. Past performance does not guarantee future results. Consult a licensed financial advisor before making investment decisions.", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Analyzed by: Abhi Bhardwaj - SentiStock Analytics", styles['Normal']))
    story.append(Paragraph(f"Data Source: Yahoo Finance", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Initialize session state for watchlist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Sidebar
with st.sidebar:
    st.title("🤖 SentiStock Analytics")
    
    # Watchlist Section
    st.markdown("---")
    st.markdown("### ⭐ Watchlist")
    if st.session_state.watchlist:
        watchlist_ticker = st.selectbox("Quick Access", st.session_state.watchlist)
        if st.button("Load from Watchlist"):
            selected_tickers = [watchlist_ticker]
    else:
        st.caption("No favorites yet. Add stocks below!")
    
    # Theme Toggle
    theme_mode = st.toggle("☀️ Light Mode", value=False)
    if theme_mode:
        st.markdown("""
        <style>
            .stApp {
                background-color: #FFFFFF !important;
                color: #000000 !important;
            }
            .stSidebar {
                background-color: #F8F9FA !important;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #1E40AF !important;
            }
            .stMetric {
                background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%) !important;
                border-left: 4px solid #1E40AF !important;
            }
            .metric-card {
                background: rgba(243, 244, 246, 0.7) !important;
                border: 1px solid rgba(30, 64, 175, 0.2) !important;
            }
            /* Fix text colors */
            p, span, div {
                color: #000000 !important;
            }
            /* Fix labels */
            .stMarkdown, .stText {
                color: #000000 !important;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            /* Ensure dark mode styles */
            .stApp {
                background-color: #0E1117 !important;
                color: #FAFAFA !important;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # Analysis Mode
    analysis_mode = st.radio(
        "Analysis Mode",
        ["Quick Scan (1Y)", "Deep Dive (3Y)", "Technical (6M)"],
        index=0
    )
    
    # Period mapping
    period_map = {
        "Quick Scan (1Y)": "1y",
        "Deep Dive (3Y)": "3y",
        "Technical (6M)": "6mo"
    }
    selected_period = period_map[analysis_mode]
    
    st.markdown("---")
    
    # Market Selection
    market = st.radio(
        "Select Market",
        ["🇺🇸 US", "🇮🇳 India", "🇬🇧 UK", "🇩🇪 Germany", "🇯🇵 Japan", "🇨🇦 Canada", "🇦🇺 Australia"],
        index=0,
        horizontal=True
    )
    
    # Stock Selection based on market
    if market == "🇺🇸 US":
        popular_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META"]
        additional_tickers = [
            # Tech Giants
            "AMD", "INTC", "AVGO", "ORCL", "CSCO", "ADBE", "CRM", "NOW",
            # Growth/Tech
            "NFLX", "UBER", "SNOW", "PLTR", "CRWD", "DDOG", "ZS", "MDB",
            # Fintech/Payments
            "COIN", "PYPL", "SQ", "V", "MA", "AXP",
            # E-commerce/Retail
            "SHOP", "WMT", "TGT", "COST", "HD", "LOW",
            # Finance
            "JPM", "BAC", "GS", "MS", "C", "WFC", "BLK",
            # Consumer
            "KO", "PEP", "MCD", "SBUX", "NKE", "LULU", "DIS",
            # Healthcare/Pharma
            "JNJ", "UNH", "PFE", "ABBV", "LLY", "TMO", "DHR",
            # Energy
            "XOM", "CVX", "COP", "SLB", "OXY",
            # Indexes/ETFs
            "SPY", "QQQ", "IWM", "DIA"
        ]
        default_ticker = ["TSLA"]
        custom_hint = "e.g. COIN, DIS"
        suffix = ""
        
    elif market == "🇮🇳 India":
        popular_tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS"]
        additional_tickers = [
            # IT Services
            "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "LTIM.NS", "PERSISTENT.NS",
            # Banking & Finance
            "AXISBANK.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "INDUSINDBK.NS", "PNBBANK.NS",
            # Infrastructure & Conglomerates
            "LT.NS", "ADANIENT.NS", "ADANIPORTS.NS", "GODREJCP.NS",
            # Automotive
            "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "BAJAJ-AUTO.NS",
            # Metals & Mining
            "TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "COALINDIA.NS",
            # Telecom
            "BHARTIARTL.NS", "IDEA.NS",
            # Pharma
            "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "BIOCON.NS",
            # Consumer & FMCG
            "ASIANPAINT.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "DABUR.NS", "BRITANNIA.NS",
            # Energy & Power
            "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BPCL.NS", "IOC.NS",
            # Cement
            "ULTRACEMCO.NS", "GRASIM.NS", "AMBUJACEM.NS"
        ]
        default_ticker = ["RELIANCE.NS"]
        custom_hint = "e.g. TATAMOTORS.NS"
        suffix = ".NS"
        
    elif market == "🇬🇧 UK":
        popular_tickers = ["HSBA.L", "BP.L", "SHEL.L", "ULVR.L", "AZN.L", "GSK.L", "DGE.L"]
        additional_tickers = ["BATS.L", "RIO.L", "LSEG.L", "NG.L", "BARC.L", "LLOY.L", "VOD.L"]
        default_ticker = ["HSBA.L"]
        custom_hint = "e.g. BP.L"
        suffix = ".L"
        
    elif market == "🇩🇪 Germany":
        popular_tickers = ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "VOW3.DE", "BAS.DE", "MBG.DE"]
        additional_tickers = ["BMW.DE", "ADS.DE", "DB1.DE", "DAI.DE", "EOAN.DE"]
        default_ticker = ["SAP.DE"]
        custom_hint = "e.g. BMW.DE"
        suffix = ".DE"
        
    elif market == "🇯🇵 Japan":
        popular_tickers = ["7203.T", "6758.T", "9984.T", "6861.T", "8306.T", "7267.T", "9433.T"]
        additional_tickers = ["6902.T", "6954.T", "8035.T", "4063.T", "7974.T"]
        default_ticker = ["7203.T"]
        custom_hint = "e.g. 6758.T (Sony)"
        suffix = ".T"
        
    elif market == "🇨🇦 Canada":
        popular_tickers = ["RY.TO", "TD.TO", "SHOP.TO", "ENB.TO", "CNQ.TO", "BMO.TO", "BNS.TO"]
        additional_tickers = ["CP.TO", "TRP.TO", "SU.TO", "CNR.TO", "MFC.TO"]
        default_ticker = ["SHOP.TO"]
        custom_hint = "e.g. TD.TO"
        suffix = ".TO"
        
    else:  # Australia
        popular_tickers = ["BHP.AX", "CBA.AX", "NAB.AX", "WBC.AX", "CSL.AX", "ANZ.AX", "WES.AX"]
        additional_tickers = ["RIO.AX", "FMG.AX", "WOW.AX", "TLS.AX", "MQG.AX"]
        default_ticker = ["BHP.AX"]
        custom_hint = "e.g. CBA.AX"
        suffix = ".AX"
    
    selected_tickers = st.multiselect(
        "Select Stocks", 
        options=popular_tickers + additional_tickers,
        default=default_ticker
    )
    
    custom_ticker = st.text_input(f"Or type a ticker ({custom_hint})")
    if custom_ticker:
        custom_ticker = custom_ticker.upper()
        # Auto-add suffix if not present
        if suffix and not any(custom_ticker.endswith(ext) for ext in [suffix, ".NS", ".BO", ".L", ".DE", ".T", ".TO", ".AX"]):
            custom_ticker = f"{custom_ticker}{suffix}"
        if custom_ticker not in selected_tickers:
            selected_tickers.append(custom_ticker)
    
    st.markdown("---")
    
    # Technical Indicator Controls
    st.subheader("Technical Indicators")
    show_indicators = st.checkbox("Show Technical Indicators", value=True)
    
    if show_indicators:
        rsi_period = st.slider("RSI Period", min_value=5, max_value=30, value=14)
        ma_short = st.number_input("Short MA Period", min_value=5, max_value=50, value=20)
        ma_long = st.number_input("Long MA Period", min_value=20, max_value=200, value=50)
        show_macd = st.checkbox("Show MACD", value=True)
    
    st.markdown("---")
    st.markdown("### ✨ Features")
    st.markdown("- 📊 **Multi-Stock Comparison**")
    st.markdown("- 💰 **Real-time Prices**")
    st.markdown("- 📰 **Sentiment Analysis**")
    st.markdown("- 📉 **Technical Indicators**")
    st.markdown("- 🔮 **Scenario Planning**")

# Mobile User Hint
st.info("📱 **Mobile Users**: Tap the ☰ menu (top-left) to select markets and stocks!")

# Main Page Title
st.title("📈 SentiStock Analytics - AI-Powered Stock Analysis")
st.markdown("---")

if not selected_tickers:
    st.info("👈 Select or enter a stock ticker to get started!")
    st.stop()

# URL Sharing Feature
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Share Analysis")
if selected_tickers:
    share_ticker = selected_tickers[0]
    share_url = f"?ticker={share_ticker}"
    st.sidebar.code(share_url, language=None)
    st.sidebar.caption("Copy and share this URL parameter")

# Data Fetching with Progress
data = {}
progress_text = "Fetching market data..."
progress_bar = st.progress(0)

for i, ticker in enumerate(selected_tickers):
    with st.spinner(f"Loading {ticker}..."):
        data[ticker] = yf.Ticker(ticker)
    progress_bar.progress((i + 1) / len(selected_tickers))
    
progress_bar.empty()

# --- COMPARISON MODE (If > 1 ticker) ---
if len(selected_tickers) > 1:
    st.header("📊 Market Comparison")
    
    # Metrics Table
    cols = st.columns(len(selected_tickers))
    comparison_data = []
    
    for idx, ticker in enumerate(selected_tickers):
        stock = data[ticker]
        info = stock.info
        current_price = as_number(info.get('currentPrice') or info.get('regularMarketPrice'))
        previous_close = as_number(info.get('previousClose'), current_price)
        delta = current_price - previous_close
        delta_percent = (delta / previous_close) * 100 if previous_close else 0
        
        comparison_data.append({
            'Ticker': ticker,
            'Price': f"${current_price:.2f}",
            'Change %': f"{delta_percent:.2f}%",
            'Market Cap': format_large_number(info.get('marketCap')),
            'P/E': f"{info.get('trailingPE', 'N/A')}"
        })
        
        with cols[idx]:
            st.metric(
                label=ticker, 
                value=f"${current_price:.2f}", 
                delta=f"{delta_percent:.2f}%"
            )
    
    # Data Editor for Comparison
    with st.expander("📊 Detailed Comparison Table", expanded=False):
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    # Comparison Chart
    st.subheader("Price History Comparison")
    fig = go.Figure()
    for ticker in selected_tickers:
        hist = data[ticker].history(period=selected_period)
        if not hist.empty:
            start_price = hist['Close'].iloc[0]
            normalized_close = ((hist['Close'] - start_price) / start_price) * 100
            fig.add_trace(go.Scatter(x=hist.index, y=normalized_close, mode='lines', name=ticker))
    
    fig.update_layout(
        yaxis_title="Change (%)", 
        hovermode="x unified",
        template="plotly_dark",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

# --- STOCK BREAKDOWN (Iterate through tickers) ---
st.markdown("---")
st.header("💰 Stock Breakdown")

tabs = st.tabs(selected_tickers)

for i, ticker in enumerate(selected_tickers):
    with tabs[i]:
        with st.status(f"Analyzing {ticker}...", expanded=True) as status:
            st.write("Fetching fundamentals...")
            stock = data[ticker]
            info = stock.info
            
            st.write("Analyzing news sentiment...")
            news = stock.news
            
            st.write("Calculating technical indicators...")
            hist = stock.history(period=selected_period)
            
            status.update(label=f"Analysis complete for {ticker}!", state="complete", expanded=False)
        
        # Data Freshness & Watchlist
        fresh_col1, fresh_col2, fresh_col3 = st.columns([2, 1, 1])
        with fresh_col1:
            current_time = datetime.now(pytz.timezone('America/New_York'))
            st.caption(f"🕐 Last Updated: {current_time.strftime('%I:%M %p ET')} | {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')}")
        with fresh_col2:
            # Market status
            market_open = 9 <= current_time.hour < 16 and current_time.weekday() < 5
            status_emoji = "🟢" if market_open else "🔴"
            st.caption(f"{status_emoji} Market: {'Open' if market_open else 'Closed'}")
        with fresh_col3:
            # Watchlist toggle
            if ticker in st.session_state.watchlist:
                if st.button(f"💔 Remove from Watchlist", key=f"remove_{ticker}"):
                    st.session_state.watchlist.remove(ticker)
                    st.success(f"Removed {ticker}")
            else:
                if st.button(f"⭐ Add to Watchlist", key=f"add_{ticker}"):
                    st.session_state.watchlist.append(ticker)
                    st.success(f"Added {ticker} to watchlist!")
        
        
        # Institutional Ownership
        st.markdown("---")
        st.subheader("🏦 Institutional Ownership")
        institutional_holders = stock.institutional_holders
        if not institutional_holders.empty:
            st.dataframe(institutional_holders.head(5), use_container_width=True, hide_index=True)
        else:
            st.info("No institutional ownership data available.")
        
        # Fundamentals
        col1, col2, col3, col4 = st.columns(4)
        current_price = as_number(info.get('currentPrice') or info.get('regularMarketPrice'))
        previous_close = as_number(info.get('previousClose'), current_price)
        beta = info.get('beta', 1.0)
        
        with col1: st.metric("Current Price", f"${current_price:.2f}")
        with col2: st.metric("Market Cap", format_large_number(info.get('marketCap')))
        with col3: st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
        with col4: st.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")

        # Scenario Injector 🔮
        st.markdown("---")
        st.subheader("🔮 Scenario Planning")
        scenario_col1, scenario_col2 = st.columns([2, 1])
        
        with scenario_col1:
            selected_scenario = st.selectbox(
                "What if...",
                ["None", "Interest Rates +1%", "Tech Acquisition Announced", 
                 "Global Recession Fear", "Earnings Beat Expectation", "Supply Chain Disruption"],
                key=f"scenario_{ticker}"
            )
        
        # Sentiment
        total_polarity = 0
        analyzed_news = []
        
        if news:
            for item in news:
                title = item.get('title', '')
                if not title and 'content' in item: title = item['content'].get('title', '')
                link = item.get('link', '')
                publisher = item.get('publisher', 'Unknown')
                
                blob = TextBlob(title)
                polarity = blob.sentiment.polarity
                total_polarity += polarity
                analyzed_news.append({'title': title, 'link': link, 'publisher': publisher, 'polarity': polarity})
            
            avg_polarity = total_polarity / len(news)
        else:
            avg_polarity = 0
        
        # Apply scenario adjustment
        base_sentiment = avg_polarity
        adjusted_sentiment = apply_scenario(base_sentiment, selected_scenario)
        
        # Generate recommendation
        if adjusted_sentiment > 0.1:
            recommendation = "BUY"
        elif adjusted_sentiment < -0.1:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"

        # Calculate target price and risk metrics
        if current_price > 0:
            target_price = current_price * (1 + adjusted_sentiment * 0.3)  # 30% sentiment weight
            upside_percent = ((target_price - current_price) / current_price) * 100
        else:
            target_price = 0.0
            upside_percent = 0.0
        
        # Risk rating based on beta
        if beta < 0.8:
            risk_rating = "Low"
            risk_color = "green"
        elif beta < 1.5:
            risk_rating = "Medium"
            risk_color = "orange"
        else:
            risk_rating = "High"
            risk_color = "red"
        
        # Social buzz (based on news volume)
        news_volume = len(analyzed_news) if analyzed_news else 0
        if news_volume > 15:
            social_buzz = "🔥 Very High"
            buzz_mentions = f"{news_volume * 500}+"
        elif news_volume > 8:
            social_buzz = "📈 High"
            buzz_mentions = f"{news_volume * 300}+"
        elif news_volume > 3:
            social_buzz = "💬 Moderate"
            buzz_mentions = f"{news_volume * 150}+"
        else:
            social_buzz = "🔇 Low"
            buzz_mentions = f"<{news_volume * 100}"
        
        # Executive Summary Card
        st.markdown("---")
        st.markdown("### 📊 Executive Summary")
        
        # Theme-aware colors
        if theme_mode:  # Light mode
            card_bg = "linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%)"
            border_color = "#1E40AF"
            title_color = "#1E40AF"
            text_color = "#000000"
            label_color = "#6B7280"
        else:  # Dark mode
            card_bg = "linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%)"
            border_color = "#FFD700"
            title_color = "#FFD700"
            text_color = "#FFFFFF"
            label_color = "#888"
        
        summary_card = f"""
        <div style='background: {card_bg}; 
                    padding: 25px; border-radius: 15px; border: 2px solid {border_color}; margin-bottom: 20px;'>
            <h2 style='color: {title_color}; margin: 0 0 15px 0;'>{ticker}</h2>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
                <div>
                    <p style='color: {label_color}; margin: 5px 0;'>Recommendation</p>
                    <h3 style='color: {'#00FF88' if recommendation == 'BUY' else '#FF4444' if recommendation == 'SELL' else border_color}; margin: 0;'>{recommendation}</h3>
                </div>
                <div>
                    <p style='color: {label_color}; margin: 5px 0;'>Target Price</p>
                    <h3 style='color: {text_color}; margin: 0;'>${target_price:.2f} ({upside_percent:+.1f}%)</h3>
                </div>
                <div>
                    <p style='color: {label_color}; margin: 5px 0;'>Risk Level</p>
                    <h3 style='color: {risk_color}; margin: 0;'>{risk_rating} (β: {beta:.2f})</h3>
                </div>
                <div>
                    <p style='color: {label_color}; margin: 5px 0;'>Sentiment Score</p>
                    <h3 style='color: {text_color}; margin: 0;'>{adjusted_sentiment:.2f} ({int(abs(adjusted_sentiment) * 100)}% confidence)</h3>
                </div>
                <div>
                    <p style='color: {label_color}; margin: 5px 0;'>Social Buzz</p>
                    <h3 style='color: {text_color}; margin: 0;'>{social_buzz}</h3>
                    <p style='color: {label_color}; margin: 0; font-size: 14px;'>Mentions: {buzz_mentions} today</p>
                </div>
                <div>
                    <p style='color: {label_color}; margin: 5px 0;'>News Sentiment</p>
                    <h3 style='color: {text_color}; margin: 0;'>{get_sentiment_label(adjusted_sentiment)}</h3>
                </div>
            </div>
        </div>
        """
        st.markdown(summary_card, unsafe_allow_html=True)
        
        with scenario_col2:
            if selected_scenario != "None":
                st.metric(
                    "Scenario Impact",
                    f"{(adjusted_sentiment - base_sentiment) * 100:.1f}%",
                    delta=f"Confidence: {abs(adjusted_sentiment) * 100:.0f}%"
                )
                st.caption(f"**Adjusted Rec:** {recommendation}")
            else:
                st.metric("Base Sentiment", f"{base_sentiment:.2f}")

        st.subheader("📰 News Sentiment Analysis")
        
        # News Sentiment Filter
        if analyzed_news:
            min_sentiment = st.slider(
                "Filter news by minimum sentiment score",
                -1.0, 1.0, -1.0, 0.1,
                key=f"filter_{ticker}"
            )
            filtered_news = [n for n in analyzed_news if n['polarity'] >= min_sentiment]
            st.caption(f"Showing {len(filtered_news)} of {len(analyzed_news)} articles")
        else:
            filtered_news = []
        
        s_col1, s_col2 = st.columns([1, 3])
        with s_col1:
            st.markdown(f"## {get_sentiment_label(adjusted_sentiment)}")
            st.progress((adjusted_sentiment + 1) / 2)
        
        with s_col2:
            # Certificate Download Button
            cert_buffer = generate_certificate(
                ticker, 
                current_price, 
                recommendation,
                adjusted_sentiment,
                info.get('trailingPE', 'N/A'),
                format_large_number(info.get('marketCap'))
            )
            
            st.download_button(
                label="📜 Download Analysis Certificate",
                data=cert_buffer,
                file_name=f"{ticker}_analysis_certificate.png",
                mime="image/png",
                use_container_width=True
            )
            
            with st.expander("Latest News & Sentiment Scores", expanded=False):
                for item in filtered_news[:10]:  # Use filtered_news instead of analyzed_news
                    p_score = item['polarity']
                    p_emoji = "🟢" if p_score > 0.1 else "🔴" if p_score < -0.1 else "🟡"
                    st.markdown(f"{p_emoji} **[{item['title']}]({item['link']})**")
                    st.caption(f"Source: {item['publisher']} | Score: {p_score:.2f}")
            
            with st.expander("🔬 Named Entity Recognition (NER) on News", expanded=False):
                if analyzed_news:
                    try:
                        import spacy
                        try:
                            nlp = spacy.load("en_core_web_sm")
                        except OSError:
                            import subprocess
                            import sys
                            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], capture_output=True)
                            nlp = spacy.load("en_core_web_sm")
                        
                        entities = {"ORG": [], "GPE": [], "PERSON": []}
                        for item in analyzed_news:
                            doc = nlp(item["title"])
                            for ent in doc.ents:
                                if ent.label_ in entities:
                                    entities[ent.label_].append(ent.text)
                        
                        ner_col1, ner_col2, ner_col3 = st.columns(3)
                        with ner_col1:
                            st.markdown("**Organizations (ORG)**")
                            orgs = sorted(list(set(entities["ORG"])))[:10]
                            for org in orgs:
                                st.write(f"🏢 {org}")
                            if not orgs: st.caption("No organizations found")
                        with ner_col2:
                            st.markdown("**Locations (GPE)**")
                            gpes = sorted(list(set(entities["GPE"])))[:10]
                            for gpe in gpes:
                                st.write(f"📍 {gpe}")
                            if not gpes: st.caption("No locations found")
                        with ner_col3:
                            st.markdown("**People (PERSON)**")
                            persons = sorted(list(set(entities["PERSON"])))[:10]
                            for person in persons:
                                st.write(f"👤 {person}")
                            if not persons: st.caption("No people found")
                    except Exception as e:
                        st.info("Entities (Fallback Noun Phrases):")
                        phrases = []
                        for item in analyzed_news:
                            phrases.extend(TextBlob(item["title"]).noun_phrases)
                        phrases = sorted(list(set(phrases)))[:15]
                        for phrase in phrases:
                            st.write(f"🔑 {phrase}")
                else:
                    st.write("No news articles available to analyze.")
            
            with st.expander("📊 Granger Causality Test", expanded=False):
                if not hist.empty and analyzed_news:
                    try:
                        from statsmodels.tsa.stattools import grangercausalitytests
                        
                        daily_sent = {}
                        for item in news:
                            time_epoch = item.get('providerPublishTime', 0)
                            if time_epoch:
                                date_str = datetime.fromtimestamp(time_epoch).strftime('%Y-%m-%d')
                                daily_sent.setdefault(date_str, []).append(TextBlob(item.get('title', '')).sentiment.polarity)
                        
                        daily_avg_sent = {d: sum(p)/len(p) for d, p in daily_sent.items()}
                        
                        aligned_data = pd.DataFrame(index=hist.index)
                        aligned_data['price'] = hist['Close']
                        aligned_data['sentiment'] = aligned_data.index.map(lambda d: daily_avg_sent.get(d.strftime('%Y-%m-%d'), 0.0))
                        
                        aligned_data['sentiment'] = aligned_data['sentiment'].replace(0, np.nan).ffill().fillna(0.0)
                        
                        aligned_data['price_diff'] = aligned_data['price'].diff().dropna()
                        aligned_data['sentiment_diff'] = aligned_data['sentiment'].diff().dropna()
                        aligned_data = aligned_data.dropna()
                        
                        if len(aligned_data) > 10:
                            test_df = aligned_data[['price_diff', 'sentiment_diff']]
                            max_lag = min(5, len(test_df) // 3)
                            
                            if max_lag > 0:
                                gc_res = grangercausalitytests(test_df, max_lag=max_lag, verbose=False)
                                
                                p_values = []
                                for lag in range(1, max_lag + 1):
                                    p_val = gc_res[lag][0]['ssr_chi2test'][1]
                                    p_values.append((lag, p_val))
                                
                                min_lag, min_p = min(p_values, key=lambda x: x[1])
                                
                                st.write(f"**Causality Results (Max Lag: {max_lag} days)**")
                                if min_p < 0.05:
                                    st.success(f"✅ **Significant Causality Detected!** Sentiment statistically leads price at a lag of **{min_lag} days** (p-value: **{min_p:.4f}**).")
                                else:
                                    st.info(f"❌ **No Causal Relationship Detected.** (Minimum p-value: **{min_p:.4f}** at lag {min_lag} days, threshold: 0.05).")
                                
                                st.dataframe(pd.DataFrame([
                                    {"Lag (Days)": lag, "p-value": f"{p:.4f}", "Significant": "Yes" if p < 0.05 else "No"}
                                    for lag, p in p_values
                                ]), use_container_width=True, hide_index=True)
                            else:
                                st.warning("Not enough variance or data points to compute lags.")
                        else:
                            st.warning("Need more historical data overlap to perform Granger causality test.")
                    except Exception as e:
                        st.error(f"Error computing Granger causality: {e}")
                else:
                    st.write("No price or news data available for causality test.")

        # Price Chart with Technical Indicators
        st.subheader("Price Chart & Technical Analysis")
        
        if not hist.empty and show_indicators:
            # Calculate indicators
            hist['RSI'] = ta.rsi(hist['Close'], length=rsi_period)
            hist['SMA_Short'] = ta.sma(hist['Close'], length=ma_short)
            hist['SMA_Long'] = ta.sma(hist['Close'], length=ma_long)
            
            if show_macd:
                macd = ta.macd(hist['Close'])
                hist['MACD'] = macd['MACD_12_26_9']
                hist['MACD_signal'] = macd['MACDs_12_26_9']
            
            # Create subplots
            from plotly.subplots import make_subplots
            
            num_rows = 3 if show_macd else 2
            fig = make_subplots(
                rows=num_rows, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.5, 0.25, 0.25] if show_macd else [0.7, 0.3],
                subplot_titles=(f'{ticker} Price', 'RSI', 'MACD') if show_macd else (f'{ticker} Price', 'RSI')
            )
            
            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name='Price'
                ),
                row=1, col=1
            )
            
            # Moving Averages
            fig.add_trace(
                go.Scatter(x=hist.index, y=hist['SMA_Short'], name=f'SMA {ma_short}', line=dict(color='orange', width=1)),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=hist.index, y=hist['SMA_Long'], name=f'SMA {ma_long}', line=dict(color='blue', width=1)),
                row=1, col=1
            )
            
            # RSI
            fig.add_trace(
                go.Scatter(x=hist.index, y=hist['RSI'], name='RSI', line=dict(color='purple')),
                row=2, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            # MACD
            if show_macd:
                fig.add_trace(
                    go.Scatter(x=hist.index, y=hist['MACD'], name='MACD', line=dict(color='blue')),
                    row=3, col=1
                )
                fig.add_trace(
                    go.Scatter(x=hist.index, y=hist['MACD_signal'], name='Signal', line=dict(color='red')),
                    row=3, col=1
                )
            
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                height=800,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Raw Data Expander
            with st.expander("📊 View Raw Price Data", expanded=False):
                st.dataframe(hist[['Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'SMA_Short', 'SMA_Long']].tail(50))
        
        elif not hist.empty:
            # Simple chart without indicators
            fig = go.Figure(data=[go.Candlestick(x=hist.index,
                open=hist['Open'], high=hist['High'],
                low=hist['Low'], close=hist['Close'])])
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # PDF Report Generation
        st.markdown("---")
        st.subheader("📄 Professional PDF Report")
        st.write("Download a comprehensive analysis report with all metrics, charts, and insights.")
        if st.button(f"📥 Generate PDF Report", key=f"pdf_report_{ticker}"):
            with st.spinner("Generating professional PDF report..."):
                pdf_buffer = generate_pdf_report(ticker, info, hist, news, analyzed_news, recommendation, target_price, risk_rating, beta, adjusted_sentiment, social_buzz, buzz_mentions)
                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"{ticker}_Stock_Analysis_Report.pdf",
                    mime="application/pdf",
                    key=f"download_pdf_{ticker}",
                    use_container_width=True
                )
                st.success("✅ PDF report generated successfully!")
        
        else:
            st.warning("No price history available.")

# Attribution Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 20px;'>
    <p><strong>Built by: Abhi Bhardwaj</strong></p>
    <p>Data: <a href='https://github.com/ranaroussi/yfinance' target='_blank'>yfinance</a> | 
    Sentiment: <a href='https://textblob.readthedocs.io/' target='_blank'>TextBlob</a> | 
    <a href='https://github.com/AB0204/SentiStock-Analytics' target='_blank'>View on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
