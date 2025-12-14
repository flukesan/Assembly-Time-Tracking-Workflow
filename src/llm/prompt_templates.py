"""
Prompt Templates for DeepSeek-R1
Bilingual (Thai + English) prompts for various tasks
"""

import json
from typing import Dict, List, Any
from datetime import datetime


class PromptTemplate:
    """
    Prompt templates for assembly line worker analysis
    """

    # System prompts
    SYSTEM_WORKER_ANALYST = """คุณเป็นผู้ช่วยวิเคราะห์ผลการทำงานของพนักงานในโรงงานประกอบ คุณสามารถ:
1. วิเคราะห์ข้อมูล productivity indices ของพนักงาน
2. แนะนำการปรับปรุงประสิทธิภาพการทำงาน
3. เปรียบเทียบผลการทำงานระหว่างพนักงาน
4. สรุปผลการทำงานรายวัน/รายสัปดาห์

ตอบคำถามเป็นภาษาไทยหรือภาษาอังกฤษตามที่ผู้ใช้ถาม โดยให้คำตอบที่กระชับ ชัดเจน และเป็นประโยชน์"""

    SYSTEM_REPORT_GENERATOR = """You are a professional report generator for manufacturing assembly line operations.
You create comprehensive, data-driven reports with:
1. Executive summary
2. Key performance indicators (KPIs)
3. Productivity analysis
4. Recommendations for improvement
5. Supporting data and charts

Format reports in clear, professional Thai or English based on user preference."""

    # Worker analysis prompts
    @staticmethod
    def worker_performance_query(
        worker_name: str,
        indices: Dict[str, float],
        context: str = ""
    ) -> str:
        """
        Generate prompt for worker performance analysis

        Args:
            worker_name: Worker name
            indices: Productivity indices
            context: Additional context

        Returns:
            Formatted prompt
        """
        prompt = f"""วิเคราะห์ผลการทำงานของพนักงาน {worker_name}

ข้อมูล Productivity Indices:
- เวลาทำงานจริง: {indices.get('index_1_active_time', 0)/3600:.2f} ชั่วโมง
- เวลา idle: {indices.get('index_2_idle_time', 0)/3600:.2f} ชั่วโมง
- เวลาพัก: {indices.get('index_3_break_time', 0)/3600:.2f} ชั่วโมง
- ประสิทธิภาพการทำงาน: {indices.get('index_5_work_efficiency', 0):.1f}%
- จำนวนครั้งเปลี่ยนโซน: {indices.get('index_6_zone_transitions', 0)} ครั้ง
- งานที่ทำเสร็จ: {indices.get('index_8_tasks_completed', 0)} งาน
- ผลผลิตต่อชั่วโมง: {indices.get('index_9_output_per_hour', 0):.2f} ชิ้น/ชม
- คะแนนคุณภาพ: {indices.get('index_10_quality_score', 0):.1f}/100
- ประสิทธิภาพโดยรวม: {indices.get('index_11_overall_productivity', 0):.1f}/100

{context if context else ''}

กรุณาวิเคราะห์และให้คำแนะนำเพื่อปรับปรุงประสิทธิภาพการทำงาน"""
        return prompt

    @staticmethod
    def compare_workers(
        workers_data: List[Dict[str, Any]]
    ) -> str:
        """
        Generate prompt for comparing multiple workers

        Args:
            workers_data: List of worker data with indices

        Returns:
            Formatted prompt
        """
        comparison_text = "เปรียบเทียบผลการทำงานของพนักงานต่อไปนี้:\n\n"

        for i, worker in enumerate(workers_data, 1):
            name = worker.get('name', 'Unknown')
            indices = worker.get('indices', {})

            comparison_text += f"""พนักงานคนที่ {i}: {name}
- ประสิทธิภาพโดยรวม: {indices.get('index_11_overall_productivity', 0):.1f}/100
- ประสิทธิภาพการทำงาน: {indices.get('index_5_work_efficiency', 0):.1f}%
- ผลผลิตต่อชั่วโมง: {indices.get('index_9_output_per_hour', 0):.2f} ชิ้น/ชม
- คะแนนคุณภาพ: {indices.get('index_10_quality_score', 0):.1f}/100

"""

        comparison_text += "\nกรุณา:\n"
        comparison_text += "1. จัดอันดับพนักงานตามประสิทธิภาพโดยรวม\n"
        comparison_text += "2. วิเคราะห์จุดแข็งและจุดอ่อนของแต่ละคน\n"
        comparison_text += "3. แนะนำการปรับปรุงสำหรับพนักงานที่มีประสิทธิภาพต่ำ"

        return comparison_text

    @staticmethod
    def shift_summary(
        shift_name: str,
        total_workers: int,
        avg_productivity: float,
        total_output: int,
        issues: List[str] = None
    ) -> str:
        """
        Generate shift summary prompt

        Args:
            shift_name: Shift name (morning/afternoon/night)
            total_workers: Number of workers
            avg_productivity: Average productivity score
            total_output: Total output/tasks completed
            issues: List of issues if any

        Returns:
            Formatted prompt
        """
        shift_thai = {
            'morning': 'กะเช้า',
            'afternoon': 'กะบ่าย',
            'night': 'กะดึก'
        }.get(shift_name, shift_name)

        prompt = f"""สรุปผลการทำงาน{shift_thai}

สถิติโดยรวม:
- จำนวนพนักงาน: {total_workers} คน
- ประสิทธิภาพเฉลี่ย: {avg_productivity:.1f}/100
- ผลผลิตรวม: {total_output} ชิ้น
"""

        if issues:
            prompt += "\nปัญหาที่พบ:\n"
            for issue in issues:
                prompt += f"- {issue}\n"

        prompt += "\nกรุณาสรุปผลการทำงานและให้คำแนะนำสำหรับการปรับปรุง"

        return prompt

    @staticmethod
    def anomaly_detection(
        worker_name: str,
        current_indices: Dict[str, float],
        historical_avg: Dict[str, float]
    ) -> str:
        """
        Generate anomaly detection prompt

        Args:
            worker_name: Worker name
            current_indices: Current productivity indices
            historical_avg: Historical average indices

        Returns:
            Formatted prompt
        """
        prompt = f"""ตรวจจับความผิดปกติในการทำงานของ {worker_name}

ผลการทำงานวันนี้:
- ประสิทธิภาพโดยรวม: {current_indices.get('index_11_overall_productivity', 0):.1f}/100
- ผลผลิตต่อชั่วโมง: {current_indices.get('index_9_output_per_hour', 0):.2f} ชิ้น/ชม
- คะแนนคุณภาพ: {current_indices.get('index_10_quality_score', 0):.1f}/100

ค่าเฉลี่ยในอดีต (30 วันที่ผ่านมา):
- ประสิทธิภาพโดยรวม: {historical_avg.get('index_11_overall_productivity', 0):.1f}/100
- ผลผลิตต่อชั่วโมง: {historical_avg.get('index_9_output_per_hour', 0):.2f} ชิ้น/ชม
- คะแนนคุณภาพ: {historical_avg.get('index_10_quality_score', 0):.1f}/100

กรุณาวิเคราะห์ว่ามีความผิดปกติหรือไม่ และระบุสาเหตุที่เป็นไปได้"""

        return prompt

    @staticmethod
    def productivity_recommendations(
        low_performers: List[Dict[str, Any]],
        best_practices: List[str] = None
    ) -> str:
        """
        Generate productivity improvement recommendations

        Args:
            low_performers: List of workers with low productivity
            best_practices: List of best practices

        Returns:
            Formatted prompt
        """
        prompt = "พนักงานที่ต้องการการปรับปรุง:\n\n"

        for worker in low_performers:
            name = worker.get('name', 'Unknown')
            indices = worker.get('indices', {})
            prompt += f"""- {name}
  ประสิทธิภาพ: {indices.get('index_11_overall_productivity', 0):.1f}/100
  ปัญหาหลัก: {worker.get('main_issue', 'ไม่ระบุ')}

"""

        if best_practices:
            prompt += "\nBest Practices ที่ควรนำมาใช้:\n"
            for practice in best_practices:
                prompt += f"- {practice}\n"

        prompt += "\nกรุณาแนะนำแผนการปรับปรุงสำหรับพนักงานแต่ละคน"

        return prompt

    @staticmethod
    def daily_report(
        date: datetime,
        total_workers: int,
        shifts_data: Dict[str, Dict[str, Any]],
        highlights: List[str] = None
    ) -> str:
        """
        Generate daily report prompt

        Args:
            date: Report date
            total_workers: Total workers
            shifts_data: Data for each shift
            highlights: Key highlights

        Returns:
            Formatted prompt
        """
        date_str = date.strftime('%d/%m/%Y')

        prompt = f"""สร้างรายงานสรุปผลการทำงานประจำวันที่ {date_str}

ข้อมูลโดยรวม:
- จำนวนพนักงานทั้งหมด: {total_workers} คน

"""

        for shift_name, shift_data in shifts_data.items():
            shift_thai = {
                'morning': 'กะเช้า',
                'afternoon': 'กะบ่าย',
                'night': 'กะดึก'
            }.get(shift_name, shift_name)

            prompt += f"""{shift_thai}:
- พนักงาน: {shift_data.get('workers', 0)} คน
- ประสิทธิภาพเฉลี่ย: {shift_data.get('avg_productivity', 0):.1f}/100
- ผลผลิต: {shift_data.get('total_output', 0)} ชิ้น

"""

        if highlights:
            prompt += "\nจุดเด่นวันนี้:\n"
            for highlight in highlights:
                prompt += f"- {highlight}\n"

        prompt += """\nกรุณาสร้างรายงานที่ประกอบด้วย:
1. สรุปผลการทำงานโดยรวม
2. การเปรียบเทียบระหว่างกะ
3. พนักงานที่มีผลงานดีเด่น
4. ปัญหาที่พบและแนวทางแก้ไข
5. คำแนะนำสำหรับวันพรุ่งนี้"""

        return prompt

    @staticmethod
    def natural_language_query(
        question: str,
        context_data: Dict[str, Any]
    ) -> str:
        """
        Process natural language query with context

        Args:
            question: User's question
            context_data: Relevant context data from RAG

        Returns:
            Formatted prompt with context
        """
        prompt = f"""คำถาม: {question}

ข้อมูลที่เกี่ยวข้อง:
{json.dumps(context_data, ensure_ascii=False, indent=2)}

กรุณาตอบคำถามโดยใช้ข้อมูลที่ให้มา ตอบเป็นภาษาเดียวกับคำถาม"""

        return prompt
