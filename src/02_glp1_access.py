import duckdb, requests
con = duckdb.connect("formulary.duckdb")

def rxcuis(name):
    r = requests.get("https://rxnav.nlm.nih.gov/REST/drugs.json", params={"name": name}).json()
    return [p["rxcui"] for g in r["drugGroup"].get("conceptGroup", []) for p in g.get("conceptProperties", [])]

rows = [(b, c) for b in ["ozempic", "mounjaro", "trulicity", "rybelsus"] for c in rxcuis(b)]
con.sql("CREATE OR REPLACE TABLE drug_map (brand VARCHAR, rxcui VARCHAR)")
con.executemany("INSERT INTO drug_map VALUES (?, ?)", rows)
print(con.sql("SELECT d.brand, COUNT(DISTINCT d.rxcui) codes, COUNT(f.RXCUI) formulary_rows FROM drug_map d LEFT JOIN formulary f USING (rxcui) GROUP BY 1").df(), "\n")

print(con.sql("""
WITH p AS (SELECT DISTINCT CONTRACT_ID, PLAN_ID, SEGMENT_ID, FORMULARY_ID FROM plans WHERE PLAN_SUPPRESSED_YN='N'),
fb AS (SELECT f.FORMULARY_ID, d.brand, MIN(f.TIER_LEVEL_VALUE::INT) tier,
         MAX((f.PRIOR_AUTHORIZATION_YN='Y')::INT) pa, MAX((f.STEP_THERAPY_YN='Y')::INT) st
       FROM formulary f JOIN drug_map d USING (rxcui) GROUP BY 1,2),
b AS (SELECT DISTINCT brand FROM drug_map)
SELECT b.brand,
  ROUND(COUNT(fb.FORMULARY_ID)*100.0/COUNT(*),1) pct_plans_covering,
  ROUND(AVG(fb.pa)*100,1) pct_covered_with_pa,
  ROUND(AVG(fb.st)*100,1) pct_covered_with_st,
  MODE(fb.tier) typical_tier
FROM p CROSS JOIN b LEFT JOIN fb ON fb.FORMULARY_ID=p.FORMULARY_ID AND fb.brand=b.brand
GROUP BY 1 ORDER BY 2 DESC
""").df())
