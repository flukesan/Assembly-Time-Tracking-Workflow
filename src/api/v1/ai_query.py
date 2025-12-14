"""
AI Query API
Natural language queries powered by RAG + DeepSeek-R1
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel
import logging

from llm.ollama_client import OllamaClient, ChatMessage
from llm.prompt_templates import PromptTemplate
from rag.knowledge_base import KnowledgeBase

router = APIRouter(prefix="/api/v1/ai", tags=["ai-query"])
logger = logging.getLogger(__name__)

# Global instances (will be injected during startup)
ollama_client: Optional[OllamaClient] = None
knowledge_base: Optional[KnowledgeBase] = None


def set_ollama_client(client: OllamaClient):
    """Set global Ollama client instance"""
    global ollama_client
    ollama_client = client


def set_knowledge_base(kb: KnowledgeBase):
    """Set global knowledge base instance"""
    global knowledge_base
    knowledge_base = kb


# Request/Response Models
class QueryRequest(BaseModel):
    question: str
    show_reasoning: bool = True
    max_context_items: int = 5


class QueryResponse(BaseModel):
    question: str
    answer: str
    reasoning: Optional[str] = None
    context_used: dict
    model: str
    duration_ms: Optional[int] = None


class WorkerAnalysisRequest(BaseModel):
    worker_id: str
    include_recommendations: bool = True


class CompareWorkersRequest(BaseModel):
    worker_ids: List[str]
    criteria: Optional[str] = "overall_productivity"


class ShiftSummaryRequest(BaseModel):
    shift: str  # morning, afternoon, night
    date: Optional[str] = None  # YYYY-MM-DD


# Endpoints

@router.post("/query", response_model=QueryResponse)
async def natural_language_query(request: QueryRequest):
    """
    Ask questions in natural language (Thai or English)

    Examples:
    - "พนักงาน W001 ทำงานอย่างไรบ้างวันนี้?"
    - "Who has the highest productivity in the morning shift?"
    - "แนะนำการปรับปรุงสำหรับพนักงานที่มี efficiency ต่ำกว่า 70%"
    """
    if not ollama_client or not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI services not initialized"
        )

    try:
        # Get relevant context from knowledge base
        context = knowledge_base.get_context_for_query(
            query=request.question,
            max_results=request.max_context_items
        )

        # Build prompt with context
        prompt = PromptTemplate.natural_language_query(
            question=request.question,
            context_data=context
        )

        # Build messages
        messages = [
            ChatMessage(
                role="system",
                content=PromptTemplate.SYSTEM_WORKER_ANALYST
            ),
            ChatMessage(
                role="user",
                content=prompt
            )
        ]

        # Query LLM
        response = await ollama_client.chat(
            messages=messages,
            temperature=0.7,
            show_reasoning=request.show_reasoning
        )

        return QueryResponse(
            question=request.question,
            answer=response.content,
            reasoning=response.reasoning,
            context_used=context,
            model=response.model or "deepseek-r1:14b",
            duration_ms=response.total_duration_ms
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


@router.post("/analyze/worker")
async def analyze_worker(request: WorkerAnalysisRequest):
    """
    Analyze a specific worker's performance
    """
    if not ollama_client or not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI services not initialized"
        )

    try:
        # Search for worker productivity data
        results = knowledge_base.search_productivity(
            query=f"worker {request.worker_id} productivity performance",
            limit=5,
            worker_id=request.worker_id
        )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No productivity data found for worker {request.worker_id}"
            )

        # Get latest productivity data
        latest = results[0]['payload']
        indices = latest.get('indices', {})

        # Generate analysis prompt
        prompt = PromptTemplate.worker_performance_query(
            worker_name=latest.get('worker_name', request.worker_id),
            indices=indices,
            context="Please provide detailed analysis and actionable recommendations." if request.include_recommendations else ""
        )

        # Query LLM
        response = await ollama_client.generate(
            prompt=prompt,
            temperature=0.7
        )

        return {
            "worker_id": request.worker_id,
            "worker_name": latest.get('worker_name'),
            "analysis": response.content,
            "reasoning": response.reasoning,
            "productivity_data": indices,
            "model": response.model
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Worker analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/compare/workers")
async def compare_workers(request: CompareWorkersRequest):
    """
    Compare multiple workers' performance
    """
    if not ollama_client or not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI services not initialized"
        )

    try:
        # Gather data for all workers
        workers_data = []

        for worker_id in request.worker_ids:
            results = knowledge_base.search_productivity(
                query=f"worker {worker_id} latest productivity",
                limit=1,
                worker_id=worker_id
            )

            if results:
                payload = results[0]['payload']
                workers_data.append({
                    'name': payload.get('worker_name', worker_id),
                    'worker_id': worker_id,
                    'indices': payload.get('indices', {})
                })

        if not workers_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No productivity data found for specified workers"
            )

        # Generate comparison prompt
        prompt = PromptTemplate.compare_workers(workers_data)

        # Query LLM
        response = await ollama_client.generate(
            prompt=prompt,
            temperature=0.7
        )

        return {
            "workers_compared": len(workers_data),
            "comparison": response.content,
            "reasoning": response.reasoning,
            "workers_data": workers_data,
            "model": response.model
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Worker comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )


@router.post("/summary/shift")
async def shift_summary(request: ShiftSummaryRequest):
    """
    Generate shift performance summary
    """
    if not ollama_client or not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI services not initialized"
        )

    try:
        # Search for shift data
        query = f"{request.shift} shift productivity performance"
        if request.date:
            query += f" on {request.date}"

        results = knowledge_base.search_productivity(
            query=query,
            limit=20
        )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for {request.shift} shift"
            )

        # Calculate shift statistics
        total_workers = len(set(r['payload'].get('worker_id') for r in results))
        productivities = [r['payload'].get('overall_productivity', 0) for r in results]
        avg_productivity = sum(productivities) / len(productivities) if productivities else 0

        total_output = sum(
            r['payload'].get('indices', {}).get('index_8_tasks_completed', 0)
            for r in results
        )

        # Detect issues
        issues = []
        for r in results:
            indices = r['payload'].get('indices', {})
            if indices.get('index_11_overall_productivity', 0) < 60:
                issues.append(
                    f"Low productivity: {r['payload'].get('worker_name')} ({indices.get('index_11_overall_productivity', 0):.1f}/100)"
                )

        # Generate summary prompt
        prompt = PromptTemplate.shift_summary(
            shift_name=request.shift,
            total_workers=total_workers,
            avg_productivity=avg_productivity,
            total_output=total_output,
            issues=issues[:5] if issues else None
        )

        # Query LLM
        response = await ollama_client.generate(
            prompt=prompt,
            temperature=0.7
        )

        return {
            "shift": request.shift,
            "date": request.date,
            "summary": response.content,
            "reasoning": response.reasoning,
            "statistics": {
                "total_workers": total_workers,
                "avg_productivity": avg_productivity,
                "total_output": total_output,
                "issues_count": len(issues)
            },
            "model": response.model
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Shift summary failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}"
        )


@router.get("/health")
async def ai_health_check():
    """Check AI services health"""
    health = {
        "ollama_client": {
            "initialized": ollama_client is not None,
            "connected": False
        },
        "knowledge_base": {
            "initialized": knowledge_base is not None
        }
    }

    if ollama_client:
        health["ollama_client"]["connected"] = await ollama_client.check_connection()
        if health["ollama_client"]["connected"]:
            health["ollama_client"]["stats"] = ollama_client.get_stats()

    if knowledge_base:
        health["knowledge_base"]["stats"] = knowledge_base.get_stats()

    return health


@router.get("/models")
async def list_models():
    """List available LLM models"""
    if not ollama_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama client not initialized"
        )

    try:
        models = await ollama_client.list_models()
        return {
            "models": models,
            "current_model": ollama_client.model
        }
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )
