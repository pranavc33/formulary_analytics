import duckdb
con = duckdb.connect("formulary.duckdb")
for t in ["formulary", "plans"]:
    con.sql(f"""CREATE OR REPLACE TABLE {t} AS
        SELECT * FROM read_csv('data/{t}.txt', delim='|', header=true, all_varchar=true, encoding='latin-1')""")
    print(t, "rows:", con.sql(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    print([c[0] for c in con.sql(f"DESCRIBE {t}").fetchall()], "\n")
