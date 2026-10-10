"""Strict single-record measured CTG import; photographs/PDFs are not numeric features."""
import csv
import io
import json
from backend.services.inference import CTG_FEATURES
from backend.schemas.assessment import AssessmentInput


def ctg_template_csv():
    return ",".join(CTG_FEATURES)+"\n"+",".join("" for _ in CTG_FEATURES)+"\n"


def parse_ctg_csv(content):
    if len(content)>1_000_000:raise ValueError("CTG CSV must be smaller than 1 MB")
    try:text=content.decode("utf-8-sig")
    except UnicodeDecodeError:raise ValueError("Upload a UTF-8 CSV")
    reader=csv.reader(io.StringIO(text))
    rows=[row for row in reader if any(cell.strip() for cell in row)]
    if len(rows)!=2:raise ValueError("CTG CSV requires a header and exactly one patient record")
    header=[cell.strip() for cell in rows[0]]
    if len(header)!=21 or len(set(header))!=21 or set(header)!=set(CTG_FEATURES):
        raise ValueError("CTG CSV must contain exactly the 21 template feature names, with no duplicates")
    if len(rows[1])!=21:raise ValueError("CTG CSV record must contain 21 numeric values")
    try:features=dict(zip(header,[float(v.strip()) for v in rows[1]]))
    except ValueError:raise ValueError("Every CTG feature must be a measured numeric value")
    return complete_ctg(features)


def complete_ctg(features):
    AssessmentInput.ctg_numeric(features)
    if set(features)!=set(CTG_FEATURES):raise ValueError("Supply all 21 measured CTG features")
    return AssessmentInput.ctg_contract(features)


def parse_ctg_json(text):
    features=json.loads(text)
    if not isinstance(features,dict):raise ValueError("CTG JSON must be an object")
    return complete_ctg(features)
