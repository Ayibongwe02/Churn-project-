import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="CHURN SIGNAL - Telco Cohort", layout="wide")
st.title("🚨 CHURN SIGNAL · TELCO COHORT")

# Load data
@st.cache_data
def load_data():
    # Load from relative paths inside the project
    customers = pd.read_csv("attachments/churn_customers.csv")
    predictions = pd.read_csv("attachments/churn_predictions.csv")
    return customers, predictions

customers_df, predictions_df = load_data()

# Merge data
merged_df = customers_df.merge(predictions_df, on='customerID', how='left')

# Create SQLite DB
conn = sqlite3.connect(':memory:')
merged_df.to_sql('customer_churn_predictions', conn, index=False, if_exists='replace')

# Load SQL queries
with open("attachments/churn_queries.sql", "r") as f:
    sql_content = f.read()

# Sidebar
st.sidebar.header("Dashboard Controls")
view = st.sidebar.selectbox("Select View", ["Overview", "High Risk Leaderboard", "Segment Analysis", "SQL Queries"])

# Overview
if view == "Overview":
    st.header("Risk Distribution")
    risk_counts = merged_df['risk_band'].value_counts()
    fig = px.pie(names=risk_counts.index, values=risk_counts.values, title="Risk Distribution")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Customers", len(merged_df))
        st.metric("High Risk (At Risk + Urgent)", len(merged_df[merged_df['risk_band'].isin(['At Risk', 'Urgent'])]))
    with col2:
        st.metric("Avg Risk Score", f"{merged_df['risk_score'].mean():.1%}")
        st.metric("Avg Monthly Revenue", f"${merged_df['MonthlyCharges'].mean():.2f}")

# Leaderboard
elif view == "High Risk Leaderboard":
    st.header("High-risk Leaderboard")
    top_risk = merged_df.nlargest(20, 'risk_score')[['customerID', 'risk_score', 'risk_band', 'tenure', 'Contract', 'MonthlyCharges']]
    top_risk = top_risk.rename(columns={
        'risk_score': 'Churn Risk',
        'risk_band': 'Risk Band',
        'MonthlyCharges': 'Monthly Charges ($)'
    })
    st.dataframe(top_risk.style.format({'Churn Risk': '{:.1%}'}), use_container_width=True)

# Segment Analysis
elif view == "Segment Analysis":
    st.header("Churn Rate by Segment")
    
    # By Contract
    contract_query = """
    SELECT Contract, COUNT(*) as customers, 
           ROUND(AVG(CASE WHEN risk_score >= 0.5 THEN 1.0 ELSE 0.0 END), 3) as predicted_churn_rate
    FROM customer_churn_predictions 
    GROUP BY Contract
    """
    contract_df = pd.read_sql(contract_query, conn)
    contract_df = contract_df.rename(columns={
        'predicted_churn_rate': 'Predicted Churn Rate (%)',
        'customers': 'Number of Customers'
    })
    st.subheader("By Contract Type")
    st.dataframe(contract_df.style.format({'Predicted Churn Rate (%)': '{:.1%}'}), use_container_width=True)

    # By Internet
    internet_query = """
    SELECT InternetService, COUNT(*) as customers, 
           ROUND(AVG(CASE WHEN risk_score >= 0.5 THEN 1.0 ELSE 0.0 END), 3) as predicted_churn_rate
    FROM customer_churn_predictions 
    GROUP BY InternetService
    """
    internet_df = pd.read_sql(internet_query, conn)
    internet_df = internet_df.rename(columns={
        'predicted_churn_rate': 'Predicted Churn Rate (%)',
        'customers': 'Number of Customers'
    })
    st.subheader("By Internet Service")
    st.dataframe(internet_df.style.format({'Predicted Churn Rate (%)': '{:.1%}'}), use_container_width=True)

# SQL Queries
elif view == "SQL Queries":
    st.header("Available SQL Queries")
    st.code(sql_content, language="sql")
    
    query_name = st.selectbox("Run Query", ["top_20_highest_risk", "churn_rate_by_contract", "revenue_at_risk_by_band"])
    
    if st.button("Execute Query"):
        if query_name == "top_20_highest_risk":
            query = "SELECT customerID, tenure, Contract, MonthlyCharges, ROUND(risk_score, 3) AS risk_score FROM customer_churn_predictions ORDER BY risk_score DESC LIMIT 20"
        elif query_name == "churn_rate_by_contract":
            query = sql_content.split("-- churn_rate_by_contract")[1].split(";")[0].strip() if "-- churn_rate_by_contract" in sql_content else ""
        else:
            query = "SELECT risk_band, COUNT(*) AS customers, ROUND(SUM(MonthlyCharges), 2) AS monthly_revenue_at_risk FROM customer_churn_predictions GROUP BY risk_band"
        
        result = pd.read_sql(query, conn)
        st.dataframe(result)

st.caption("Synthetic Telco-style data • Built with Streamlit + SQLite")
