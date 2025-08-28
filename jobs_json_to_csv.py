import json
import pandas as pd

# Paths
json_path = "example-job/jobs_dataset.json"
csv_clean_path = "example-job/jobs_dataset.csv"

# Load
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Normalize arrays to pipe-separated strings and None -> ""


def join_list(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return " | ".join(map(str, v))
    return v


for item in data:
    item["responsibilities"] = join_list(item.get("responsibilities"))
    item["qualifications"] = join_list(item.get("qualifications"))
    item["preferredFaculties"] = join_list(item.get("preferredFaculties"))
    # normalize nullable
    if item.get("ageLimit") is None:
        item["ageLimit"] = ""

# Flatten nested companyInfo with pd.json_normalize
df = pd.json_normalize(data, sep=".")

# Optional: rename dotted columns to friendlier names
rename_map = {
    "companyInfo.name": "companyInfo_name",
    "companyInfo.description": "companyInfo_description",
    "companyInfo.employees": "companyInfo_employees",
    "companyInfo.industry": "companyInfo_industry",
    "companyInfo.website": "companyInfo_website",
}
df = df.rename(columns=rename_map)

# Reorder columns for readability
col_order = [
    "id", "position", "company", "logo", "level", "openings", "closingDate", "location",
    "employeeType", "salary", "experience", "ageLimit", "education",
    "matchingPercentage" if "matchingPercentage" in df.columns else None,
    "description", "responsibilities", "qualifications", "preferredFaculties",
    "companyInfo_name", "companyInfo_description", "companyInfo_employees",
    "companyInfo_industry", "companyInfo_website"
]
# filter None and only include present columns
col_order = [c for c in col_order if c and c in df.columns]
df = df[col_order]

# Save clean CSV
df.to_csv(csv_clean_path, index=False, encoding="utf-8")
