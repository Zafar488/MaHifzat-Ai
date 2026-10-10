"""Offline checks for honest dataset fallback and the real sklearn WDBC schema."""
import json
import sys
import pandas as pd
import pytest
import download_and_prep as prep

def test_no_silent_synthetic_fallback_and_explicit_manifest(tmp_path,monkeypatch):
    monkeypatch.setattr(prep,"DATA_DIR",tmp_path)
    monkeypatch.setitem(sys.modules,"kagglehub",None)
    monkeypatch.setattr(prep,"_try_url_download",lambda *a,**kw: None)
    with pytest.raises(RuntimeError,match="explicit"):
        prep.prepare_carereach()
    assert not list(tmp_path.glob("*.parquet"))
    original=prep._generate_synthetic_carereach
    monkeypatch.setattr(prep,"_generate_synthetic_carereach",lambda:original(12))
    df=prep.prepare_carereach(allow_synthetic=True)
    manifest=json.loads((tmp_path/"carereach_prepared.provenance.json").read_text())
    assert len(df)==12 and manifest["synthetic"] is True
    assert manifest["rows"]==12 and len(manifest["sha256"])==64

def test_wdbc_builtin_fallback_has_expected_feature_names(tmp_path,monkeypatch):
    monkeypatch.setattr(prep,"DATA_DIR",tmp_path)
    monkeypatch.setattr(prep,"_try_url_download",lambda *a,**kw: None)
    df=prep.prepare_oncotrace()
    assert len(df)==569
    assert {"radius_mean","radius_worst","texture_se","target","volume_mean"} <= set(df)
    assert not df.select_dtypes(include="number").isna().any().any()
    manifest=json.loads((tmp_path/"oncotrace_prepared.provenance.json").read_text())
    assert manifest["synthetic"] is False and "sklearn" in manifest["source"]
