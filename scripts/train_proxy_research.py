"""Rebuild incompatible proxy artifacts for dataset research ONLY, never clinical serving."""
import argparse
import json
import hashlib
import platform
from pathlib import Path
import sys
import joblib
import pandas as pd
import numpy as np
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold, GridSearchCV
from sklearn.metrics import classification_report, f1_score
from lightgbm import LGBMClassifier
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.services.inference import DISABLED

def train(name):
    care=name=="carereach"
    path=ROOT/"data"/("carereach_prepared.parquet" if care else "gestation_prepared.parquet")
    df=pd.read_parquet(path)
    numeric=["Age","Scholarship","Hipertension","Diabetes","Alcoholism","Handcap","SMS_received","booking_delta_days","appointment_dow","sms_x_delta","comorbidity_count"] if care else [
        "Pregnancies","Glucose","BloodPressure","SkinThickness","Insulin","BMI","DiabetesPedigreeFunction","Age","MAP","glucose_tolerance_idx","age_parity_interaction","insulin_glucose_ratio","SBP_estimated"]
    categorical=["Gender","age_group"] if care else []
    features=numeric+categorical
    x=df[features].copy()
    for col in categorical: x[col]=x[col].astype(str)
    y=df["target"].astype(int)
    groups=df["PatientId"].astype(str) if care else pd.util.hash_pandas_object(x,index=False).astype(str)
    train_idx,test_idx=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=20261010).split(x,y,groups))
    numeric_steps=Pipeline([("imputer",SimpleImputer(strategy="median")),("scaler",RobustScaler())])
    transforms=[("numeric",numeric_steps,numeric)]
    if categorical:
        transforms.append(("categorical",OneHotEncoder(handle_unknown="ignore",sparse_output=False),categorical))
    pipeline=Pipeline([("preprocessor",ColumnTransformer(transforms)),
            ("estimator",LGBMClassifier(n_estimators=150,verbosity=-1,n_jobs=1,class_weight="balanced",random_state=20261010))])
    search=GridSearchCV(pipeline,{"estimator__num_leaves":[15,31]},cv=StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=20261010),scoring="f1_macro",n_jobs=1)
    search.fit(x.iloc[train_idx],y.iloc[train_idx],groups=groups.iloc[train_idx])
    winner=search.best_estimator_
    predictions=winner.predict(x.iloc[test_idx])
    sample=x.iloc[[test_idx[0]]]
    output=ROOT/"artifacts/research"/name
    output.mkdir(parents=True,exist_ok=True)
    bundle={"schema_version":1,"model_version":"research-only-v2-20261010","pipeline":winner,"features":features,
            "label_map":{str(c):str(c) for c in winner.classes_},"sklearn_version":sklearn.__version__,
            "python_version":platform.python_version(),"intended_use":DISABLED[name],
            "clinical_serving":False,"known_input":sample.iloc[0].to_dict(),
            "known_prediction":str(winner.predict(sample)[0]),"known_probabilities":winner.predict_proba(sample)[0].tolist()}
    joblib.dump(bundle,output/"pipeline-v1.joblib")
    report={"dataset":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"rows":len(df),"target":"target",
         "intended_use":"General appointment no-show dataset research" if care else "Pima-derived manufactured risk-label research",
         "not_clinical_reason":DISABLED[name],"cv_macro_f1":float(search.best_score_),
         "test_macro_f1":float(f1_score(y.iloc[test_idx],predictions,average="macro")),
         "test_report":classification_report(y.iloc[test_idx],predictions,output_dict=True,zero_division=0),
         "train_indices":train_idx.tolist(),"test_indices":test_idx.tolist(),"group_overlap":len(set(groups.iloc[train_idx])&set(groups.iloc[test_idx])),
         "split":"PatientId groups" if care else "Identical feature groups",
         "upstream_data_limitations":"Legacy prepared dataset lacks acquisition manifest. Gestation file was globally imputed and labels partly derived from input features; scores do not establish an obstetric outcome.",
         "model_version":bundle["model_version"],"clinical_serving":False}
    (output/"manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(name,"research-only compatible pipeline; internal label F1",round(report["test_macro_f1"],4))
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model",choices=["carereach","gestationinsight","all"],default="all")
    args=parser.parse_args()
    for name in (["carereach","gestationinsight"] if args.model=="all" else [args.model]): train(name)
