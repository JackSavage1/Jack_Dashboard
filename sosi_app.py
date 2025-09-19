import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="SOSI Language Services Dashboard",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stAlert {
        background-color: #e8f4fd;
        border-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# SOSI-specific data loading functions

@st.cache_data
def load_local_excel_files():
    """Load local Excel files with error handling"""
    data = {}
    
    # Check if files exist in current directory
    files = {
        'historical': 'AllDataAnalysis_20250908_194306.xlsx',
        'linguists': 'SOSiApprovedLinguists (1).xlsx',
        'staging': 'tblStaging_Raw.xlsx'
    }
    
    for key, filename in files.items():
        try:
            if os.path.exists(filename):
                if key == 'historical':
                    # Load all sheets from historical data
                    xl_file = pd.ExcelFile(filename)
                    data[key] = {}
                    for sheet in xl_file.sheet_names:
                        data[key][sheet] = pd.read_excel(filename, sheet_name=sheet)
                else:
                    # Load first sheet for other files
                    data[key] = pd.read_excel(filename, sheet_name=0)
            else:
                data[key] = None
        except Exception as e:
            data[key] = None
    
    return data

# Data cleaning functions for SOSI data will be handled within each tab as needed

# Load SOSI data files
with st.spinner("Loading SOSI data files..."):
    local_data = load_local_excel_files()

# Set API data to None since this is SOSI-specific
lass_df = None
lep_df = None

# Main header
st.markdown('<h1 class="main-header">🗣️ SOSI Language Services Dashboard</h1>', unsafe_allow_html=True)
st.markdown("### Comprehensive Analysis of Language Services and Interpreter Management")

# Display Excel file loading status
if any(local_data.values()):
    with st.expander("📁 Local Excel Files Status", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if local_data.get('historical') is not None:
                st.success("✅ Historical Data Loaded")
                if isinstance(local_data['historical'], dict):
                    st.write(f"Sheets: {', '.join(local_data['historical'].keys())}")
            else:
                st.error("❌ Historical Data Not Found")
                
        with col2:
            if local_data.get('linguists') is not None:
                st.success("✅ Linguist Directory Loaded")
                st.write(f"Records: {len(local_data['linguists'])}")
            else:
                st.error("❌ Linguist Directory Not Found")
                
        with col3:
            if local_data.get('staging') is not None:
                st.success("✅ Staging Data Loaded")
                st.write(f"Records: {len(local_data['staging'])}")
            else:
                st.error("❌ Staging Data Not Found")

# Create tabs for different pages
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Trends", "👥 Linguist Directory", "📋 Data Analysis"])

# Tab 1: Overview
with tab1:
    st.subheader("📊 SOSI Language Services Overview")
    
    # Quick stats from available data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if local_data.get('historical') and isinstance(local_data['historical'], dict):
            hist_data = local_data['historical'].get('All Historical Data')
            if hist_data is not None:
                st.metric("Total Service Requests", len(hist_data))
            else:
                st.metric("Total Service Requests", "N/A")
        else:
            st.metric("Total Service Requests", "N/A")
    
    with col2:
        if local_data.get('linguists') is not None:
            st.metric("Available Linguists", len(local_data['linguists']))
        else:
            st.metric("Available Linguists", "N/A")
    
    with col3:
        if local_data.get('historical') and isinstance(local_data['historical'], dict):
            hist_data = local_data['historical'].get('All Historical Data')
            if hist_data is not None and 'Language' in hist_data.columns:
                st.metric("Languages Supported", hist_data['Language'].nunique())
            else:
                st.metric("Languages Supported", "N/A")
        else:
            st.metric("Languages Supported", "N/A")
    
    with col4:
        if local_data.get('staging') is not None and 'Status' in local_data['staging'].columns:
            completed = len(local_data['staging'][local_data['staging']['Status'].str.contains('completed|done', case=False, na=False)])
            st.metric("Completed Services", completed)
        else:
            st.metric("Completed Services", "N/A")
    
    st.markdown("---")
    st.markdown("""
    ### 🎯 **Dashboard Features:**
    
    **📈 Trends Tab**: Analyze historical service request patterns and linguist availability over time
    
    **👥 Linguist Directory**: Search and filter available linguists by language, location, and proficiency
    
    **📋 Data Analysis**: Comprehensive analysis of service delivery, duration, and performance metrics
    
    ### 📁 **Data Sources:**
    - **Historical Analysis**: Service request trends and patterns
    - **Linguist Directory**: Approved linguist database with contact information
    - **Staging Data**: Real-time service delivery and performance metrics
    """)

# Tab 2: Trends
with tab2:
    st.subheader("📈 Trends Analysis")
    
    # Check if historical data is available
    if local_data.get('historical') and isinstance(local_data['historical'], dict):
        # Get the main historical data sheet
        hist_data = local_data['historical'].get('All Historical Data')
        
        if hist_data is not None and not hist_data.empty:
            # Convert date columns to datetime
            date_columns = ['Request Date', 'Hearing Date', 'Row Added']
            for col in date_columns:
                if col in hist_data.columns:
                    hist_data[col] = pd.to_datetime(hist_data[col], errors='coerce')
            
            # Time range filter
            st.markdown("### ⏰ Select Time Range")
            col1, col2 = st.columns(2)
            
            with col1:
                if 'Request Date' in hist_data.columns:
                    min_date = hist_data['Request Date'].min()
                    max_date = hist_data['Request Date'].max()
                    
                    if pd.notna(min_date) and pd.notna(max_date):
                        start_date = st.date_input(
                            "Start Date",
                            value=max_date - timedelta(days=365),
                            min_value=min_date.date(),
                            max_value=max_date.date()
                        )
                    else:
                        start_date = st.date_input("Start Date")
            
            with col2:
                if 'Request Date' in hist_data.columns and pd.notna(max_date):
                    end_date = st.date_input(
                        "End Date",
                        value=max_date.date(),
                        min_value=min_date.date() if pd.notna(min_date) else None,
                        max_value=max_date.date()
                    )
                else:
                    end_date = st.date_input("End Date")
            
            # Filter data by date range
            if 'Request Date' in hist_data.columns:
                mask = (hist_data['Request Date'].dt.date >= start_date) & (hist_data['Request Date'].dt.date <= end_date)
                filtered_hist = hist_data[mask].copy()
            else:
                filtered_hist = hist_data.copy()
            
            # Trend visualizations
            st.markdown("---")
            
            # Requests over time
            if 'Request Date' in filtered_hist.columns:
                st.markdown("### 📊 Service Requests Over Time")
                
                # Group by month
                monthly_requests = filtered_hist.groupby(filtered_hist['Request Date'].dt.to_period('M')).size()
                monthly_requests.index = monthly_requests.index.to_timestamp()
                
                fig_trend = px.line(
                    x=monthly_requests.index,
                    y=monthly_requests.values,
                    title="Monthly Service Requests",
                    labels={'x': 'Month', 'y': 'Number of Requests'}
                )
                fig_trend.update_traces(mode='lines+markers')
                st.plotly_chart(fig_trend, use_container_width=True)
            
            # Language trends
            if 'Language' in filtered_hist.columns and 'Request Date' in filtered_hist.columns:
                st.markdown("### 🌍 Language Request Trends")
                
                # Top languages over time
                top_languages = filtered_hist['Language'].value_counts().head(5).index
                lang_trend_data = []
                
                for lang in top_languages:
                    lang_data = filtered_hist[filtered_hist['Language'] == lang]
                    monthly = lang_data.groupby(lang_data['Request Date'].dt.to_period('M')).size()
                    monthly.index = monthly.index.to_timestamp()
                    
                    for date, count in monthly.items():
                        lang_trend_data.append({
                            'Date': date,
                            'Language': lang,
                            'Count': count
                        })
                
                if lang_trend_data:
                    lang_trend_df = pd.DataFrame(lang_trend_data)
                    
                    fig_lang_trend = px.line(
                        lang_trend_df,
                        x='Date',
                        y='Count',
                        color='Language',
                        title="Top 5 Languages - Request Trends",
                        labels={'Count': 'Number of Requests', 'Date': 'Month'}
                    )
                    st.plotly_chart(fig_lang_trend, use_container_width=True)
            
            # Linguist availability trends
            if 'Has Linguist?' in filtered_hist.columns:
                st.markdown("### 👥 Linguist Availability Trends")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Overall availability
                    availability_counts = filtered_hist['Has Linguist?'].value_counts()
                    
                    fig_avail = px.pie(
                        values=availability_counts.values,
                        names=availability_counts.index,
                        title="Overall Linguist Availability",
                        color_discrete_map={'Yes': '#2E7D32', 'No': '#D32F2F'}
                    )
                    st.plotly_chart(fig_avail, use_container_width=True)
                
                with col2:
                    # Availability by language
                    if 'Language' in filtered_hist.columns:
                        lang_avail = filtered_hist.groupby(['Language', 'Has Linguist?']).size().unstack(fill_value=0)
                        lang_avail['Total'] = lang_avail.sum(axis=1)
                        lang_avail['Availability %'] = (lang_avail.get('Yes', 0) / lang_avail['Total'] * 100).round(1)
                        
                        top_lang_avail = lang_avail.nlargest(10, 'Total')
                        
                        fig_lang_avail = px.bar(
                            x=top_lang_avail.index,
                            y=top_lang_avail['Availability %'],
                            title="Linguist Availability by Top 10 Languages",
                            labels={'x': 'Language', 'y': 'Availability %'},
                            color=top_lang_avail['Availability %'],
                            color_continuous_scale='RdYlGn'
                        )
                        fig_lang_avail.add_hline(y=50, line_dash="dash", annotation_text="50% threshold")
                        st.plotly_chart(fig_lang_avail, use_container_width=True)
            
        else:
            st.warning("No historical data available for trends analysis.")
    else:
        st.warning("Historical data file not found. Please ensure 'AllDataAnalysis_20250908_194306.xlsx' is in the same directory as the app.")
        st.info("Expected file: AllDataAnalysis_20250908_194306.xlsx")

# Tab 3: Linguist Directory
with tab3:
    st.subheader("👥 Linguist Directory")
    
    if local_data.get('linguists') is not None:
        linguists_df = local_data['linguists']
        
        # Filters for linguist directory
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Languages' in linguists_df.columns:
                unique_languages = sorted(linguists_df['Languages'].dropna().unique())
                selected_ling_language = st.selectbox(
                    "Filter by Language",
                    ["All"] + unique_languages
                )
        
        with col2:
            if 'State' in linguists_df.columns:
                unique_states = sorted(linguists_df['State'].dropna().unique())
                selected_state = st.selectbox(
                    "Filter by State",
                    ["All"] + unique_states
                )
        
        with col3:
            if 'Proficiency' in linguists_df.columns:
                unique_prof = sorted(linguists_df['Proficiency'].dropna().unique())
                selected_prof = st.selectbox(
                    "Filter by Proficiency",
                    ["All"] + unique_prof
                )
        
        # Apply filters
        filtered_linguists = linguists_df.copy()
        
        if selected_ling_language != "All":
            filtered_linguists = filtered_linguists[filtered_linguists['Languages'] == selected_ling_language]
        
        if selected_state != "All":
            filtered_linguists = filtered_linguists[filtered_linguists['State'] == selected_state]
        
        if selected_prof != "All":
            filtered_linguists = filtered_linguists[filtered_linguists['Proficiency'] == selected_prof]
        
        # Summary statistics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Linguists", len(filtered_linguists))
        
        with col2:
            if 'Languages' in filtered_linguists.columns:
                st.metric("Languages Covered", filtered_linguists['Languages'].nunique())
        
        with col3:
            if 'State' in filtered_linguists.columns:
                st.metric("States Represented", filtered_linguists['State'].nunique())
        
        with col4:
            if 'Rate' in filtered_linguists.columns:
                avg_rate = pd.to_numeric(filtered_linguists['Rate'], errors='coerce').mean()
                if not pd.isna(avg_rate):
                    st.metric("Average Rate", f"${avg_rate:.2f}")
        
        # Visualizations
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Languages Distribution")
            if 'Languages' in filtered_linguists.columns:
                lang_counts = filtered_linguists['Languages'].value_counts().head(15)
                
                fig_lang_dist = px.bar(
                    y=lang_counts.index,
                    x=lang_counts.values,
                    orientation='h',
                    title="Top 15 Languages by Linguist Count",
                    labels={'x': 'Number of Linguists', 'y': 'Language'}
                )
                st.plotly_chart(fig_lang_dist, use_container_width=True)
        
        with col2:
            st.markdown("#### Geographic Distribution")
            if 'State' in filtered_linguists.columns:
                state_counts = filtered_linguists['State'].value_counts()
                
                fig_state_dist = px.pie(
                    values=state_counts.values,
                    names=state_counts.index,
                    title="Linguists by State",
                    hole=0.4
                )
                st.plotly_chart(fig_state_dist, use_container_width=True)
        
        # Display linguist table
        st.markdown("---")
        st.markdown("### 📋 Linguist Details")
        
        # Select columns to display
        display_columns = ['Languages', 'first_name', 'last_name', 'State', 'Proficiency', 'Rate']
        display_columns = [col for col in display_columns if col in filtered_linguists.columns]
        
        st.dataframe(
            filtered_linguists[display_columns],
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        st.download_button(
            label="Download Filtered Linguist Data",
            data=filtered_linguists.to_csv(index=False),
            file_name="filtered_linguists.csv",
            mime="text/csv"
        )
        
    else:
        st.warning("Linguist directory file not found. Please ensure 'SOSiApprovedLinguists (1).xlsx' is in the same directory as the app.")
        st.info("Expected file: SOSiApprovedLinguists (1).xlsx")

# Tab 4: Data Analysis
with tab4:
    st.subheader("📋 Comprehensive Data Analysis")
    
    if local_data.get('staging') is not None:
        staging_df = local_data['staging']
        
        st.markdown("### 📊 Staging Data Analysis")
        
        # Convert date columns
        date_cols = ['Date of request', 'Hearing Date', 'Timestamp']
        for col in date_cols:
            if col in staging_df.columns:
                staging_df[col] = pd.to_datetime(staging_df[col], errors='coerce')
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", len(staging_df))
        
        with col2:
            if 'Language' in staging_df.columns:
                st.metric("Unique Languages", staging_df['Language'].nunique())
        
        with col3:
            if 'Status' in staging_df.columns:
                st.metric("Unique Statuses", staging_df['Status'].nunique())
        
        with col4:
            if 'Medium' in staging_df.columns:
                st.metric("Service Mediums", staging_df['Medium'].nunique())
        
        # Analysis visualizations
        st.markdown("---")
        
        # Status distribution
        if 'Status' in staging_df.columns:
            st.markdown("#### Status Distribution")
            status_counts = staging_df['Status'].value_counts()
            
            fig_status = px.bar(
                x=status_counts.index,
                y=status_counts.values,
                title="Service Request Status Distribution",
                labels={'x': 'Status', 'y': 'Count'},
                color=status_counts.values,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        # Medium analysis
        if 'Medium' in staging_df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                medium_counts = staging_df['Medium'].value_counts()
                
                fig_medium = px.pie(
                    values=medium_counts.values,
                    names=medium_counts.index,
                    title="Service Delivery Medium",
                    hole=0.4
                )
                st.plotly_chart(fig_medium, use_container_width=True)
            
            with col2:
                if 'Language' in staging_df.columns:
                    # Top languages by medium
                    lang_medium = staging_df.groupby(['Medium', 'Language']).size().reset_index(name='Count')
                    top_langs = staging_df['Language'].value_counts().head(5).index
                    lang_medium_filtered = lang_medium[lang_medium['Language'].isin(top_langs)]
                    
                    fig_lang_medium = px.bar(
                        lang_medium_filtered,
                        x='Medium',
                        y='Count',
                        color='Language',
                        title="Top 5 Languages by Service Medium",
                        barmode='group'
                    )
                    st.plotly_chart(fig_lang_medium, use_container_width=True)
        
        # Time analysis
        if 'Billable time' in staging_df.columns:
            st.markdown("---")
            st.markdown("#### Service Duration Analysis")
            
            # Convert billable time to numeric
            staging_df['Billable time (numeric)'] = pd.to_numeric(staging_df['Billable time'], errors='coerce')
            
            if not staging_df['Billable time (numeric)'].isna().all():
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_time_dist = px.histogram(
                        staging_df[staging_df['Billable time (numeric)'].notna()],
                        x='Billable time (numeric)',
                        nbins=30,
                        title="Distribution of Service Duration",
                        labels={'Billable time (numeric)': 'Duration (minutes)', 'count': 'Frequency'}
                    )
                    st.plotly_chart(fig_time_dist, use_container_width=True)
                
                with col2:
                    if 'Language' in staging_df.columns:
                        avg_time_by_lang = staging_df.groupby('Language')['Billable time (numeric)'].mean().sort_values(ascending=False).head(10)
                        
                        fig_avg_time = px.bar(
                            x=avg_time_by_lang.values,
                            y=avg_time_by_lang.index,
                            orientation='h',
                            title="Average Service Duration by Language (Top 10)",
                            labels={'x': 'Average Duration (minutes)', 'y': 'Language'}
                        )
                        st.plotly_chart(fig_avg_time, use_container_width=True)
    
    # Raw data display
    st.markdown("---")
    st.markdown("### 📁 Raw Data Tables")
    
    data_tabs = st.tabs(["Historical Data", "Linguist Data", "Staging Data"])
    
    with data_tabs[0]:
        if local_data.get('historical') and isinstance(local_data['historical'], dict):
            for sheet_name, sheet_data in local_data['historical'].items():
                st.write(f"Sheet: {sheet_name}")
                st.dataframe(sheet_data, use_container_width=True)
                st.download_button(
                    label=f"Download {sheet_name}",
                    data=sheet_data.to_csv(index=False),
                    file_name=f"historical_{sheet_name.replace(' ', '_')}.csv",
                    mime="text/csv"
                )
    
    with data_tabs[1]:
        if local_data.get('linguists') is not None:
            st.dataframe(local_data['linguists'], use_container_width=True)
            st.download_button(
                label="Download Linguist Data",
                data=local_data['linguists'].to_csv(index=False),
                file_name="linguist_data.csv",
                mime="text/csv"
            )
    
    with data_tabs[2]:
        if local_data.get('staging') is not None:
            st.dataframe(local_data['staging'], use_container_width=True)
            st.download_button(
                label="Download Staging Data",
                data=local_data['staging'].to_csv(index=False),
                file_name="staging_data.csv",
                mime="text/csv"
            )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>SOSI Language Services Dashboard</strong> | 
    Data Sources: Historical Analysis & Linguist Directory | 
    Last Updated: {}</p>
    <p>This dashboard provides comprehensive analysis of language services, interpreter management, and service delivery metrics.</p>
</div>
""".format(datetime.now().strftime("%B %d, %Y")), unsafe_allow_html=True)