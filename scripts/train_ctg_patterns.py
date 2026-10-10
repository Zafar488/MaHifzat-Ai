"""Repair PretermGuard's original CLASS task as CTG pattern research, not preterm prediction."""
import json
import hashlib
from pathlib import Path
import sys
import joblib
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupShuffleSplit,StratifiedGroupKFold,GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score,classification_report
from lightgbm import LGBMClassifier
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.services.inference import CTG_FEATURES

def train():
    path=ROOT/"data/uci_ctg.parquet"
    frame=pd.read_parquet(path)
    x=frame[CTG_FEATURES].astype(float)
    y=frame.CLASS.astype(int)
    groups=pd.util.hash_pandas_object(x,index=False)
    train_idx,test_idx=next(GroupShuffleSplit(test_size=.2,random_state=20261010).split(x,y,groups))
    pipeline=Pipeline([("imputer",SimpleImputer(strategy="median")),("scaler",StandardScaler()),
                        ("estimator",RandomForestClassifier(n_estimators=200,class_weight="balanced",n_jobs=1,random_state=20261010))])
    grid=[{"estimator":[RandomForestClassifier(n_estimators=250,class_weight="balanced",n_jobs=1,random_state=20261010)],"estimator__min_samples_leaf":[1,3]},
          {"estimator":[LGBMClassifier(n_estimators=200,class_weight="balanced",n_jobs=1,verbosity=-1,random_state=20261010)],"estimator__num_leaves":[15,31]}]
    search=GridSearchCV(pipeline,grid,cv=StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=20261010),scoring="f1_macro",n_jobs=1,error_score="raise")
    search.fit(x.iloc[train_idx],y.iloc[train_idx],groups=groups.iloc[train_idx])
    winner=search.best_estimator_
    pred=winner.predict(x.iloc[test_idx])
    sample=x.iloc[[test_idx[0]]]
    folder=ROOT/"artifacts/research/pretermguard"
    folder.mkdir(parents=True,exist_ok=True)
    bundle={"schema_version":1,"model_version":"ctg-patterns-v3-20261010","pipeline":winner,"features":CTG_FEATURES,
          "sklearn_version":sklearn.__version__,"clinical_serving":False,"known_input":sample.iloc[0].to_dict(),
          "known_prediction":str(winner.predict(sample)[0]),"known_probabilities":winner.predict_proba(sample)[0].tolist(),
          "intended_use":"Original UCI CLASS CTG pattern classification (all 10 classes). No preterm outcome exists.",
          "label_map":{str(c):"CTG pattern class "+str(c) for c in winner.classes_}}
    joblib.dump(bundle,folder/"pipeline-v1.joblib")
    manifest={"dataset":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"target":"CLASS",
      "rows":len(frame),"classes":list(map(str,winner.classes_)),"train_indices":train_idx.tolist(),"test_indices":test_idx.tolist(),
      "cv_macro_f1":float(search.best_score_),"test_macro_f1":float(f1_score(y.iloc[test_idx],pred,average="macro")),
      "test_report":classification_report(y.iloc[test_idx],pred,output_dict=True,zero_division=0),
      "clinical_serving":False,"group_overlap":len(set(groups.iloc[train_idx])&set(groups.iloc[test_idx])),
      "not_clinical_reason":"CLASS denotes CTG patterns, not gestational age at birth or an observed preterm outcome.",
      "original_bug":"Legacy mapping retained only CLASS 1,2,3 as normal/suspect/pathological and discarded other pattern classes."}
    (folder/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("CTG pattern pipeline rebuilt; all",len(winner.classes_),"classes; research macro-F1",round(manifest["test_macro_f1"],4))
    return bundle,manifest
if __name__=="__main__":train()
