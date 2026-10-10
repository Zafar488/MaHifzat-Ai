"""Read-only data/model checks; writes a reproducible evidence report under docs."""
from pathlib import Path
import sys
import ast
import hashlib
import json
import warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix, f1_score
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.services.inference import MATERNAL_FEATURES, CTG_FEATURES, ModelRegistry, DISABLED

def datasets():
    result = {}
    for path in sorted((ROOT/"data").glob("*.parquet")):
        df = pd.read_parquet(path)
        numeric = df.select_dtypes(include="number")
        item = {"rows":len(df),"columns":list(df.columns),"null_cells":int(df.isna().sum().sum()),
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "infinite_numeric_cells":int(np.isinf(numeric.to_numpy(dtype=float)).sum())}
        if path.name in ("uci_maternal.parquet","uci_ctg.parquet"):
            features = MATERNAL_FEATURES if "maternal" in path.name else CTG_FEATURES
            target = "RiskLevel" if "maternal" in path.name else "NSP"
            groups = pd.util.hash_pandas_object(df[features].astype(float),index=False)
            item.update(unique_feature_groups=int(groups.nunique()),duplicate_feature_rows=int(groups.duplicated().sum()),
                        conflicting_label_groups=int(pd.DataFrame({"group":groups,"target":df[target]}).groupby("group").target.nunique().gt(1).sum()),
                        labels={str(k):int(v) for k,v in df[target].value_counts().items()})
        else:
            item["source_provenance"] = "No local acquisition manifest; origin cannot be certified from row count"
        result[path.name]=item
    return result

def supported():
    registry = ModelRegistry()
    registry.load_all()
    results = {}
    for name,features in [("maternalguard",MATERNAL_FEATURES),("fetalwatch",CTG_FEATURES)]:
        manifest_path = ROOT/"artifacts/serving"/name/"manifest.json"
        manifest=json.loads(manifest_path.read_text())
        df=pd.read_parquet(ROOT/"data"/manifest["dataset"])
        assert hashlib.sha256((ROOT/"data"/manifest["dataset"]).read_bytes()).hexdigest() == manifest["sha256"], "Dataset hash mismatch"
        bundle=registry._models[name]
        x=df[features].astype(float)
        y=df.RiskLevel.astype(str) if name == "maternalguard" else df.NSP.map({1:"normal",2:"suspect",3:"pathological"})
        train,test=manifest["train_indices"],manifest["test_indices"]
        groups=pd.util.hash_pandas_object(x,index=False)
        overlap=len(set(groups.iloc[train])&set(groups.iloc[test]))
        assert overlap == 0
        pred=bundle["pipeline"].predict(x.iloc[test])
        probs=bundle["pipeline"].predict_proba(x.iloc[test])
        assert np.isfinite(probs).all() and np.allclose(probs.sum(axis=1),1)
        f1=float(f1_score(y.iloc[test],pred,average="macro"))
        assert abs(f1-manifest["final_test_macro_f1"]) < 1e-10
        results[name]={"algorithm":type(bundle["pipeline"].named_steps["estimator"]).__name__,
            "model_version":bundle["model_version"],"test_rows":len(test),"test_macro_f1":f1,
            "training_cv_macro_f1":manifest["cv_macro_f1"],"train_test_group_overlap":overlap,
            "test_report":classification_report(y.iloc[test],pred,output_dict=True,zero_division=0),
            "confusion_matrix":confusion_matrix(y.iloc[test],pred,labels=list(bundle["pipeline"].classes_)).tolist(),
            "classes":list(map(str,bundle["pipeline"].classes_)),
            "clinical_validation":"Not established; repeated internal holdout, no local external validation"}
    return results

def research():
    results={}
    for name in ("carereach","gestationinsight","pretermguard"):
        folder=ROOT/"artifacts/research"/name
        bundle=joblib.load(folder/"pipeline-v1.joblib")
        manifest=json.loads((folder/"manifest.json").read_text())
        path=ROOT/"data"/manifest["dataset"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest["sha256"]
        df=pd.read_parquet(path)
        x=df[bundle["features"]].copy()
        if name=="carereach":
            for col in ("Gender","age_group"): x[col]=x[col].astype(str)
            groups=df.PatientId.astype(str)
        else:
            groups=pd.util.hash_pandas_object(x.astype(float) if name=="pretermguard" else x,index=False).astype(str)
        train,test=manifest["train_indices"],manifest["test_indices"]
        assert not set(groups.iloc[train])&set(groups.iloc[test])
        predictions=bundle["pipeline"].predict(x.iloc[test])
        probabilities=bundle["pipeline"].predict_proba(x.iloc[test])
        assert np.isfinite(probabilities).all() and np.allclose(probabilities.sum(axis=1),1)
        score=float(f1_score(df[manifest.get("target","target")].iloc[test],predictions,average="macro"))
        assert abs(score-manifest["test_macro_f1"])<1e-10
        results[name]={"load_and_predict":"passed","clinical_serving":False,
          "test_macro_f1":score,"train_test_group_overlap":0,
          "not_clinical_reason":manifest["not_clinical_reason"],
          "upstream_data_limitations":manifest.get("upstream_data_limitations",manifest["not_clinical_reason"])}
    return results


def legacy():
    results={}
    for name in ("maternalguard","fetalwatch","pretermguard","carereach","gestationinsight"):
        path=ROOT/"artifacts"/name/"best_model.joblib"
        row={"path":str(path.relative_to(ROOT)),"served":False}
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model=joblib.load(path)
                if name in ("fetalwatch","pretermguard"):
                    x=pd.read_parquet(ROOT/"data/uci_ctg.parquet")[CTG_FEATURES].iloc[:5]
                elif name=="maternalguard":
                    x=pd.read_parquet(ROOT/"data/uci_maternal.parquet")[MATERNAL_FEATURES].iloc[:5]
                elif name=="carereach":
                    pre=joblib.load(path.parent/"preprocessor.joblib")
                    df=pd.read_parquet(ROOT/"data/carereach_prepared.parquet").iloc[:5].copy()
                    for col in ("Gender","age_group"): df[col]=df[col].astype(str)
                    x=pre.transform(df)
                else:
                    pre=joblib.load(path.parent/"preprocessor.joblib")
                    metadata=json.loads((path.parent/"metadata.json").read_text())
                    cols=metadata.get("numeric_features") or metadata.get("feature_list") or list(pre.feature_names_in_)
                    cols=list(pre.feature_names_in_) if hasattr(pre,"feature_names_in_") else cols
                    x=pre.transform(pd.read_parquet(ROOT/"data/gestation_prepared.parquet")[cols].iloc[:5])
                pred=model.predict(x)
                probs=model.predict_proba(x)
                row.update(load_and_predict="passed",sample_predictions=list(map(str,pred)),
                    finite_normalized_probabilities=bool(np.isfinite(probs).all() and np.allclose(probs.sum(axis=1),1)),
                    algorithm=type(model).__name__)
        except Exception as exc:
            row.update(load_and_predict="failed",error_type=type(exc).__name__)
        row["reason_not_served"] = DISABLED.get(name,"Bare legacy estimator without the complete verified train-time preprocessing contract")
        results[name]=row
    return results

def physionet():
    from src.data.loaders.physionet_ctg import load_physionet_records
    from src.features.ctg_features import extract_features_from_signal
    records=load_physionet_records()
    results=[]
    for record in records:
        features=extract_features_from_signal(record["fhr_signal"],record["uc_signal"],record["fs"])
        results.append({"record":record["record_name"],"sampling_hz":record["fs"],
            "duration_minutes":len(record["fhr_signal"])/record["fs"]/60,
            "feature_extraction_finite":bool(np.isfinite(features.to_numpy()).all())})
    return {"records_read":len(records),"records":results,"served":False,
            "reason":"Exploratory extraction uses heuristic variability/movement definitions; no established equivalence to UCI device features or independent clinical evaluation"}

def inventory():
    result=[]
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file(): continue
        rel=path.relative_to(ROOT)
        if any(p in (".git",".venv","__pycache__", ".pytest_cache",".qoder") for p in rel.parts): continue
        if path.name=="project_inventory.json": continue
        if path.name.startswith(".env") and path.name != ".env.example": continue
        if path.suffix not in (".py",".md",".json",".toml",".bat",".html",".ipynb",".txt"): continue
        if "archive" in rel.parts or path.name == "pre-existing-status.txt": continue
        content=path.read_text(encoding="utf-8-sig")
        row={"file":rel.as_posix(),"lines":len(content.splitlines()),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        if path.suffix == ".py":
            tree=ast.parse(content)
            row["functions"]=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        elif path.suffix == ".ipynb":
            row["cells"]=len(json.loads(content).get("cells",[]))
        result.append(row)
    return result

def main():
    report={"datasets":datasets(),"supported":supported(),"legacy_smoke_checks":legacy(),"research_rebuilds":research(),"physionet":physionet(),
            "limitations":["No prospective local clinical validation","No independently labelled preterm, gestational-complication or ANC population dataset",
                           "Legacy smoke checks demonstrate estimator execution only, not clinical correctness or independent accuracy"]}
    folder=ROOT/"docs"
    folder.mkdir(exist_ok=True)
    (folder/"model_audit.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    (folder/"project_inventory.json").write_text(json.dumps(inventory(),indent=2),encoding="utf-8")
    for name,value in report["supported"].items():
        print(name,value["algorithm"],"holdout macro-F1",round(value["test_macro_f1"],4))
    for name,value in report["legacy_smoke_checks"].items():
        print("legacy",name,value["load_and_predict"])
    print("PhysioNet records read:",report["physionet"]["records_read"])
if __name__ == "__main__":
    main()
