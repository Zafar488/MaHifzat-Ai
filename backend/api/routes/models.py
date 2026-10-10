"""Authenticated model catalog and explicit dataset-contract inference."""
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict
from typing import Literal
from backend.api.auth import get_current_user
from backend.api.deps import get_model_registry
from backend.services.model_workbench import catalog,predict
router=APIRouter(prefix="/models",tags=["five-model workbench"])

@router.get("/catalog")
async def model_catalog(user=Depends(get_current_user),registry=Depends(get_model_registry)):
    return {"models":catalog()}

class PredictRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    model:Literal["maternalguard","fetalwatch","pretermguard","gestationinsight","carereach"]
    features:dict

@router.post("/predict")
async def model_predict(request:PredictRequest,user=Depends(get_current_user),registry=Depends(get_model_registry)):
    try:return predict(request.model,request.features)
    except ValueError as exc:raise HTTPException(422,str(exc))
    except (OSError,KeyError,AttributeError,TypeError):raise HTTPException(503,"Model runtime unavailable")
