"""All five models are executable with their actual target and input contract disclosed."""
import json
import math
from functools import lru_cache
import joblib
import pandas as pd
import numpy as np
import sklearn
from backend.config import settings
from backend.services.inference import ModelRegistry,MATERNAL_FEATURES,CTG_FEATURES

@lru_cache(maxsize=3)
def research_bundle(name):
    if name not in ("pretermguard","carereach","gestationinsight"):raise ValueError("Unknown model")
    bundle=joblib.load(settings.ARTIFACTS_DIR/"research"/name/"pipeline-v1.joblib")
    if bundle["sklearn_version"]!=sklearn.__version__:raise ValueError("Incompatible model runtime")
    sample=pd.DataFrame([bundle["known_input"]],columns=bundle["features"])
    if str(bundle["pipeline"].predict(sample)[0])!=bundle["known_prediction"]:raise ValueError("Artifact parity failed")
    return bundle

def catalog():
    items=[]
    for name in ("maternalguard","fetalwatch","pretermguard","gestationinsight","carereach"):
        clinical=name in ("maternalguard","fetalwatch")
        try:
            bundle=ModelRegistry()._models[name] if clinical else research_bundle(name)
            manifest_path=settings.ARTIFACTS_DIR/("serving" if clinical else "research")/name/"manifest.json"
            manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
            features=bundle["features"]
            example=bundle["known_input"]
            if isinstance(example,list):example=dict(zip(features,example))
            items.append({"name":name,"executable":True,"care_decision_use":clinical,"intended_use":bundle["intended_use"],
                 "features":features,"example":example,"version":bundle["model_version"],
                 "internal_macro_f1":manifest.get("final_test_macro_f1",manifest.get("test_macro_f1")),
                 "target":manifest.get("target","target"),"clinical_validation":"not established"})
        except (OSError,ValueError,KeyError,AttributeError):
            items.append({"name":name,"executable":False,"care_decision_use":clinical,"reason":"Model runtime is unavailable"})
    return items

def predict(name,features):
    if name=="maternalguard":return ModelRegistry().predict_maternal_risk(features)
    if name=="fetalwatch":return ModelRegistry().predict_fetal_health(features)
    bundle=research_bundle(name)
    expected=set(bundle["features"])
    if set(features)!=expected:raise ValueError("Supply exactly these features: "+", ".join(bundle["features"]))
    values={}
    for key,value in features.items():
        if key in ("Gender","age_group"):
            if not isinstance(value,str) or len(value)>50:raise ValueError("Invalid category")
            values[key]=value
        else:
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError("Numeric finite features required")
            values[key]=float(value)
    if name=="pretermguard":
        from backend.schemas.assessment import AssessmentInput
        AssessmentInput.ctg_contract(values)
    sample=pd.DataFrame([values],columns=bundle["features"])
    label=str(bundle["pipeline"].predict(sample)[0])
    probs=bundle["pipeline"].predict_proba(sample)[0]
    if not np.isfinite(probs).all() or not np.isclose(probs.sum(),1):raise ValueError("Invalid model output")
    return {"status":"research_prediction","model":name,"label":bundle["label_map"].get(label,label),
       "probabilities":{bundle["label_map"].get(str(c),str(c)):float(p) for c,p in zip(bundle["pipeline"].classes_,probs)},
       "model_version":bundle["model_version"],"intended_use":bundle["intended_use"],"care_decision_use":False,
       "clinical_validation":"not established","warning":"Dataset-specific research output; it must not determine obstetric referral or treatment."}
