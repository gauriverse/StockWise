import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "stockwise.db"
if DB.exists():
    DB.unlink()  # rebuild from scratch

con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys = ON")  # make SQLite enforce foreign keys
con.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))

# parent tables first, child tables after
for table in ["suppliers", "stores", "products", "sales", "inventory"]:
    df = pd.read_csv(ROOT / "data" / f"{table}.csv")
    df.to_sql(table, con, if_exists="append", index=False)
    print(f"loaded {table}: {len(df):,} rows")

con.commit()
con.close()
print("done ->", DB)