-- 1. Row counts per table
SELECT 'suppliers' AS tbl, COUNT(*) AS n FROM suppliers
UNION ALL SELECT 'stores', COUNT(*) FROM stores
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'sales', COUNT(*) FROM sales
UNION ALL SELECT 'inventory', COUNT(*) FROM inventory;

-- 2. Date range and total GST-inclusive sales
SELECT MIN(sale_date) AS first_day, MAX(sale_date) AS last_day,
       ROUND(SUM(gross_sales)) AS total_gross_sales_inr,
       ROUND(SUM(net_revenue)) AS total_net_revenue_inr,
       ROUND(SUM(gross_profit)) AS total_gross_profit_inr
FROM sales_enriched;

-- 3. Revenue by financial year
SELECT fy, COUNT(*) AS lines, ROUND(SUM(net_revenue)) AS net_revenue_inr
FROM sales_enriched GROUP BY fy ORDER BY fy;

-- 4. Rows per store
SELECT store_id, COUNT(*) AS lines FROM sales GROUP BY store_id ORDER BY store_id;

-- 5. Dead stock check: sold Oct-Dec 2025 but never after 31 Dec 2025
SELECT p.product_id, p.sku_name
FROM products p
WHERE EXISTS (SELECT 1 FROM sales s WHERE s.product_id = p.product_id
              AND s.sale_date BETWEEN '2025-10-01' AND '2025-12-31')
  AND NOT EXISTS (SELECT 1 FROM sales s WHERE s.product_id = p.product_id
                  AND s.sale_date > '2025-12-31')
ORDER BY p.product_id;