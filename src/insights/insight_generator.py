"""
Insight Generator
Automatically generates AI-powered insights from worker data
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from llm.ollama_client import OllamaClient, ChatMessage
from llm.prompt_templates import PromptTemplate
from rag.knowledge_base import KnowledgeBase
from workers.worker_models import ProductivityIndex

logger = logging.getLogger(__name__)


class InsightGenerator:
    """
    Generates automated insights about worker performance
    """

    def __init__(
        self,
        ollama_client: OllamaClient,
        knowledge_base: KnowledgeBase,
        min_productivity_threshold: float = 60.0,
        min_efficiency_threshold: float = 70.0
    ):
        """
        Initialize insight generator

        Args:
            ollama_client: Ollama client for LLM
            knowledge_base: Knowledge base for data retrieval
            min_productivity_threshold: Minimum acceptable productivity
            min_efficiency_threshold: Minimum acceptable efficiency
        """
        self.ollama = ollama_client
        self.kb = knowledge_base
        self.min_productivity = min_productivity_threshold
        self.min_efficiency = min_efficiency_threshold

        logger.info("InsightGenerator initialized")

    async def generate_daily_insights(
        self,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate insights for a specific day

        Args:
            date: Target date (default: today)

        Returns:
            Dict with generated insights
        """
        date = date or datetime.now()
        date_str = date.strftime('%Y-%m-%d')

        logger.info(f"Generating daily insights for {date_str}")

        insights = {
            'date': date_str,
            'generated_at': datetime.now().isoformat(),
            'low_performers': [],
            'top_performers': [],
            'shift_analysis': {},
            'recommendations': [],
            'alerts': []
        }

        try:
            # Search for productivity data from the date
            query = f"productivity performance on {date_str}"
            results = self.kb.search_productivity(query, limit=50)

            if not results:
                logger.warning(f"No productivity data found for {date_str}")
                return insights

            # Analyze workers
            workers_data = []
            for result in results:
                payload = result['payload']
                indices = payload.get('indices', {})

                worker_data = {
                    'worker_id': payload.get('worker_id'),
                    'worker_name': payload.get('worker_name'),
                    'shift': payload.get('shift'),
                    'productivity': indices.get('index_11_overall_productivity', 0),
                    'efficiency': indices.get('index_5_work_efficiency', 0),
                    'output': indices.get('index_9_output_per_hour', 0),
                    'quality': indices.get('index_10_quality_score', 0),
                    'indices': indices
                }
                workers_data.append(worker_data)

            # Identify low performers
            low_performers = [
                w for w in workers_data
                if w['productivity'] < self.min_productivity
            ]

            # Identify top performers
            sorted_workers = sorted(
                workers_data,
                key=lambda x: x['productivity'],
                reverse=True
            )
            top_performers = sorted_workers[:5]

            # Generate AI insights for low performers
            if low_performers:
                insights['low_performers'] = await self._analyze_low_performers(
                    low_performers
                )

            # Generate AI insights for top performers
            if top_performers:
                insights['top_performers'] = await self._analyze_top_performers(
                    top_performers
                )

            # Analyze by shift
            shifts = {}
            for worker in workers_data:
                shift = worker['shift']
                if shift not in shifts:
                    shifts[shift] = []
                shifts[shift].append(worker)

            for shift_name, shift_workers in shifts.items():
                insights['shift_analysis'][shift_name] = await self._analyze_shift(
                    shift_name,
                    shift_workers
                )

            # Generate overall recommendations
            insights['recommendations'] = await self._generate_recommendations(
                workers_data,
                low_performers,
                top_performers
            )

            # Generate alerts
            insights['alerts'] = self._generate_alerts(workers_data)

            # Store insights in knowledge base
            await self._store_insights(insights)

            logger.info(f"Daily insights generated successfully for {date_str}")

        except Exception as e:
            logger.error(f"Failed to generate daily insights: {e}")
            insights['error'] = str(e)

        return insights

    async def _analyze_low_performers(
        self,
        workers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze low performing workers"""
        analyses = []

        for worker in workers[:5]:  # Limit to top 5
            try:
                prompt = PromptTemplate.worker_performance_query(
                    worker_name=worker['worker_name'],
                    indices=worker['indices'],
                    context="Focus on identifying root causes and actionable improvements."
                )

                messages = [
                    ChatMessage(role="system", content=PromptTemplate.SYSTEM_WORKER_ANALYST),
                    ChatMessage(role="user", content=prompt)
                ]

                response = await self.ollama.chat(
                    messages=messages,
                    temperature=0.7,
                    show_reasoning=False
                )

                analyses.append({
                    'worker_id': worker['worker_id'],
                    'worker_name': worker['worker_name'],
                    'productivity': worker['productivity'],
                    'analysis': response.content,
                    'indices': worker['indices']
                })

            except Exception as e:
                logger.error(f"Failed to analyze worker {worker['worker_id']}: {e}")

        return analyses

    async def _analyze_top_performers(
        self,
        workers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze top performing workers"""
        analyses = []

        for worker in workers:
            analyses.append({
                'worker_id': worker['worker_id'],
                'worker_name': worker['worker_name'],
                'productivity': worker['productivity'],
                'efficiency': worker['efficiency'],
                'output': worker['output'],
                'quality': worker['quality'],
                'best_practices': self._extract_best_practices(worker)
            })

        return analyses

    def _extract_best_practices(self, worker: Dict[str, Any]) -> List[str]:
        """Extract best practices from top performer"""
        practices = []

        if worker['efficiency'] > 85:
            practices.append(f"High work efficiency ({worker['efficiency']:.1f}%)")

        if worker['quality'] > 90:
            practices.append(f"Excellent quality score ({worker['quality']:.1f}/100)")

        if worker['output'] > 12:
            practices.append(f"High output rate ({worker['output']:.2f} per hour)")

        return practices

    async def _analyze_shift(
        self,
        shift_name: str,
        workers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze shift performance"""
        avg_productivity = sum(w['productivity'] for w in workers) / len(workers) if workers else 0
        total_output = sum(w.get('indices', {}).get('index_8_tasks_completed', 0) for w in workers)

        issues = []
        for w in workers:
            if w['productivity'] < self.min_productivity:
                issues.append(f"{w['worker_name']}: {w['productivity']:.1f}/100")

        return {
            'total_workers': len(workers),
            'avg_productivity': avg_productivity,
            'total_output': total_output,
            'issues': issues,
            'status': 'good' if avg_productivity >= 70 else 'needs_improvement'
        }

    async def _generate_recommendations(
        self,
        all_workers: List[Dict[str, Any]],
        low_performers: List[Dict[str, Any]],
        top_performers: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []

        # Overall productivity
        avg_productivity = sum(w['productivity'] for w in all_workers) / len(all_workers) if all_workers else 0

        if avg_productivity < 70:
            recommendations.append(
                f"⚠️ Overall productivity is below target ({avg_productivity:.1f}/100). Consider team training."
            )

        # Low performers
        if len(low_performers) > len(all_workers) * 0.3:
            recommendations.append(
                f"📊 {len(low_performers)} workers ({len(low_performers)/len(all_workers)*100:.0f}%) need performance improvement."
            )

        # Quality issues
        low_quality_count = sum(1 for w in all_workers if w['quality'] < 80)
        if low_quality_count > 0:
            recommendations.append(
                f"🎯 {low_quality_count} workers have quality scores below 80. Implement quality control measures."
            )

        # Best practices
        if top_performers:
            top_worker = top_performers[0]
            recommendations.append(
                f"⭐ {top_worker['worker_name']} is the top performer ({top_worker['productivity']:.1f}/100). Share their best practices."
            )

        return recommendations

    def _generate_alerts(self, workers: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate alerts for critical issues"""
        alerts = []

        for worker in workers:
            # Critical low productivity
            if worker['productivity'] < 50:
                alerts.append({
                    'level': 'critical',
                    'worker': worker['worker_name'],
                    'message': f"Critical low productivity: {worker['productivity']:.1f}/100"
                })

            # Very low quality
            if worker['quality'] < 60:
                alerts.append({
                    'level': 'warning',
                    'worker': worker['worker_name'],
                    'message': f"Low quality score: {worker['quality']:.1f}/100"
                })

            # High idle time
            idle_time = worker.get('indices', {}).get('index_2_idle_time', 0) / 3600
            if idle_time > 2:
                alerts.append({
                    'level': 'info',
                    'worker': worker['worker_name'],
                    'message': f"High idle time: {idle_time:.1f} hours"
                })

        return alerts

    async def _store_insights(self, insights: Dict[str, Any]) -> bool:
        """Store insights in knowledge base"""
        try:
            # Store daily summary
            summary_text = f"""Daily Insights for {insights['date']}:
- Low Performers: {len(insights['low_performers'])}
- Top Performers: {len(insights['top_performers'])}
- Alerts: {len(insights['alerts'])}
- Recommendations: {len(insights['recommendations'])}
"""

            self.kb.index_insight(
                insight_type='daily_summary',
                content=summary_text,
                metadata=insights
            )

            return True

        except Exception as e:
            logger.error(f"Failed to store insights: {e}")
            return False

    async def generate_worker_insight(
        self,
        worker_id: str,
        lookback_days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Generate insight for a specific worker

        Args:
            worker_id: Worker ID
            lookback_days: Number of days to analyze

        Returns:
            Worker-specific insights
        """
        try:
            # Search for worker productivity data
            results = self.kb.search_productivity(
                query=f"worker {worker_id} productivity",
                limit=lookback_days,
                worker_id=worker_id
            )

            if not results:
                return None

            # Calculate averages
            productivities = [
                r['payload'].get('overall_productivity', 0)
                for r in results
            ]
            avg_productivity = sum(productivities) / len(productivities)

            # Get latest data
            latest = results[0]['payload']
            current_productivity = latest.get('overall_productivity', 0)

            # Detect trend
            if len(productivities) >= 3:
                recent_avg = sum(productivities[:3]) / 3
                older_avg = sum(productivities[3:]) / len(productivities[3:]) if len(productivities) > 3 else recent_avg

                if recent_avg > older_avg * 1.1:
                    trend = 'improving'
                elif recent_avg < older_avg * 0.9:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'insufficient_data'

            return {
                'worker_id': worker_id,
                'worker_name': latest.get('worker_name'),
                'current_productivity': current_productivity,
                'avg_productivity': avg_productivity,
                'trend': trend,
                'data_points': len(productivities),
                'analyzed_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate worker insight: {e}")
            return None

    def get_stats(self) -> dict:
        """Get insight generator statistics"""
        return {
            'min_productivity_threshold': self.min_productivity,
            'min_efficiency_threshold': self.min_efficiency,
            'ollama_connected': self.ollama is not None,
            'knowledge_base_connected': self.kb is not None
        }
