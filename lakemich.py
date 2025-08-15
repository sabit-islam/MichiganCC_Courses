"""
Lake Michigan College course scraper
Input:  lakemich_raw.csv 
Output: data/lake_mich.csv 

Developed by: Sabit Islam
Date: 08-14-2025
"""
import pandas as pd


INPUT_CSV  = "lakemich_raw.csv"  
OUTPUT_CSV = "data/lake_mich.csv"    

COL_SUBJ   = "Course Subject Code"
COL_NUM    = "Course Number"
COL_TITLE  = "Course Title"
COL_CRED   = "Credits - Credit Hours - Credit Hours Min"
COL_DESC   = "Course Description"

df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")

def combine_code(row) -> str:
    subj = (row.get(COL_SUBJ, "") or "").strip()
    num  = (row.get(COL_NUM, "") or "").strip()
    return f"{subj} {num}".strip()

out = pd.DataFrame({
    "course_code":   df.apply(combine_code, axis=1),
    "course_name":   df[COL_TITLE].str.strip(),
    "credit_hours":  df[COL_CRED].str.strip(),
    "description":   df[COL_DESC].str.replace(r"\s+", " ", regex=True).str.strip(),
})

out = out[out["course_code"] != ""].drop_duplicates().reset_index(drop=True)

out.to_csv(OUTPUT_CSV, index=False)
print(f"Saved {len(out):,} rows to {OUTPUT_CSV}")
