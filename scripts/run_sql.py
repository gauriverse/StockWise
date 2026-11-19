
import sqlite3
import sys
from pathlib import Path

import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

ROOT = Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "stockwise.db")
text = Path(sys.argv[1]).read_text(encoding="utf-8")
for stmt in [s.strip() for s in text.split(";") if s.strip()]:
    print("\n>>", stmt.splitlines()[0])
    print(pd.read_sql_query(stmt, con).to_string(index=False))
con.close()