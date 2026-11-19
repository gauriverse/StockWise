-- Q1. Top 10 products by net revenue in FY 2025-26
SELECT sku_name, category,
       SUM(qty) AS units,
       ROUND(SUM(net_revenue)) AS net_revenue_inr,
       ROUND(100.0 * SUM(net_revenue) / (SELECT SUM(net_revenue) FROM sales_enriched WHERE fy = '2025-26'), 2) AS pct_of_total
FROM sales_enriched
WHERE fy = '2025-26'
GROUP BY product_id, sku_name, category
ORDER BY net_revenue_inr DESC
LIMIT 10;

-- Q2. Category performance (both years)
SELECT category,
       ROUND(SUM(net_revenue)) AS net_revenue_inr,
       ROUND(SUM(gross_profit)) AS gross_profit_inr,
       ROUND(100.0 * SUM(gross_profit) / SUM(net_revenue), 1) AS margin_pct
FROM sales_enriched
GROUP BY category
ORDER BY net_revenue_inr DESC;

-- Q3. Monthly net revenue with month-over-month growth
WITH monthly AS (
    SELECT strftime('%Y-%m', sale_date) AS month,
           ROUND(SUM(net_revenue)) AS net_revenue_inr
    FROM sales_enriched
    GROUP BY month
)
SELECT month, net_revenue_inr,
       LAG(net_revenue_inr) OVER (ORDER BY month) AS prev_month_inr,
       ROUND(100.0 * (net_revenue_inr - LAG(net_revenue_inr) OVER (ORDER BY month))
             / LAG(net_revenue_inr) OVER (ORDER BY month), 1) AS mom_pct
FROM monthly
ORDER BY month;

-- Q4. Stock at or below reorder level (current rule of thumb)
SELECT st.city, p.sku_name, i.stock_on_hand, i.reorder_level
FROM inventory i
JOIN products p ON p.product_id = i.product_id
JOIN stores st  ON st.store_id  = i.store_id
WHERE i.stock_on_hand <= i.reorder_level
ORDER BY i.stock_on_hand, st.city
LIMIT 15;

-- Q5. Will run out BEFORE the supplier can deliver (days of stock left vs lead time)
WITH recent AS (
    SELECT store_id, product_id, SUM(qty) / 90.0 AS avg_daily_sales
    FROM sales
    WHERE sale_date >= '2026-01-01'
    GROUP BY store_id, product_id
)
SELECT st.city, p.sku_name, i.stock_on_hand,
       ROUND(r.avg_daily_sales, 2) AS avg_daily_sales,
       ROUND(i.stock_on_hand / r.avg_daily_sales, 1) AS days_left,
       su.avg_lead_time_days AS lead_time_days
FROM inventory i
JOIN recent r     ON r.store_id = i.store_id AND r.product_id = i.product_id
JOIN products p   ON p.product_id = i.product_id
JOIN suppliers su ON su.supplier_id = p.supplier_id
JOIN stores st    ON st.store_id = i.store_id
WHERE i.stock_on_hand / r.avg_daily_sales < su.avg_lead_time_days
ORDER BY days_left, st.city
LIMIT 15;

-- Q6. Stock-out summary
SELECT SUM(stock_on_hand = 0) AS zero_stock_rows,
       SUM(stock_on_hand > 0 AND stock_on_hand <= reorder_level) AS low_stock_rows,
       COUNT(*) AS total_rows
FROM inventory;

-- Q7. In stock but will run out before delivery (zero-stock rows excluded)
WITH recent AS (
    SELECT store_id, product_id, SUM(qty) / 90.0 AS avg_daily_sales
    FROM sales
    WHERE sale_date >= '2026-01-01'
    GROUP BY store_id, product_id
)
SELECT st.city, p.sku_name, i.stock_on_hand,
       ROUND(i.stock_on_hand / r.avg_daily_sales, 1) AS days_left,
       su.avg_lead_time_days AS lead_time_days
FROM inventory i
JOIN recent r     ON r.store_id = i.store_id AND r.product_id = i.product_id
JOIN products p   ON p.product_id = i.product_id
JOIN suppliers su ON su.supplier_id = p.supplier_id
JOIN stores st    ON st.store_id = i.store_id
WHERE i.stock_on_hand > 0
  AND i.stock_on_hand / r.avg_daily_sales < su.avg_lead_time_days
ORDER BY su.avg_lead_time_days - i.stock_on_hand / r.avg_daily_sales DESC
LIMIT 15;