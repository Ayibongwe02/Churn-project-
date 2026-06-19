-- Customer Churn Prediction Dashboard -- SQL layer
-- Schema: customer_churn_predictions(customerID, tenure, Contract,
--   InternetService, PaymentMethod, MonthlyCharges, TotalCharges,
--   SeniorCitizen, risk_score, risk_band)

-- top_20_highest_risk
SELECT TOP 20 customerID, tenure, Contract, MonthlyCharges, ROUND(risk_score, 3) AS risk_score
        FROM customer_churn_predictions
        ORDER BY risk_score DESC;

-- churn_rate_by_contract
SELECT Contract,
               COUNT(*) AS customers,
               ROUND(AVG(CASE WHEN risk_score >= 0.5 THEN 1.0 ELSE 0.0 END), 3) AS predicted_churn_rate,
               ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges
        FROM customer_churn_predictions
        GROUP BY Contract
        ORDER BY predicted_churn_rate DESC;

-- revenue_at_risk_by_band
SELECT risk_band,
               COUNT(*) AS customers,
               ROUND(SUM(MonthlyCharges), 2) AS monthly_revenue_at_risk
        FROM customer_churn_predictions
        GROUP BY risk_band;

-- new_customers_at_risk
SELECT COUNT(*) AS new_customers_high_risk
        FROM customer_churn_predictions
        WHERE tenure < 6 AND risk_score >= 0.6;

-- churn_rate_by_internet
SELECT InternetService,
               COUNT(*) AS customers,
               ROUND(AVG(CASE WHEN risk_score >= 0.5 THEN 1.0 ELSE 0.0 END), 3) AS predicted_churn_rate
        FROM customer_churn_predictions
        GROUP BY InternetService
        ORDER BY predicted_churn_rate DESC;
