# app.py

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph.supervisor import get_supervisor_graph
import uuid
import os
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine # Use SQLAlchemy to avoid warnings
import base64 # Added for encoding local image

# --- Page Config (Must be the first st command) ---
st.set_page_config(
    page_title="NexusCorpus Retail Analytics Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed" # Starts with the sidebar closed
)

# --- NEW FUNCTION TO ENCODE LOCAL IMAGE ---
@st.cache_data
def get_base64_image(image_path):
    """Loads a local image and returns it as a base64 encoded string."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except FileNotFoundError:
        st.error(f"Image file not found at {image_path}. Please make sure 'assets/business_tech_bg.jpg' exists.")
        return None

# --- LOAD LOCAL IMAGE ---
# IMPORTANT: Create an 'assets' folder in the same directory as app.py
# and place your 'business_tech_bg.jpg' file inside it.
image_path = os.path.join(os.path.dirname(__file__), "assets", "business_tech_bg.jpg")
image_base64 = get_base64_image(image_path)

if image_base64:
    bg_image_css = f"data:image/jpg;base64,{image_base64}"
else:
    # Fallback to a plain color if image not found
    bg_image_css = "linear-gradient(270deg, #1e3d59, #1e2a38)"


# --- Custom CSS Styling (Dark "Real-World" Theme) ---
st.markdown(f"""
<style>
    :root {{
        --bg-color: #0e1117;
        --container-bg: rgba(25, 30, 35, 0.85); /* Dark semi-transparent background */
        --container-border: rgba(255, 255, 255, 0.15);
        --text-color: #ffffff; /* Pure white for max contrast */
        --text-secondary: #d0d0d8; /* Much lighter grey for labels/captions */
        --accent-color: #00aaff; /* A bright blue for KPIs and highlights */
        --shadow-color: rgba(0, 0, 0, 0.3);

        /* --- NEW: Custom Text and Icon Colors --- */
        --color-main-caption: #FFDAB9; /* Peach */
        --color-section-header: #FFA500; /* Bright Orange */
        --color-chat-header: #FF7F50; /* Coral */
        --color-chat-caption: #AFEEEE; /* Pale Turquoise */
    }}

    /* Main app background */
    body {{
        background-image: url("{bg_image_css}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    .stApp {{
        background-color: transparent;
    }}
    
    /* --- Sidebar Styling (Dark Glassmorphism) --- */
    [data-testid="stSidebar"] {{
        background: var(--container-bg);
        backdrop-filter: blur(10px);
        border-right: 1px solid var(--container-border);
        box-shadow: 5px 0px 20px var(--shadow-color);
    }}
    
    /* --- KPI Card Styling (Dark Glassmorphism) --- */
    .kpi-card {{
        background: var(--container-bg);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 20px;
        border: 1px solid var(--container-border);
        box-shadow: 0 4px 15px var(--shadow-color);
        text-align: center;
        transition: all 0.3s ease; /* Added for hover effect */
    }}
    .kpi-card:hover {{
        transform: translateY(-5px); /* "Lift" effect on hover */
        box-shadow: 0 8px 25px var(--shadow-color);
    }}
    .kpi-card p {{ /* Metric label */
        font-size: 1.1rem;
        color: var(--text-secondary); /* Uses new lighter grey */
        margin: 0;
    }}
    .kpi-card h2 {{ /* Metric value */
        font-size: 2.5rem;
        color: var(--accent-color); 
        font-weight: 600;
        margin: 5px 0 5px 0;
    }}

    /* --- Chart Container Styling (Dark Glassmorphism) --- */
    [data-testid="stPlotlyChart"] {{
        background: var(--container-bg);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 10px;
        border: 1px solid var(--container-border);
        box-shadow: 0 4px 15px var(--shadow-color);
    }}
    
    /* --- Chat Message Styling (Dark Glassmorphism) --- */
    .stChatMessage {{
        background: var(--container-bg);
        backdrop-filter: blur(8px);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid var(--container-border);
    }}
    
    [data-testid="stChatMessageContent"][aria-label="AI message content"] {{
         background-color: rgba(0, 170, 255, 0.1); /* Light blue accent for AI */
         backdrop-filter: blur(8px);
         border: 1px solid rgba(0, 170, 255, 0.2);
    }}

    /* ---
    --- Text Color Overrides (FIX 4.0)
    --- */

    /* 1. Menu Icon Visibility Fix */
    [data-testid="stSidebarToggleButton"] {{
        background-color: rgba(165, 42, 42, 0.8); /* Dark brown background */
        border-radius: 5px;
        padding: 8px 12px; /* Add some padding around the icon */
        margin-left: -10px; /* Adjust if needed to fit layout */
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
    }}
    [data-testid="stSidebarToggleButton"] svg {{
        fill: #ffffff !important; /* Make icon white */
    }}
    [data-testid="stSidebarToggleButton"]:hover {{
        background-color: rgba(165, 42, 42, 1); /* Darker brown on hover */
    }}


    /* 2. Gradient for Main Title */
    .main-title {{
        font-size: 2.75rem;
        font-weight: 700; 
        margin-bottom: -10px; /* Pull caption up */
        background: linear-gradient(90deg, #87CEEB, #F5F5DC); /* Dark Sky Blue to Dark White/Beige */
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        color: transparent; /* Fallback for browsers that don't support -webkit-text-fill-color */
    }}
    .main-caption {{
        color: var(--color-main-caption) !important;
        font-size: 1rem;
    }}
    .section-header {{
        color: var(--color-section-header) !important;
        font-size: 1.5rem;
        font-weight: 600;
    }}
    .chat-header {{
        color: var(--color-chat-header) !important;
        font-size: 1.5rem;
        font-weight: 600;
    }}
    .chat-caption {{
        color: var(--color-chat-caption) !important;
        font-size: 1rem;
    }}

    /* Force all base text to be light */
    body, .stApp, .st-emotion-cache-16txtl3 {{
        color: var(--text-color) !important;
    }}
    
    /* Force all markdown content to be bright white (fallback) */
    [data-testid="stMarkdown"] p,
    [data-testid="stMarkdown"] li,
    [data-testid="stMarkdown"] table {{
        color: var(--text-color) !important;
    }}

    /* Force chat message text (ALL elements) to be bright white */
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] * {{
        color: var(--text-color) !important;
    }}
    
    /* Force captions to be a readable light grey (fallback) */
    .stCaption, [data-testid="stCaption"] {{
        color: var(--text-secondary) !important;
    }}
    
    /* Force sidebar/filter labels to be bright white */
    label, .st-emotion-cache-1y4d8pa, .st-emotion-cache-1r6slb0 {{
        color: var(--text-color) !important;
    }}
    /* --- END FIX --- */


    /* --- Custom Scrollbar --- */
    ::-webkit-scrollbar {{
        width: 10px;
    }}
    ::-webkit-scrollbar-track {{
        background: rgba(0,0,0,0.2);
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--accent-color);
        border-radius: 10px;
        border: 2px solid transparent;
        background-clip: content-box;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #0088cc; /* Darker blue on hover */
    }}

    /* ---
    --- FIX FOR HEADER/TOOLBAR ---
    --- */
    
    /* Hide Streamlit default footer */
    footer {{visibility: hidden;}}
    
    /* Make header transparent but keep it for the sidebar button */
    [data-testid="stHeader"] {{
        background: transparent;
    }}
    
    /* Hide the (⋮) app menu on the right */
    [data-testid="stAppToolbar"] {{
        display: none;
    }}
    
</style>
""", unsafe_allow_html=True)

# --- NEW: Define a global font color for charts ---
plot_font_color = "#ffffff" # Pure white to match CSS

# --- Helper Function (No change) ---
def is_plotly_json(s):
    try:
        data = json.loads(s)
        return isinstance(data, dict) and 'data' in data and 'layout' in data
    except (json.JSONDecodeError, TypeError):
        return False

# --- Database Connection Function (for Dashboard) ---
@st.cache_data
def load_dashboard_data():
    try:
        # Create a SQLAlchemy engine string
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        engine_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Create the engine
        engine = create_engine(engine_string)
        
        # Load tables using the engine
        df_master = pd.read_sql("SELECT * FROM gadgethub_master_sales", engine)
        df_category = pd.read_sql("SELECT * FROM gadgethub_category_breakdown", engine)
        
        return df_master, df_category
        
    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- Session State Initialization (No change) ---
if "messages" not in st.session_state:
    st.session_state.messages = [AIMessage(content="Hello! I'm your retail analytics assistant. The dashboard above shows key metrics. You can ask me for a deeper analysis below.")]
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "running" not in st.session_state:
    st.session_state.running = False


# --- Load Data ---
df_master, df_category = load_dashboard_data()

# --- Sidebar ---
with st.sidebar:
    st.image("nexuscorp_logo.png", width=150)
    st.title("Filters & Controls")
    st.markdown("Use these filters to update the main dashboard.")

    all_years = []
    all_sub_regions = []
    all_categories = []
    
    if not df_master.empty:
        all_years = sorted(df_master['year'].unique())
    if not df_category.empty:
        all_sub_regions = sorted(df_category['sub_region'].unique()) 
        all_categories = sorted(df_category['category'].unique())

    # --- Sidebar Filters ---
    selected_years = st.multiselect("Select Year(s)", all_years, default=all_years)
    selected_regions = st.multiselect("Select Region(s)", all_sub_regions, default=all_sub_regions)
    selected_categories = st.multiselect("Select Category(s)", all_categories, default=all_categories)
    
    st.divider()
    st.header("Chat Controls")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = [AIMessage(content="Chat history cleared. How can I help?")]
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.running = False
        st.rerun()

    st.divider()
    st.caption("© 2025 NexusCorpus Retail Inc. All rights reserved.")


# --- Main Dashboard ---
# --- NEW: Use st.markdown for custom colors and gradient ---
st.markdown('<h1 class="main-title">🛒 NexusCorpus Retail Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-caption">This dashboard shows high-level metrics. Ask the AI assistant below for deeper insights.</p>', unsafe_allow_html=True)
# ---

# Filter data based on sidebar selections
filtered_master_df = df_master[df_master['year'].isin(selected_years)]
filtered_category_df = df_category[
    (df_category['year'].isin(selected_years)) &
    (df_category['sub_region'].isin(selected_regions)) & 
    (df_category['category'].isin(selected_categories))
]

# --- KPI Cards (FIXED: Now uses fully filtered data) ---
if not filtered_category_df.empty:
    # 1. Sales: Calculate from the granular data that respects ALL filters
    total_sales = filtered_category_df['category_sales_amount'].sum()

    # 2. Profit: Attempt to calculate from granular data
    if 'profit_amount' in filtered_category_df.columns:
        total_profit = filtered_category_df['profit_amount'].sum()
    else:
        # Fallback to master if granular profit not available (only filters by year)
        total_profit = filtered_master_df['profit_amount'].sum() if not filtered_master_df.empty else 0

    # 3. Margin: Calculated from totals
    avg_profit_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0
    
    # 4. Customers: Attempt to calculate from granular data
    if 'num_customers' in filtered_category_df.columns:
        total_customers = filtered_category_df['num_customers'].sum()
    elif 'customer_id' in filtered_category_df.columns:
        # Ideal case: count unique IDs
        total_customers = filtered_category_df['customer_id'].nunique()
    else:
        # Fallback
        total_customers = filtered_master_df['num_customers'].sum() if not filtered_master_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="kpi-card"><p>Total Sales</p><h2>₹{total_sales:,.0f}</h2></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="kpi-card"><p>Total Profit</p><h2>₹{total_profit:,.0f}</h2></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="kpi-card"><p>Profit Margin</p><h2>{avg_profit_margin:.1f}%</h2></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="kpi-card"><p>Total Customers</p><h2>{total_customers:,}</h2></div>""", unsafe_allow_html=True)
else:
    st.warning("No data found for the selected filters.")

st.markdown("<br>", unsafe_allow_html=True)

# --- Main Charts ---
if not filtered_category_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        # --- NEW: Use st.markdown for custom colors ---
        st.markdown('<h2 class="section-header">Sales by Category</h2>', unsafe_allow_html=True)
        # ---
        category_sales = filtered_category_df.groupby('category')['category_sales_amount'].sum().reset_index()
        fig_cat = px.bar(category_sales, x='category', y='category_sales_amount', title="Category Performance", labels={'category_sales_amount': 'Total Sales'})
        
        # --- Make chart transparent and text white (FIX 2.0) ---
        fig_cat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font_color=plot_font_color,
            title_font_color=plot_font_color,
            xaxis=dict(
                title_font_color=plot_font_color,
                tickfont_color=plot_font_color,
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(
                title_font_color=plot_font_color,
                tickfont_color=plot_font_color,
                gridcolor='rgba(255,255,255,0.1)'
            )
        )
        
        st.plotly_chart(fig_cat, use_container_width=True)
        
    with col2:
        # --- NEW: Use st.markdown for custom colors ---
        st.markdown('<h2 class="section-header">Sales by Sub-Region</h2>', unsafe_allow_html=True)
        # ---
        region_sales = filtered_category_df.groupby('sub_region')['category_sales_amount'].sum().reset_index()
        fig_reg = px.pie(region_sales, names='sub_region', values='category_sales_amount', title="Regional Sales Share", hole=0.3)
        
        # --- Make chart transparent and text white (FIX 2.0) ---
        fig_reg.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font_color=plot_font_color,
            title_font_color=plot_font_color,
            legend=dict(
                font_color=plot_font_color
            )
        )
        
        st.plotly_chart(fig_reg, use_container_width=True)
else:
    st.warning("No category breakdown data found for the selected filters.")

st.markdown("---")

# --- Chat Interface ---
# --- NEW: Use st.markdown for custom colors ---
st.markdown('<h2 class="chat-header">💬 Chat with your Agentic AI Assistant</h2>', unsafe_allow_html=True)
st.markdown('<p class="chat-caption">Ask follow-up questions, request specific analysis, or get insights on the data above.</p>', unsafe_allow_html=True)
# ---

# (Chat history display, user input, and graph execution logic all remain the same)
chat_container = st.container(height=400, border=False)
with chat_container:
    for message in st.session_state.messages:
        avatar = "🤖" if isinstance(message, AIMessage) else "👤"
        with st.chat_message(message.type, avatar=avatar):
            if is_plotly_json(message.content):
                try:
                    fig = go.Figure(json.loads(message.content))
                    # --- Make AI-generated chart transparent and text white (FIX 2.0) ---
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color=plot_font_color,
                        title_font_color=plot_font_color,
                        legend=dict(
                            font_color=plot_font_color
                        ),
                        xaxis=dict(
                            title_font_color=plot_font_color,
                            tickfont_color=plot_font_color,
                            gridcolor='rgba(255,255,255,0.1)'
                        ),
                        yaxis=dict(
                            title_font_color=plot_font_color,
                            tickfont_color=plot_font_color,
                            gridcolor='rgba(255,255,255,0.1)'
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not render chart: {e}")
            else:
                st.markdown(message.content, unsafe_allow_html=True)

user_input = st.chat_input("e.g., 'What was the best selling category in Kochi in 2024?'")

if user_input and not st.session_state.running:
    st.session_state.messages.append(HumanMessage(content=user_input))
    st.session_state.running = True
    st.rerun()

if st.session_state.running and isinstance(st.session_state.messages[-1], HumanMessage):
    with chat_container:
         with st.chat_message("AI", avatar="🤖"):
               with st.spinner("Thinking... The AI agents are on the case!"):
                      st.write("...") 
    
    try:
        graph_input = {"messages": st.session_state.messages}
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        agent_system = get_supervisor_graph()
        final_state = agent_system.invoke(graph_input, config=config)

        all_messages_from_state = final_state.get('messages', [])
        last_human_msg_index = -1
        for i, msg in enumerate(reversed(all_messages_from_state)):
            if isinstance(msg, HumanMessage):
                last_human_msg_index = len(all_messages_from_state) - 1 - i
                break
        
        new_ai_messages = all_messages_from_state[last_human_msg_index + 1:]
        
        for msg in new_ai_messages:
            if isinstance(msg, AIMessage):
                st.session_state.messages.append(msg)
        
        chart_json_str = final_state.get("chart_path")
        if is_plotly_json(chart_json_str):
            if not st.session_state.messages or st.session_state.messages[-1].content != chart_json_str:
                st.session_state.messages.append(AIMessage(content=chart_json_str))
        
    except Exception as e:
        error_message = f"An error occurred: {e}"
        st.session_state.messages.append(AIMessage(content=error_message))
    finally:
        st.session_state.running = False
        st.rerun()