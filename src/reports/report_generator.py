"""
Report Generator
Generates comprehensive reports using AI and data analytics
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from llm.ollama_client import OllamaClient, ChatMessage
from llm.prompt_templates import PromptTemplate
from rag.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates various types of reports:
    - Daily summaries
    - Weekly performance reports
    - Monthly analytics
    - Shift comparisons
    - Worker performance reports
    """

    def __init__(
        self,
        ollama_client: OllamaClient,
        knowledge_base: KnowledgeBase
    ):
        """
        Initialize report generator

        Args:
            ollama_client: Ollama client for AI
            knowledge_base: Knowledge base for data
        """
        self.ollama = ollama_client
        self.kb = knowledge_base

        logger.info("ReportGenerator initialized")

    async def generate_daily_report(
        self,
        date: Optional[datetime] = None,
        language: str = "th"
    ) -> Dict[str, Any]:
        """
        Generate daily performance report

        Args:
            date: Report date (default: today)
            language: Report language (th/en)

        Returns:
            Daily report with AI-generated summary
        """
        date = date or datetime.now()
        date_str = date.strftime('%Y-%m-%d')

        logger.info(f"Generating daily report for {date_str}")

        report = {
            'type': 'daily',
            'date': date_str,
            'generated_at': datetime.now().isoformat(),
            'language': language,
            'summary': None,
            'statistics': {},
            'shifts': {},
            'top_performers': [],
            'issues': [],
            'recommendations': []
        }

        try:
            # Get productivity data for the date
            query = f"productivity performance on {date_str}"
            results = self.kb.search_productivity(query, limit=100)

            if not results:
                logger.warning(f"No data found for {date_str}")
                report['summary'] = "ไม่มีข้อมูลสำหรับวันนี้" if language == "th" else "No data available for this date"
                return report

            # Calculate statistics
            workers_data = []
            shifts_data = {'morning': [], 'afternoon': [], 'night': [], 'flexible': []}

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
                    'tasks': indices.get('index_8_tasks_completed', 0)
                }

                workers_data.append(worker_data)

                shift = payload.get('shift', 'flexible')
                if shift in shifts_data:
                    shifts_data[shift].append(worker_data)

            # Overall statistics
            total_workers = len(workers_data)
            avg_productivity = sum(w['productivity'] for w in workers_data) / total_workers if total_workers > 0 else 0
            total_output = sum(w['tasks'] for w in workers_data)
            avg_quality = sum(w['quality'] for w in workers_data) / total_workers if total_workers > 0 else 0

            report['statistics'] = {
                'total_workers': total_workers,
                'avg_productivity': round(avg_productivity, 2),
                'total_output': total_output,
                'avg_quality': round(avg_quality, 2)
            }

            # Process shifts
            for shift_name, shift_workers in shifts_data.items():
                if shift_workers:
                    shift_avg_productivity = sum(w['productivity'] for w in shift_workers) / len(shift_workers)
                    shift_total_output = sum(w['tasks'] for w in shift_workers)

                    report['shifts'][shift_name] = {
                        'workers': len(shift_workers),
                        'avg_productivity': round(shift_avg_productivity, 2),
                        'total_output': shift_total_output
                    }

            # Top performers
            sorted_workers = sorted(workers_data, key=lambda x: x['productivity'], reverse=True)
            report['top_performers'] = [
                {
                    'name': w['worker_name'],
                    'productivity': w['productivity'],
                    'output': w['tasks']
                }
                for w in sorted_workers[:5]
            ]

            # Identify issues
            for worker in workers_data:
                if worker['productivity'] < 60:
                    report['issues'].append(
                        f"พนักงาน {worker['worker_name']}: ประสิทธิภาพต่ำ ({worker['productivity']:.1f}/100)" if language == "th" else
                        f"Worker {worker['worker_name']}: Low productivity ({worker['productivity']:.1f}/100)"
                    )

            # Generate AI summary using DeepSeek-R1
            highlights = [
                f"Total output: {total_output} tasks completed",
                f"Average productivity: {avg_productivity:.1f}/100"
            ]

            if report['top_performers']:
                highlights.append(f"Top performer: {report['top_performers'][0]['name']}")

            prompt = PromptTemplate.daily_report(
                date=date,
                total_workers=total_workers,
                shifts_data=report['shifts'],
                highlights=highlights
            )

            messages = [
                ChatMessage(role="system", content=PromptTemplate.SYSTEM_REPORT_GENERATOR),
                ChatMessage(role="user", content=prompt)
            ]

            response = await self.ollama.chat(messages=messages, temperature=0.7, show_reasoning=False)

            report['summary'] = response.content
            report['ai_model'] = response.model

            logger.info(f"Daily report generated for {date_str}")

        except Exception as e:
            logger.error(f"Failed to generate daily report: {e}")
            report['error'] = str(e)

        return report

    async def generate_weekly_report(
        self,
        start_date: Optional[datetime] = None,
        language: str = "th"
    ) -> Dict[str, Any]:
        """
        Generate weekly performance report

        Args:
            start_date: Week start date (default: last Monday)
            language: Report language

        Returns:
            Weekly report
        """
        if start_date is None:
            today = datetime.now()
            start_date = today - timedelta(days=today.weekday())

        end_date = start_date + timedelta(days=6)

        logger.info(f"Generating weekly report for {start_date.date()} to {end_date.date()}")

        report = {
            'type': 'weekly',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'language': language,
            'summary': None,
            'daily_stats': {},
            'weekly_totals': {},
            'trends': {},
            'recommendations': []
        }

        try:
            # Collect data for each day
            current_date = start_date
            all_productivities = []
            total_output = 0
            total_workers_set = set()

            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                results = self.kb.search_productivity(
                    query=f"productivity on {date_str}",
                    limit=50
                )

                day_productivities = []
                day_output = 0

                for result in results:
                    payload = result['payload']
                    indices = payload.get('indices', {})

                    productivity = indices.get('index_11_overall_productivity', 0)
                    day_productivities.append(productivity)
                    all_productivities.append(productivity)

                    day_output += indices.get('index_8_tasks_completed', 0)
                    total_workers_set.add(payload.get('worker_id'))

                total_output += day_output

                if day_productivities:
                    report['daily_stats'][date_str] = {
                        'avg_productivity': round(sum(day_productivities) / len(day_productivities), 2),
                        'total_output': day_output,
                        'workers': len(day_productivities)
                    }

                current_date += timedelta(days=1)

            # Weekly totals
            avg_weekly_productivity = sum(all_productivities) / len(all_productivities) if all_productivities else 0

            report['weekly_totals'] = {
                'total_workers': len(total_workers_set),
                'avg_productivity': round(avg_weekly_productivity, 2),
                'total_output': total_output,
                'working_days': len(report['daily_stats'])
            }

            # Analyze trends
            if len(report['daily_stats']) >= 3:
                daily_avgs = [stats['avg_productivity'] for stats in report['daily_stats'].values()]
                first_half = sum(daily_avgs[:len(daily_avgs)//2]) / (len(daily_avgs)//2)
                second_half = sum(daily_avgs[len(daily_avgs)//2:]) / (len(daily_avgs) - len(daily_avgs)//2)

                if second_half > first_half * 1.05:
                    trend = 'improving' if language == "en" else 'กำลังดีขึ้น'
                elif second_half < first_half * 0.95:
                    trend = 'declining' if language == "en" else 'กำลังลดลง'
                else:
                    trend = 'stable' if language == "en" else 'มีเสถียรภาพ'

                report['trends']['productivity'] = trend

            # Generate summary
            summary_text = f"""สรุปผลการทำงานสัปดาห์ที่ {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}:

ผลงานโดยรวม:
- พนักงานทั้งหมด: {len(total_workers_set)} คน
- ประสิทธิภาพเฉลี่ย: {avg_weekly_productivity:.1f}/100
- ผลผลิตรวม: {total_output} งาน
- วันทำงาน: {len(report['daily_stats'])} วัน

แนวโน้ม: {report['trends'].get('productivity', 'N/A')}

กรุณาวิเคราะห์และให้คำแนะนำสำหรับสัปดาห์หน้า""" if language == "th" else f"""Weekly Summary for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:

Overall Performance:
- Total Workers: {len(total_workers_set)}
- Average Productivity: {avg_weekly_productivity:.1f}/100
- Total Output: {total_output} tasks
- Working Days: {len(report['daily_stats'])}

Trend: {report['trends'].get('productivity', 'N/A')}

Please analyze and provide recommendations for next week"""

            messages = [
                ChatMessage(role="system", content=PromptTemplate.SYSTEM_REPORT_GENERATOR),
                ChatMessage(role="user", content=summary_text)
            ]

            response = await self.ollama.chat(messages=messages, temperature=0.7, show_reasoning=False)
            report['summary'] = response.content

            logger.info("Weekly report generated successfully")

        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            report['error'] = str(e)

        return report

    async def generate_worker_report(
        self,
        worker_id: str,
        days: int = 30,
        language: str = "th"
    ) -> Dict[str, Any]:
        """
        Generate individual worker performance report

        Args:
            worker_id: Worker ID
            days: Number of days to analyze
            language: Report language

        Returns:
            Worker performance report
        """
        logger.info(f"Generating worker report for {worker_id} ({days} days)")

        report = {
            'type': 'worker',
            'worker_id': worker_id,
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'language': language,
            'worker_info': {},
            'performance_summary': {},
            'trends': {},
            'analysis': None
        }

        try:
            # Get worker productivity data
            results = self.kb.search_productivity(
                query=f"worker {worker_id} productivity performance",
                limit=days,
                worker_id=worker_id
            )

            if not results:
                report['analysis'] = "ไม่พบข้อมูลพนักงาน" if language == "th" else "No worker data found"
                return report

            # Extract data
            latest = results[0]['payload']
            report['worker_info'] = {
                'name': latest.get('worker_name'),
                'shift': latest.get('shift')
            }

            productivities = []
            efficiencies = []
            outputs = []
            qualities = []

            for result in results:
                indices = result['payload'].get('indices', {})
                productivities.append(indices.get('index_11_overall_productivity', 0))
                efficiencies.append(indices.get('index_5_work_efficiency', 0))
                outputs.append(indices.get('index_9_output_per_hour', 0))
                qualities.append(indices.get('index_10_quality_score', 0))

            # Calculate averages
            report['performance_summary'] = {
                'avg_productivity': round(sum(productivities) / len(productivities), 2) if productivities else 0,
                'avg_efficiency': round(sum(efficiencies) / len(efficiencies), 2) if efficiencies else 0,
                'avg_output': round(sum(outputs) / len(outputs), 2) if outputs else 0,
                'avg_quality': round(sum(qualities) / len(qualities), 2) if qualities else 0,
                'data_points': len(productivities)
            }

            # Analyze trends
            if len(productivities) >= 7:
                recent = sum(productivities[:7]) / 7
                older = sum(productivities[7:]) / (len(productivities) - 7)

                if recent > older * 1.1:
                    trend = 'improving' if language == "en" else 'ดีขึ้น'
                elif recent < older * 0.9:
                    trend = 'declining' if language == "en" else 'ลดลง'
                else:
                    trend = 'stable' if language == "en" else 'คงที่'

                report['trends']['productivity'] = trend

            # Generate AI analysis
            prompt = PromptTemplate.worker_performance_query(
                worker_name=report['worker_info']['name'],
                indices=latest.get('indices', {}),
                context=f"This is a {days}-day performance report. Average productivity: {report['performance_summary']['avg_productivity']:.1f}/100. Trend: {report['trends'].get('productivity', 'N/A')}."
            )

            messages = [
                ChatMessage(role="system", content=PromptTemplate.SYSTEM_WORKER_ANALYST),
                ChatMessage(role="user", content=prompt)
            ]

            response = await self.ollama.chat(messages=messages, temperature=0.7, show_reasoning=False)
            report['analysis'] = response.content

            logger.info(f"Worker report generated for {worker_id}")

        except Exception as e:
            logger.error(f"Failed to generate worker report: {e}")
            report['error'] = str(e)

        return report

    def format_report_as_text(self, report: Dict[str, Any]) -> str:
        """
        Format report as readable text

        Args:
            report: Report dictionary

        Returns:
            Formatted text report
        """
        report_type = report.get('type', 'unknown')

        if report_type == 'daily':
            return self._format_daily_report(report)
        elif report_type == 'weekly':
            return self._format_weekly_report(report)
        elif report_type == 'worker':
            return self._format_worker_report(report)
        else:
            return json.dumps(report, indent=2, ensure_ascii=False)

    def _format_daily_report(self, report: Dict[str, Any]) -> str:
        """Format daily report as text"""
        text = f"📊 รายงานประจำวัน {report['date']}\n"
        text += "=" * 60 + "\n\n"

        stats = report.get('statistics', {})
        text += f"📈 สถิติโดยรวม:\n"
        text += f"   พนักงานทั้งหมด: {stats.get('total_workers', 0)} คน\n"
        text += f"   ประสิทธิภาพเฉลี่ย: {stats.get('avg_productivity', 0):.1f}/100\n"
        text += f"   ผลผลิตรวม: {stats.get('total_output', 0)} งาน\n"
        text += f"   คะแนนคุณภาพเฉลี่ย: {stats.get('avg_quality', 0):.1f}/100\n\n"

        if report.get('shifts'):
            text += "🕐 รายงานแต่ละกะ:\n"
            for shift_name, shift_data in report['shifts'].items():
                text += f"   {shift_name}: {shift_data['workers']} คน, ประสิทธิภาพ {shift_data['avg_productivity']:.1f}/100\n"
            text += "\n"

        if report.get('top_performers'):
            text += "⭐ พนักงานที่มีผลงานดีเด่น:\n"
            for i, performer in enumerate(report['top_performers'], 1):
                text += f"   {i}. {performer['name']}: {performer['productivity']:.1f}/100\n"
            text += "\n"

        if report.get('summary'):
            text += "💡 สรุปและคำแนะนำจาก AI:\n"
            text += report['summary'] + "\n"

        return text

    def _format_weekly_report(self, report: Dict[str, Any]) -> str:
        """Format weekly report as text"""
        text = f"📊 รายงานสรุปประจำสัปดาห์\n"
        text += f"📅 {report['start_date']} ถึง {report['end_date']}\n"
        text += "=" * 60 + "\n\n"

        totals = report.get('weekly_totals', {})
        text += f"📈 สถิติรวมสัปดาห์:\n"
        text += f"   พนักงานทั้งหมด: {totals.get('total_workers', 0)} คน\n"
        text += f"   ประสิทธิภาพเฉลี่ย: {totals.get('avg_productivity', 0):.1f}/100\n"
        text += f"   ผลผลิตรวม: {totals.get('total_output', 0)} งาน\n"
        text += f"   วันทำงาน: {totals.get('working_days', 0)} วัน\n\n"

        if report.get('trends'):
            text += f"📊 แนวโน้ม: {report['trends'].get('productivity', 'N/A')}\n\n"

        if report.get('summary'):
            text += "💡 วิเคราะห์และคำแนะนำจาก AI:\n"
            text += report['summary'] + "\n"

        return text

    def _format_worker_report(self, report: Dict[str, Any]) -> str:
        """Format worker report as text"""
        worker_info = report.get('worker_info', {})
        text = f"👤 รายงานผลการทำงานของพนักงาน\n"
        text += f"ชื่อ: {worker_info.get('name', 'N/A')}\n"
        text += f"กะ: {worker_info.get('shift', 'N/A')}\n"
        text += f"ระยะเวลา: {report.get('period_days', 0)} วัน\n"
        text += "=" * 60 + "\n\n"

        summary = report.get('performance_summary', {})
        text += f"📈 สรุปผลการทำงาน:\n"
        text += f"   ประสิทธิภาพเฉลี่ย: {summary.get('avg_productivity', 0):.1f}/100\n"
        text += f"   ประสิทธิภาพการทำงาน: {summary.get('avg_efficiency', 0):.1f}%\n"
        text += f"   ผลผลิตเฉลี่ย: {summary.get('avg_output', 0):.2f} ชิ้น/ชม\n"
        text += f"   คะแนนคุณภาพเฉลี่ย: {summary.get('avg_quality', 0):.1f}/100\n\n"

        if report.get('trends'):
            text += f"📊 แนวโน้ม: {report['trends'].get('productivity', 'N/A')}\n\n"

        if report.get('analysis'):
            text += "💡 การวิเคราะห์จาก AI:\n"
            text += report['analysis'] + "\n"

        return text

    def get_stats(self) -> dict:
        """Get report generator statistics"""
        return {
            'ollama_connected': self.ollama is not None,
            'knowledge_base_connected': self.kb is not None
        }
