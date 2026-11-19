CREATE TABLE suppliers (
    supplier_id        TEXT PRIMARY KEY,
    supplier_name      TEXT NOT NULL,
    city               TEXT,
    state              TEXT,
    avg_lead_time_days INTEGER NOT NULL CHECK (avg_lead_time_days > 0)
);

CREATE TABLE stores (
    store_id   TEXT PRIMARY KEY,
    store_name TEXT NOT NULL,
    city       TEXT,
    state      TEXT,
    region     TEXT
);

CREATE TABLE products (
    product_id      TEXT PRIMARY KEY,
    sku_name        TEXT NOT NULL,
    category        TEXT NOT NULL,
    brand           TEXT,
    unit_cost       REAL NOT NULL CHECK (unit_cost > 0),
    mrp             REAL NOT NULL CHECK (mrp > 0),
    gst_rate        INTEGER NOT NULL CHECK (gst_rate BETWEEN 0 AND 40),
    supplier_id     TEXT NOT NULL REFERENCES suppliers(supplier_id),
    shelf_life_days INTEGER
);

CREATE TABLE sales (
    line_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id    TEXT NOT NULL,
    sale_date     TEXT NOT NULL,          -- stored as YYYY-MM-DD
    store_id      TEXT NOT NULL REFERENCES stores(store_id),
    product_id    TEXT NOT NULL REFERENCES products(product_id),
    qty           INTEGER NOT NULL CHECK (qty > 0),
    selling_price REAL NOT NULL CHECK (selling_price > 0),
    discount_pct  REAL NOT NULL DEFAULT 0,
    payment_mode  TEXT CHECK (payment_mode IN ('UPI', 'Card', 'Cash'))
);

CREATE TABLE inventory (
    store_id          TEXT NOT NULL REFERENCES stores(store_id),
    product_id        TEXT NOT NULL REFERENCES products(product_id),
    stock_on_hand     INTEGER NOT NULL CHECK (stock_on_hand >= 0),
    reorder_level     INTEGER NOT NULL CHECK (reorder_level >= 0),
    last_restock_date TEXT,
    snapshot_date     TEXT NOT NULL,
    PRIMARY KEY (store_id, product_id)
);

CREATE INDEX idx_sales_date    ON sales(sale_date);
CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_sales_store   ON sales(store_id);

-- One row per sales line, with net revenue, cost, profit and Indian financial year
CREATE VIEW sales_enriched AS
SELECT
    s.line_id, s.invoice_id, s.sale_date, s.store_id, s.product_id, s.qty,
    s.selling_price, s.discount_pct, s.payment_mode,
    p.category, p.sku_name, p.gst_rate,
    st.city, st.region,
    s.qty * s.selling_price                              AS gross_sales,     -- GST-inclusive
    s.qty * s.selling_price / (1 + p.gst_rate / 100.0)   AS net_revenue,     -- excludes GST
    s.qty * p.unit_cost                                  AS cogs,
    s.qty * s.selling_price / (1 + p.gst_rate / 100.0) - s.qty * p.unit_cost AS gross_profit,
    CASE WHEN CAST(strftime('%m', s.sale_date) AS INTEGER) >= 4
         THEN strftime('%Y', s.sale_date) || '-' ||
              substr(CAST(CAST(strftime('%Y', s.sale_date) AS INTEGER) + 1 AS TEXT), 3, 2)
         ELSE CAST(CAST(strftime('%Y', s.sale_date) AS INTEGER) - 1 AS TEXT) || '-' ||
              strftime('%y', s.sale_date)
    END AS fy
FROM sales s
JOIN products p  ON p.product_id = s.product_id
JOIN stores st   ON st.store_id  = s.store_id;