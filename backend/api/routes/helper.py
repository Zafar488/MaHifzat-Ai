"""Pregnancy Helper API routes: Chat, evidence retrieval, and public hospital search."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.api.auth import get_current_user
from backend.services.pregnancy_rag import generate_pregnancy_advice, search_duckduckgo, check_urgent_symptoms

router = APIRouter(prefix="/helper", tags=["helper"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    language: str = Field("en", pattern="^(en|ur|roman_urdu|ur_roman)$")
    shared_assessment: Optional[Dict[str, Any]] = None
    chat_history: Optional[List[ChatMessage]] = None

class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=200)

@router.post("/chat")
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    """Conversational endpoint for Pregnancy Education Helper with RAG, danger sign check and Citations."""
    history = [msg.model_dump() for msg in request.chat_history] if request.chat_history else None
    result = await generate_pregnancy_advice(
        query=request.query,
        language=request.language,
        shared_assessment=request.shared_assessment,
        chat_history=history
    )
    return result

@router.post("/search")
async def public_search(request: SearchRequest, user=Depends(get_current_user)):
    """Supplementary DuckDuckGo public search for general hospital / clinical guidance without patient PII."""
    snippets = await search_duckduckgo(request.query, max_results=5)
    return {"query": request.query, "results": snippets}
