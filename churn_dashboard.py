import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="CHURN SIGNAL - Telco Cohort", layout="wide")
st.title("CHURN SIGNAL · TELCO COHORT")

# Load data
@st.cache_data

def load_data():
    # Load from relative paths inside the project
    customers = pd.read_csv("/workspaces/Churn-project-/churn_customers.csv")
    predictions = pd.read_csv("/workspaces/Churn-project-/churn_predictions.csv")
    return customers, predictions

customers_df, predictions_df = load_data()

# Merge data
merged_df = customers_df.merge(predictions_df, on='customerID', how='left')

# Create SQLite DB
conn = sqlite3.connect(':memory:')
merged_df.to_sql('customer_churn_predictions', conn, index=False, if_exists='replace')

# Load SQL queries
with open("/workspaces/Churn-project-/churn_queries.sql", "r") as f:
    sql_content = f.read()

# Sidebar
st.sidebar.header("Dashboard Controls")
view = st.sidebar.selectbox("Select View", ["Overview", "High Risk Leaderboard", "Segment Analysis", "SQL Queries"])

# Overview
if view == "Overview":
    st.header("Risk Distribution Across Cohort")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Customers", f"{len(merged_df):,}")
    with col2:
        high_risk = len(merged_df[merged_df['risk_band'].isin(['At Risk', 'Urgent'])])
        st.metric("High Risk Customers", high_risk)
    with col3:
        st.metric("Average Risk Score", f"{merged_df['risk_score'].mean():.1%}")

    # Risk Distribution Pie Chart
    risk_counts = merged_df['risk_band'].value_counts()
    fig = px.pie(names=risk_counts.index, values=risk_counts.values, 
                 title="Risk Distribution", color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig, use_container_width=True)

# Leaderboard
elif view == "High Risk Leaderboard":
    st.header("High-Risk Leaderboard")
    st.caption("Ranked by predicted churn risk")
    
    top_risk = merged_df.nlargest(20, 'risk_score')[
        ['customerID', 'risk_score', 'risk_band', 'tenure', 'Contract', 'MonthlyCharges']
    ].copy()
    
    top_risk['Churn Risk'] = top_risk['risk_score'].apply(lambda x: f"{x:.1%}")
    top_risk['Monthly Charges'] = top_risk['MonthlyCharges'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(top_risk[['customerID', 'Churn Risk', 'risk_band', 'tenure', 'Contract', 'Monthly Charges']], 
                 use_container_width=True, hide_index=True)

# Segment Analysis
elif view == "Segment Analysis":
    st.header("📈 Churn Rate by Segment")
    
    # By Contract
    contract_df = pd.read_sql("""
        SELECT Contract, 
               COUNT(*) as customers, 
               ROUND(AVG(CASE WHEN risk_score >= 0.5 THEN 1.0 ELSE 0.0 END), 3) as "Predicted Churn Rate",
               ROUND(AVG(MonthlyCharges), 2) as "Avg Monthly Charges"
        FROM customer_churn_predictions 
        GROUP BY Contract
        ORDER BY "Predicted Churn Rate" DESC
    """, conn)
    st.subheader("By Contract Type")
    st.dataframe(contract_df, use_container_width=True)
    
    # By Internet Service
    internet_df = pd.read_sql("""
        SELECT InternetService, 
               COUNT(*) as customers, 
               ROUND(AVG(CASE WHEN risk_score >= 0.5 THEN 1.0 ELSE 0.0 END), 3) as "Predicted Churn Rate"
        FROM customer_churn_predictions 
        GROUP BY InternetService
        ORDER BY "Predicted Churn Rate" DESC
    """, conn)
    st.subheader("By Internet Service")
    st.dataframe(internet_df, use_container_width=True)



# SQL Queries
elif view == "SQL Queries":
    st.header("SQL Queries")
    st.code(sql_content, language="sql")

st.caption("Synthetic Telco data • Built with Streamlit + SQLite")

