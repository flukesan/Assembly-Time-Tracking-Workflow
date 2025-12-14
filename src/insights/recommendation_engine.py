"""
Recommendation Engine
Generates actionable recommendations based on worker performance
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates personalized recommendations for workers and shifts
    """

    def __init__(self):
        """Initialize recommendation engine"""
        logger.info("RecommendationEngine initialized")

    def generate_worker_recommendations(
        self,
        worker_name: str,
        indices: Dict[str, float],
        anomalies: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Generate recommendations for a specific worker

        Args:
            worker_name: Worker name
            indices: Productivity indices
            anomalies: Detected anomalies (optional)

        Returns:
            List of recommendations
        """
        recommendations = []

        # Overall productivity
        productivity = indices.get('index_11_overall_productivity', 0)
        if productivity < 60:
            recommendations.append({
                'category': 'overall',
                'priority': 'high',
                'title': 'Critical Productivity Issue',
                'description': f'Overall productivity is {productivity:.1f}/100 (target: 70+)',
                'action': 'Schedule immediate performance review and identify blockers'
            })
        elif productivity < 70:
            recommendations.append({
                'category': 'overall',
                'priority': 'medium',
                'title': 'Below Target Productivity',
                'description': f'Productivity is {productivity:.1f}/100',
                'action': 'Review workflow and provide additional training if needed'
            })

        # Work efficiency
        efficiency = indices.get('index_5_work_efficiency', 0)
        idle_hours = indices.get('index_2_idle_time', 0) / 3600

        if efficiency < 70:
            recommendations.append({
                'category': 'efficiency',
                'priority': 'high',
                'title': 'Low Work Efficiency',
                'description': f'Only {efficiency:.1f}% of time is productive',
                'action': f'Reduce idle time ({idle_hours:.1f}h) by optimizing task assignments'
            })

        if idle_hours > 2:
            recommendations.append({
                'category': 'time_management',
                'priority': 'medium',
                'title': 'Excessive Idle Time',
                'description': f'{idle_hours:.1f} hours of idle time detected',
                'action': 'Investigate causes: waiting for materials, unclear instructions, or equipment issues'
            })

        # Zone transitions
        transitions = indices.get('index_6_zone_transitions', 0)
        if transitions > 20:
            recommendations.append({
                'category': 'workflow',
                'priority': 'medium',
                'title': 'Too Many Zone Changes',
                'description': f'{transitions} zone transitions recorded',
                'action': 'Optimize workstation layout or task batching to reduce movement'
            })
        elif transitions < 3:
            recommendations.append({
                'category': 'workflow',
                'priority': 'low',
                'title': 'Limited Zone Coverage',
                'description': f'Only {transitions} zone transitions',
                'action': 'Consider cross-training for flexibility'
            })

        # Output
        output = indices.get('index_9_output_per_hour', 0)
        if output < 8:
            recommendations.append({
                'category': 'output',
                'priority': 'high',
                'title': 'Low Output Rate',
                'description': f'Output is {output:.2f} units/hour (target: 10+)',
                'action': 'Review process efficiency and remove bottlenecks'
            })

        # Quality
        quality = indices.get('index_10_quality_score', 0)
        if quality < 80:
            recommendations.append({
                'category': 'quality',
                'priority': 'high',
                'title': 'Quality Below Standard',
                'description': f'Quality score is {quality:.1f}/100',
                'action': 'Provide quality training and implement double-check procedures'
            })
        elif quality < 90:
            recommendations.append({
                'category': 'quality',
                'priority': 'medium',
                'title': 'Quality Improvement Opportunity',
                'description': f'Quality score is {quality:.1f}/100',
                'action': 'Focus on attention to detail and quality best practices'
            })

        # Anomaly-based recommendations
        if anomalies and anomalies.get('has_anomalies'):
            for anomaly in anomalies.get('details', []):
                anomaly_type = anomaly['type']
                severity = anomaly['data'].get('severity', 'normal')

                if anomaly_type == 'productivity' and severity in ['critical', 'warning']:
                    recommendations.append({
                        'category': 'anomaly',
                        'priority': 'high',
                        'title': 'Unusual Productivity Pattern',
                        'description': f"Productivity deviated by {anomaly['data'].get('deviation_percent', 0):.1f}%",
                        'action': 'Investigate recent changes in work conditions or personal issues'
                    })

                elif anomaly_type == 'efficiency_drop':
                    recommendations.append({
                        'category': 'anomaly',
                        'priority': 'high',
                        'title': 'Sudden Efficiency Drop',
                        'description': f"Efficiency dropped by {anomaly['data'].get('drop_percent', 0):.1f}%",
                        'action': 'Check equipment, training, or workload changes'
                    })

        # If no recommendations, add positive feedback
        if not recommendations:
            recommendations.append({
                'category': 'recognition',
                'priority': 'info',
                'title': 'Excellent Performance',
                'description': f'{worker_name} is performing well across all metrics',
                'action': 'Continue current practices and consider for mentoring role'
            })

        return recommendations

    def generate_shift_recommendations(
        self,
        shift_name: str,
        shift_stats: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate recommendations for a shift

        Args:
            shift_name: Shift name (morning/afternoon/night)
            shift_stats: Shift statistics

        Returns:
            List of recommendations
        """
        recommendations = []

        avg_productivity = shift_stats.get('avg_productivity', 0)
        total_workers = shift_stats.get('total_workers', 0)
        issues_count = len(shift_stats.get('issues', []))

        # Overall shift performance
        if avg_productivity < 65:
            recommendations.append({
                'category': 'shift_performance',
                'priority': 'high',
                'title': f'{shift_name.title()} Shift Underperforming',
                'description': f'Average productivity: {avg_productivity:.1f}/100',
                'action': 'Conduct shift meeting to identify systemic issues'
            })

        # Low performers ratio
        if issues_count > total_workers * 0.3:
            recommendations.append({
                'category': 'workforce',
                'priority': 'high',
                'title': 'High Number of Low Performers',
                'description': f'{issues_count}/{total_workers} workers need improvement',
                'action': 'Consider shift-wide training or process review'
            })

        # Shift-specific recommendations
        if shift_name == 'night' and avg_productivity < 70:
            recommendations.append({
                'category': 'shift_specific',
                'priority': 'medium',
                'title': 'Night Shift Fatigue',
                'description': 'Night shift showing lower productivity',
                'action': 'Review break schedules and lighting conditions'
            })

        if shift_name == 'morning' and avg_productivity > 80:
            recommendations.append({
                'category': 'recognition',
                'priority': 'info',
                'title': 'Morning Shift Excellence',
                'description': 'Strong performance in morning shift',
                'action': 'Document and share best practices with other shifts'
            })

        return recommendations

    def generate_team_recommendations(
        self,
        team_stats: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate recommendations for the entire team

        Args:
            team_stats: Team-wide statistics

        Returns:
            List of recommendations
        """
        recommendations = []

        total_workers = team_stats.get('total_workers', 0)
        avg_productivity = team_stats.get('avg_productivity', 0)
        top_performers = team_stats.get('top_performers', [])
        low_performers = team_stats.get('low_performers', [])

        # Team productivity
        if avg_productivity < 70:
            recommendations.append({
                'category': 'team',
                'priority': 'high',
                'title': 'Team-Wide Productivity Issue',
                'description': f'Overall team productivity: {avg_productivity:.1f}/100',
                'action': 'Review processes, equipment, and training programs'
            })

        # Skill gap
        if len(low_performers) > 0 and len(top_performers) > 0:
            recommendations.append({
                'category': 'training',
                'priority': 'medium',
                'title': 'Performance Gap Detected',
                'description': f'Gap between top and bottom performers',
                'action': 'Implement mentoring program: pair top performers with those needing support'
            })

        # Recognition
        if len(top_performers) > total_workers * 0.2:
            recommendations.append({
                'category': 'recognition',
                'priority': 'info',
                'title': 'Strong Team Performance',
                'description': f'{len(top_performers)} workers showing excellent results',
                'action': 'Recognize and reward top performers publicly'
            })

        return recommendations

    def prioritize_recommendations(
        self,
        recommendations: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Sort recommendations by priority

        Args:
            recommendations: List of recommendations

        Returns:
            Sorted recommendations (high priority first)
        """
        priority_order = {'high': 0, 'medium': 1, 'low': 2, 'info': 3}

        return sorted(
            recommendations,
            key=lambda x: priority_order.get(x.get('priority', 'low'), 2)
        )

    def format_recommendations_for_display(
        self,
        recommendations: List[Dict[str, str]]
    ) -> str:
        """
        Format recommendations as readable text

        Args:
            recommendations: List of recommendations

        Returns:
            Formatted text
        """
        if not recommendations:
            return "ไม่มีคำแนะนำเพิ่มเติม ผลการทำงานอยู่ในเกณฑ์ดี"

        text = "📋 คำแนะนำ:\n\n"

        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢',
                'info': 'ℹ️'
            }.get(rec.get('priority', 'info'), 'ℹ️')

            text += f"{priority_emoji} {rec['title']}\n"
            text += f"   {rec['description']}\n"
            text += f"   💡 {rec['action']}\n\n"

        return text

    def get_stats(self) -> dict:
        """Get recommendation engine statistics"""
        return {
            'initialized': True
        }
