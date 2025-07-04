import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="NYC Language Access Services Dashboard",
    page_icon="🗽",
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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_lass_data():
    """Load LASS Ratings Dataset with error handling"""
    try:
        lass_url = "https://data.cityofnewyork.us/api/views/3m3d-zzwn/rows.csv?accessType=DOWNLOAD"
        lass_df = pd.read_csv(lass_url)
        return lass_df, None
    except Exception as e:
        return None, f"Error loading LASS data: {str(e)}"

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_lep_data():
    """Load LEP Population Dataset with error handling"""
    try:
        lep_url = "https://data.cityofnewyork.us/api/views/ajin-gkbp/rows.csv?accessType=DOWNLOAD"
        lep_df = pd.read_csv(lep_url)
        return lep_df, None
    except Exception as e:
        return None, f"Error loading LEP data: {str(e)}"

def clean_lass_data(df):
    """Clean and prepare LASS data"""
    if df is None:
        return None
    
    # Make a copy to avoid modifying cached data
    df = df.copy()
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Handle missing values
    df = df.fillna('Unknown')
    
    # Create a rating score based on service quality indicators
    # Convert 'Yes'/'No' responses to numeric scores
    service_columns = [
        'Interaction with Security Guards',
        'Interaction with Reception Staff', 
        'Interaction with Frontline Staff',
        'Does Facility have signs posted notifying clients \nto the right of interpretation services?',
        'Did the Secret Shopper receive the informat\nion or service asked for?'
    ]
    
    # Create a simple rating score (1-5 scale)
    df['rating_score'] = 3  # Default score
    
    for col in service_columns:
        if col in df.columns:
            # Add points for positive interactions
            df.loc[df[col].str.contains('Yes|Good|Excellent', case=False, na=False), 'rating_score'] += 0.5
            # Subtract points for negative interactions
            df.loc[df[col].str.contains('No|Poor|Bad', case=False, na=False), 'rating_score'] -= 0.5
    
    # Cap the rating between 1 and 5
    df['rating_score'] = df['rating_score'].clip(1, 5)
    
    return df

def clean_lep_data(df):
    """Clean and prepare LEP data"""
    if df is None:
        return None
    
    # Make a copy to avoid modifying cached data
    df = df.copy()
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Handle missing values
    df = df.fillna('Unknown')
    
    # Convert LEP population to numeric
    if 'LEP Population (Estimate)' in df.columns:
        df['LEP Population (Estimate)'] = pd.to_numeric(df['LEP Population (Estimate)'], errors='coerce')
    
    return df

# Load data
with st.spinner("Loading NYC Language Access Services data..."):
    lass_df, lass_error = load_lass_data()
    lep_df, lep_error = load_lep_data()

# Check for data loading errors
if lass_error:
    st.error(lass_error)
    st.stop()

if lep_error:
    st.error(lep_error)
    st.stop()

# Clean data
lass_df = clean_lass_data(lass_df)
lep_df = clean_lep_data(lep_df)

# Main header
st.markdown('<h1 class="main-header">🗽 NYC Language Access Services Dashboard</h1>', unsafe_allow_html=True)
st.markdown("### Ensuring Equal Access to City Services for All New Yorkers")

# Sidebar filters
st.sidebar.title("🔍 Dashboard Filters")
st.sidebar.markdown("---")

# Agency filter
if lass_df is not None and 'Agency' in lass_df.columns:
    agencies = sorted(lass_df['Agency'].unique())
    selected_agencies = st.sidebar.multiselect(
        "Select Agencies",
        agencies,
        default=agencies[:5] if len(agencies) > 5 else agencies
    )
else:
    selected_agencies = []

# Borough filter
if lass_df is not None and 'Borough' in lass_df.columns:
    boroughs = sorted(lass_df['Borough'].unique())
    selected_boroughs = st.sidebar.multiselect(
        "Select Boroughs",
        boroughs,
        default=boroughs
    )
else:
    selected_boroughs = []

# Language filter
if lass_df is not None and 'Secret Shopper Language' in lass_df.columns:
    languages = sorted(lass_df['Secret Shopper Language'].unique())
    selected_languages = st.sidebar.multiselect(
        "Select Languages",
        languages,
        default=languages[:5] if len(languages) > 5 else languages
    )
else:
    selected_languages = []

# Filter data based on selections
if lass_df is not None:
    filtered_lass = lass_df.copy()
    
    if selected_agencies:
        filtered_lass = filtered_lass[filtered_lass['Agency'].isin(selected_agencies)]
    
    if selected_boroughs:
        filtered_lass = filtered_lass[filtered_lass['Borough'].isin(selected_boroughs)]
    
    if selected_languages:
        filtered_lass = filtered_lass[filtered_lass['Secret Shopper Language'].isin(selected_languages)]
else:
    filtered_lass = pd.DataFrame()

# Key Metrics Row
st.markdown("---")
st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if not filtered_lass.empty:
        total_agencies = filtered_lass['Agency'].nunique()
        st.metric(
            label="Total Agencies",
            value=total_agencies,
            help="Number of agencies providing language access services"
        )
    else:
        st.metric(label="Total Agencies", value="N/A")

with col2:
    if not filtered_lass.empty:
        total_languages = filtered_lass['Secret Shopper Language'].nunique()
        st.metric(
            label="Languages Supported",
            value=total_languages,
            help="Number of different languages supported across agencies"
        )
    else:
        st.metric(label="Languages Supported", value="N/A")

with col3:
    if not filtered_lass.empty and 'rating_score' in filtered_lass.columns:
        avg_rating = filtered_lass['rating_score'].mean()
        st.metric(
            label="Average Rating",
            value=f"{avg_rating:.1f}" if not pd.isna(avg_rating) else "N/A",
            help="Average rating across all language access services"
        )
    else:
        st.metric(label="Average Rating", value="N/A")

with col4:
    if not filtered_lass.empty:
        total_services = len(filtered_lass)
        st.metric(
            label="Total Services",
            value=total_services,
            help="Total number of language access services provided"
        )
    else:
        st.metric(label="Total Services", value="N/A")

# Visualizations
st.markdown("---")
st.subheader("📈 Language Access Services Analysis")

# Row 1: Agency Performance and Language Distribution
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🏢 Agency Performance")
    if not filtered_lass.empty and 'Agency' in filtered_lass.columns:
        agency_counts = filtered_lass['Agency'].value_counts().head(10)
        
        fig_agency = px.bar(
            x=agency_counts.values,
            y=agency_counts.index,
            orientation='h',
            title="Top 10 Agencies by Service Count",
            labels={'x': 'Number of Services', 'y': 'Agency'},
            color=agency_counts.values,
            color_continuous_scale='Blues'
        )
        fig_agency.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_agency, use_container_width=True)
        
        st.info("💡 **Insight**: This shows which agencies provide the most language access services.")
    else:
        st.warning("Agency data not available for visualization.")

with col2:
    st.markdown("#### 🌍 Language Distribution")
    if not filtered_lass.empty and 'Secret Shopper Language' in filtered_lass.columns:
        language_counts = filtered_lass['Secret Shopper Language'].value_counts().head(10)
        
        fig_language = px.pie(
            values=language_counts.values,
            names=language_counts.index,
            title="Top 10 Languages by Service Availability",
            hole=0.4
        )
        fig_language.update_layout(height=400)
        st.plotly_chart(fig_language, use_container_width=True)
        
        st.info("💡 **Insight**: This shows which languages are most commonly supported across agencies.")
    else:
        st.warning("Language data not available for visualization.")

# Row 2: Borough Analysis and Rating Distribution
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🗽 Borough Coverage")
    if not filtered_lass.empty and 'Borough' in filtered_lass.columns:
        borough_counts = filtered_lass['Borough'].value_counts()
        
        fig_borough = px.bar(
            x=borough_counts.index,
            y=borough_counts.values,
            title="Language Access Services by Borough",
            labels={'x': 'Borough', 'y': 'Number of Services'},
            color=borough_counts.values,
            color_continuous_scale='Greens'
        )
        fig_borough.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_borough, use_container_width=True)
        
        st.info("💡 **Insight**: This shows how language access services are distributed across NYC boroughs.")
    else:
        st.warning("Borough data not available for visualization.")

with col2:
    st.markdown("#### ⭐ Service Ratings")
    if not filtered_lass.empty and 'rating_score' in filtered_lass.columns:
        fig_rating = px.histogram(
            x=filtered_lass['rating_score'],
            title="Distribution of Service Ratings",
            labels={'x': 'Rating Score', 'y': 'Count'},
            nbins=10
        )
        fig_rating.update_layout(height=400)
        st.plotly_chart(fig_rating, use_container_width=True)
        
        st.info("💡 **Insight**: This shows the distribution of service quality ratings (1-5 scale).")
    else:
        st.warning("Rating data not available for visualization.")

# Row 3: LEP Population Analysis (if data is available)
if lep_df is not None and not lep_df.empty:
    st.markdown("---")
    st.subheader("👥 Limited English Proficiency (LEP) Population Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 LEP Population by Borough")
        if 'Borough' in lep_df.columns and 'LEP Population (Estimate)' in lep_df.columns:
            lep_borough = lep_df.groupby('Borough')['LEP Population (Estimate)'].sum().reset_index()
            
            fig_lep = px.bar(
                lep_borough,
                x='Borough',
                y='LEP Population (Estimate)',
                title="LEP Population by Borough",
                labels={'LEP Population (Estimate)': 'LEP Population', 'Borough': 'Borough'},
                color='LEP Population (Estimate)',
                color_continuous_scale='Reds'
            )
            fig_lep.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_lep, use_container_width=True)
        else:
            st.warning("LEP population data not available for visualization.")
    
    with col2:
        st.markdown("#### 🌍 Top Languages by LEP Population")
        if 'Language' in lep_df.columns and 'LEP Population (Estimate)' in lep_df.columns:
            lep_language = lep_df.groupby('Language')['LEP Population (Estimate)'].sum().sort_values(ascending=False).head(10)
            
            fig_lep_lang = px.bar(
                x=lep_language.values,
                y=lep_language.index,
                orientation='h',
                title="Top 10 Languages by LEP Population",
                labels={'x': 'LEP Population', 'y': 'Language'},
                color=lep_language.values,
                color_continuous_scale='Purples'
            )
            fig_lep_lang.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_lep_lang, use_container_width=True)
        else:
            st.warning("LEP language data not available for visualization.")

# Data Tables
st.markdown("---")
st.subheader("📋 Raw Data")

tab1, tab2 = st.tabs(["LASS Data", "LEP Data"])

with tab1:
    if not filtered_lass.empty:
        st.dataframe(filtered_lass, use_container_width=True)
        st.download_button(
            label="Download LASS Data as CSV",
            data=filtered_lass.to_csv(index=False),
            file_name="nyc_lass_data.csv",
            mime="text/csv"
        )
    else:
        st.warning("No LASS data available to display.")

with tab2:
    if lep_df is not None and not lep_df.empty:
        st.dataframe(lep_df, use_container_width=True)
        st.download_button(
            label="Download LEP Data as CSV",
            data=lep_df.to_csv(index=False),
            file_name="nyc_lep_data.csv",
            mime="text/csv"
        )
    else:
        st.warning("No LEP data available to display.")

# Insights and Recommendations
st.markdown("---")
st.subheader("💡 Key Insights & Recommendations")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 🎯 **Key Findings:**
    
    **Service Distribution:**
    - Agencies vary significantly in their language access service offerings
    - Some boroughs may have better coverage than others
    - Certain languages are more commonly supported than others
    
    **Quality Assessment:**
    - Service ratings help identify areas for improvement
    - High-performing agencies can serve as models for others
    - Regular monitoring of service quality is essential
    """)

with col2:
    st.markdown("""
    #### 🚀 **Recommendations:**
    
    **Immediate Actions:**
    - Expand services in underserved boroughs
    - Increase support for less commonly offered languages
    - Implement best practices from high-performing agencies
    
    **Long-term Strategy:**
    - Develop comprehensive language access plans
    - Invest in staff training and resources
    - Establish regular quality assessment protocols
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>NYC Language Access Services Dashboard</strong> | 
    Data Source: NYC Open Data | 
    Last Updated: {}</p>
    <p>This dashboard helps ensure equal access to city services for all New Yorkers, regardless of language proficiency.</p>
</div>
""".format(datetime.now().strftime("%B %d, %Y")), unsafe_allow_html=True) 