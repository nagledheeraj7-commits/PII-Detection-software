#!/usr/bin/env python3
"""
Premium PII Detection Analytics Dashboard - SaaS Style
"""

import streamlit as st
import pandas as pd
import re
from io import StringIO

def detect_emails(text):
    """Detect email addresses using regex"""
    if pd.isna(text):
        return 0
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    return len(re.findall(email_pattern, str(text)))

def detect_phones(text):
    """Detect phone numbers (10 digits, with spaces or dashes)"""
    if pd.isna(text):
        return 0
    # Pattern for 10-digit numbers with optional spaces/dashes
    phone_patterns = [
        r'\b\d{10}\b',  # 10 digits
        r'\b\d{3}[-\s]\d{3}[-\s]\d{4}\b',  # 123-456-7890 or 123 456 7890
        r'\b\d{3}[-\s]\d{7}\b',  # 123-4567890
        r'\b\d{7}[-\s]\d{3}\b'  # 4567890-123
    ]
    total = 0
    for pattern in phone_patterns:
        total += len(re.findall(pattern, str(text)))
    return total

def detect_names(text):
    """Detect names (alphabets and spaces only, length > 3)"""
    if pd.isna(text):
        return 0
    text_str = str(text).strip()
    # Check if contains only alphabets and spaces, and length > 3
    if len(text_str) > 3 and re.match(r'^[a-zA-Z\s]+$', text_str):
        # Additional check: at least 2 words, each starting with capital letter
        words = text_str.split()
        if len(words) >= 2 and all(word.istitle() for word in words if word.strip()):
            return 1
    return 0

def analyze_column_pii(column_data):
    """Analyze a column for PII types"""
    emails = 0
    phones = 0
    names = 0
    
    for value in column_data:
        emails += detect_emails(value)
        phones += detect_phones(value)
        names += detect_names(value)
    
    # Determine column type
    if emails > 0:
        column_type = "Email"
    elif phones > 0:
        column_type = "Phone"
    elif names > 0:
        column_type = "Name"
    else:
        column_type = "Non-PII"
    
    return {
        'type': column_type,
        'emails': emails,
        'phones': phones,
        'names': names,
        'total_pii': emails + phones + names
    }

def analyze_pii(df):
    """Analyze DataFrame for PII (limited to first 1000 rows for performance)"""
    # Limit to first 1000 rows for performance
    df_limited = df.head(1000)
    
    results = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'analyzed_rows': len(df_limited),
        'total_emails': 0,
        'total_phones': 0,
        'total_names': 0,
        'total_pii_found': 0,
        'column_analysis': {}
    }
    
    for column in df_limited.columns:
        column_result = analyze_column_pii(df_limited[column])
        results['column_analysis'][column] = column_result
        results['total_emails'] += column_result['emails']
        results['total_phones'] += column_result['phones']
        results['total_names'] += column_result['names']
        results['total_pii_found'] += column_result['total_pii']
    
    return results

def create_kpi_cards(results):
    """Create KPI cards for metrics display"""
    # Calculate detection percentage
    total_cells = results['analyzed_rows'] * results['total_columns']
    detection_percentage = (results['total_pii_found'] / total_cells * 100) if total_cells > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #3b82f6; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="color: #64748b; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;">📄 Rows</div>
            <div style="color: #1e293b; font-size: 1.875rem; font-weight: 700;">{}</div>
        </div>
        """.format(results['analyzed_rows']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #10b981; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="color: #64748b; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;">📋 Columns</div>
            <div style="color: #1e293b; font-size: 1.875rem; font-weight: 700;">{}</div>
        </div>
        """.format(results['total_columns']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #f59e0b; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="color: #64748b; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;">🔍 Total PII</div>
            <div style="color: #1e293b; font-size: 1.875rem; font-weight: 700;">{}</div>
        </div>
        """.format(results['total_pii_found']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ef4444; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="color: #64748b; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;">📊 Detection %</div>
            <div style="color: #1e293b; font-size: 1.875rem; font-weight: 700;">{:.1f}%</div>
        </div>
        """.format(detection_percentage), unsafe_allow_html=True)

def create_charts(results):
    """Create charts for PII analysis results"""
    
    # Data for charts
    pii_types = ['Email', 'Phone', 'Name']
    pii_counts = [results['total_emails'], results['total_phones'], results['total_names']]
    
    # Create bar chart
    st.markdown("### PII Distribution by Type")
    bar_chart_data = pd.DataFrame({
        'PII Type': pii_types,
        'Count': pii_counts
    })
    st.bar_chart(bar_chart_data.set_index('PII Type'), color='#3b82f6')
    
    # Create percentage breakdown chart
    st.markdown("### PII Percentage Breakdown")
    if results['total_pii_found'] > 0:
        percentage_data = pd.DataFrame({
            'PII Type': pii_types,
            'Percentage': [count / results['total_pii_found'] * 100 for count in pii_counts]
        })
        st.bar_chart(percentage_data.set_index('PII Type'), color='#10b981')
    else:
        st.info("No PII data available for percentage breakdown")

def export_results(results):
    """Export results as CSV"""
    # Prepare export data
    export_data = []
    for col_name, col_analysis in results['column_analysis'].items():
        export_data.append({
            'Column': col_name,
            'PII Type': col_analysis['type'],
            'Count': col_analysis['total_pii']
        })
    
    # Create DataFrame
    export_df = pd.DataFrame(export_data)
    
    # Convert to CSV
    csv = export_df.to_csv(index=False)
    
    # Provide download button
    st.download_button(
        label="📥 Download Report",
        data=csv,
        file_name="pii_analysis_report.csv",
        mime="text/csv"
    )

def main():
    """Main Streamlit application"""
    # Header Design
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 2.5rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem;">🔐 PII Detection Dashboard</h1>
        <p style="font-size: 1.125rem; color: #64748b; margin: 0;">Analyze sensitive data from CSV files</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Divider
    st.markdown('<div style="height: 1px; background: #e2e8f0; margin: 2rem 0;"></div>', unsafe_allow_html=True)
    
    # Upload Section
    st.markdown("### 📁 Upload Section")
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Read CSV file
            df = pd.read_csv(uploaded_file)
            
            st.markdown("---")
            
            # Data Preview Section
            st.markdown("### 📊 Data Preview")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            
            st.dataframe(df.head(5), width='stretch')
            
            st.markdown("---")
            
            # Analysis Section
            st.markdown("### 🚀 Analysis")
            
            if st.button("Analyze PII", type="primary", use_container_width=True):
                with st.spinner("🔍 Analyzing PII data..."):
                    results = analyze_pii(df)
                
                st.markdown("---")
                
                # Results Dashboard Section
                st.markdown("### 📈 Results Dashboard")
                
                # KPI Cards
                create_kpi_cards(results)
                
                st.markdown("---")
                
                # Charts
                create_charts(results)
                
                st.markdown("---")
                
                # Column-wise analysis table
                st.markdown("### Column-wise PII Detection")
                
                # Prepare table data with clean column names
                table_data = []
                for col_name, col_analysis in results['column_analysis'].items():
                    table_data.append({
                        'Column': col_name,
                        'PII Type': col_analysis['type'],
                        'Count': col_analysis['total_pii']
                    })
                
                # Create DataFrame for table
                results_df = pd.DataFrame(table_data)
                st.dataframe(results_df, width='stretch')
                
                st.markdown("---")
                
                # Export section
                st.markdown("### 💾 Export Results")
                export_results(results)
                
                st.markdown("---")
                
                # Detailed column breakdown
                st.markdown("### 🔍 Detailed Column Analysis")
                
                for col_name, col_analysis in results['column_analysis'].items():
                    if col_analysis['total_pii'] > 0:
                        with st.expander(f"📊 {col_name} ({col_analysis['type']})"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Emails", col_analysis['emails'])
                            with col2:
                                st.metric("Phones", col_analysis['phones'])
                            with col3:
                                st.metric("Names", col_analysis['names'])
                            st.write(f"**Total PII:** {col_analysis['total_pii']}")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
    
    else:
        # Empty State
        st.markdown("""
        <div style="text-align: center; padding: 3rem 0; background: #f8fafc; border-radius: 8px; border: 2px dashed #cbd5e1;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📁</div>
            <div style="font-size: 1.125rem; color: #475569; font-weight: 500;">Upload a CSV file to start analysis</div>
            <div style="font-size: 0.875rem; color: #64748b; margin-top: 0.5rem;">Supported format: CSV files with text data</div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
