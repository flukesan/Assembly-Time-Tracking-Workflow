# RAG + DeepSeek-R1 Integration Architecture

## 🔍 Overview

This system combines **Retrieval-Augmented Generation (RAG)** with **DeepSeek-R1:14B** for intelligent analysis and question-answering about assembly line operations.

### Key Features
- **Bilingual Support**: Thai + English queries and responses
- **Reasoning Chain**: Show step-by-step thinking process
- **OpenAI-Compatible API**: Easy integration via Ollama
- **Multi-Source Retrieval**: PostgreSQL + Qdrant vector search
- **Context-Aware**: Real-time data + historical patterns

---

## 🏗️ RAG Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER QUERY INPUT                                │
│  (Thai/English natural language question)                           │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: Query Analysis & Intent Detection                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • Language detection (langdetect)                           │   │
│  │ • Intent classification (question/command/analysis)         │   │
│  │ • Entity extraction (worker_id, zone_id, date, time)        │   │
│  │ • Query rewriting (if needed)                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: Query Routing (Determine data sources)                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ IF: Real-time query ("what's happening now?")               │   │
│  │   → Route to: Redis + PostgreSQL (last 1 hour)             │   │
│  │                                                             │   │
│  │ IF: Historical query ("what happened yesterday?")           │   │
│  │   → Route to: PostgreSQL + Qdrant                          │   │
│  │                                                             │   │
│  │ IF: Knowledge query ("how to fix X?")                      │   │
│  │   → Route to: Qdrant (knowledge_base, anomaly_patterns)    │   │
│  │                                                             │   │
│  │ IF: Comparative query ("compare zone A vs B")              │   │
│  │   → Route to: PostgreSQL aggregations + Qdrant patterns    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│  STEP 3A:           │         │  STEP 3B:           │
│  Vector Search      │         │  SQL Query          │
│  (Qdrant)           │         │  (PostgreSQL/Redis) │
├─────────────────────┤         ├─────────────────────┤
│ • Generate query    │         │ • Build SQL query   │
│   embedding         │         │ • Apply filters     │
│ • Search 5          │         │ • Aggregate data    │
│   collections       │         │ • Join tables       │
│ • Hybrid filtering  │         │ • Get real-time     │
│ • Top-k=5 results   │         │   stats             │
└──────────┬──────────┘         └──────────┬──────────┘
           │                               │
           └───────────────┬───────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: Context Assembly                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Combine retrieved contexts:                                 │   │
│  │ • Vector search results (5 documents)                       │   │
│  │ • SQL query results (metrics, sessions, anomalies)          │   │
│  │ • System status (current index, active workers)             │   │
│  │                                                             │   │
│  │ Rank by relevance:                                          │   │
│  │ • Semantic similarity score (Qdrant)                        │   │
│  │ • Temporal relevance (recent > old)                         │   │
│  │ • Source priority (PostgreSQL > Qdrant for facts)          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: Prompt Engineering                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Build structured prompt:                                    │   │
│  │                                                             │   │
│  │ [SYSTEM ROLE]                                               │   │
│  │ You are an expert manufacturing analyst...                  │   │
│  │                                                             │   │
│  │ [CURRENT CONTEXT] (from PostgreSQL/Redis)                   │   │
│  │ - Current index: 5/11                                       │   │
│  │ - Zone Z01: 2 workers, 92% active                          │   │
│  │ - Recent anomaly: High idle time in Z02                    │   │
│  │                                                             │   │
│  │ [HISTORICAL CONTEXT] (from Qdrant)                          │   │
│  │ - Similar incident on 2025-01-10: Parts delay              │   │
│  │ - Resolution: Buffer stock system                          │   │
│  │                                                             │   │
│  │ [USER QUESTION]                                             │   │
│  │ ทำไม zone Z01 วันนี้ทำงานช้ากว่าปกติ?                      │   │
│  │                                                             │   │
│  │ [INSTRUCTIONS]                                              │   │
│  │ - Analyze using provided context                            │   │
│  │ - Show your reasoning process                              │   │
│  │ - Cite sources                                             │   │
│  │ - Provide actionable recommendations                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 6: LLM Inference (DeepSeek-R1:14B via Ollama)                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ POST http://localhost:11434/v1/chat/completions            │   │
│  │                                                             │   │
│  │ {                                                           │   │
│  │   "model": "deepseek-r1:14b",                              │   │
│  │   "messages": [                                             │   │
│  │     {"role": "system", "content": "..."},                  │   │
│  │     {"role": "user", "content": "..."}                     │   │
│  │   ],                                                        │   │
│  │   "temperature": 0.7,                                       │   │
│  │   "stream": true,  // Stream response                      │   │
│  │   "max_tokens": 2000                                        │   │
│  │ }                                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 7: Response Post-Processing                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • Extract reasoning chain (DeepSeek-R1 specific)            │   │
│  │ • Parse final answer                                        │   │
│  │ • Add source citations                                      │   │
│  │ • Format for UI (markdown, charts, etc.)                   │   │
│  │ • Log query & response for feedback loop                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RETURN TO USER                                  │
│  • Reasoning steps (collapsible)                                   │
│  • Final answer                                                    │
│  • Source citations (clickable links)                              │
│  • Recommendations (action items)                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Component Design

### 1. Query Analyzer

```python
# src/rag/query_analyzer.py

from langdetect import detect
import re
from typing import Dict, List

class QueryAnalyzer:
    def __init__(self):
        self.intent_patterns = {
            'real_time': [
                r'ตอนนี้|now|current|real.?time|กำลัง',
                r'what.*happening|เกิดอะไรขึ้น'
            ],
            'historical': [
                r'yesterday|เมื่อวาน|last week|สัปดาห์ที่แล้ว',
                r'past|ก่อนหน้า|history|ประวัติ'
            ],
            'comparison': [
                r'compare|เปรียบเทียบ|vs|กับ',
                r'difference|ความแตกต่าง|better|worse'
            ],
            'troubleshooting': [
                r'why|ทำไม|problem|ปัญหา|issue',
                r'slow|ช้า|error|ผิดพลาด|fix|แก้ไข'
            ],
            'how_to': [
                r'how to|วิธีการ|steps|ขั้นตอน',
                r'procedure|กระบวนการ|process'
            ]
        }

        self.entity_patterns = {
            'worker_id': r'W\d{3}|worker[ _]?\d+|พนักงาน[ _]?\d+',
            'zone_id': r'Z\d{2}|zone[ _]?\d+|สถานี[ _]?\d+',
            'index_number': r'index[ _]?\d+|ตาราง[ _]?\d+',
            'date': r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}'
        }

    def analyze(self, query: str) -> Dict:
        """Analyze user query and extract metadata"""
        # Detect language
        try:
            language = detect(query)
        except:
            language = 'th'  # Default to Thai

        # Detect intent
        intent = self._detect_intent(query)

        # Extract entities
        entities = self._extract_entities(query)

        # Suggest query rewrite if needed
        rewritten_query = self._rewrite_query(query, language)

        return {
            'original_query': query,
            'language': language,
            'intent': intent,
            'entities': entities,
            'rewritten_query': rewritten_query,
            'requires_real_time': intent == 'real_time',
            'requires_vector_search': intent in ['troubleshooting', 'how_to'],
            'requires_sql': True  # Almost always need SQL for facts
        }

    def _detect_intent(self, query: str) -> str:
        """Classify query intent"""
        query_lower = query.lower()

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent

        return 'general'  # Default

    def _extract_entities(self, query: str) -> Dict:
        """Extract named entities from query"""
        entities = {}

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches[0]

        return entities

    def _rewrite_query(self, query: str, language: str) -> str:
        """Optionally rewrite query for better retrieval"""
        # Example: Expand abbreviations, fix typos, etc.
        # For now, return original
        return query
```

---

### 2. Query Router

```python
# src/rag/query_router.py

from typing import Dict, List

class QueryRouter:
    def __init__(self, postgres_manager, qdrant_manager, redis_manager):
        self.postgres = postgres_manager
        self.qdrant = qdrant_manager
        self.redis = redis_manager

    def route(self, query_analysis: Dict) -> Dict:
        """Determine which data sources to query"""
        sources = {
            'redis': False,
            'postgresql': False,
            'qdrant': False,
            'qdrant_collections': []
        }

        intent = query_analysis['intent']
        entities = query_analysis['entities']

        # Real-time queries → Redis
        if query_analysis['requires_real_time']:
            sources['redis'] = True

        # Always query PostgreSQL for facts
        if query_analysis['requires_sql']:
            sources['postgresql'] = True

        # Vector search for knowledge/troubleshooting
        if query_analysis['requires_vector_search']:
            sources['qdrant'] = True

            # Select relevant collections based on intent
            if intent == 'troubleshooting':
                sources['qdrant_collections'] = [
                    'anomaly_patterns',
                    'incident_reports',
                    'work_sequences'
                ]
            elif intent == 'how_to':
                sources['qdrant_collections'] = [
                    'knowledge_base',
                    'work_sequences'
                ]
            elif intent == 'comparison':
                sources['qdrant_collections'] = [
                    'worker_behaviors',
                    'work_sequences'
                ]
            else:
                # Default: Search all collections
                sources['qdrant_collections'] = [
                    'work_sequences',
                    'anomaly_patterns',
                    'knowledge_base',
                    'worker_behaviors',
                    'incident_reports'
                ]

        return sources
```

---

### 3. Retriever

```python
# src/rag/retriever.py

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from typing import List, Dict
import hashlib
import pickle

class Retriever:
    def __init__(self, qdrant_client, postgres_manager, redis_manager, embedding_model):
        self.qdrant = qdrant_client
        self.postgres = postgres_manager
        self.redis = redis_manager
        self.embedding_model = embedding_model

    def retrieve_vector(self, query: str, collections: List[str], top_k=5, filters=None) -> List[Dict]:
        """Retrieve relevant documents from Qdrant"""
        # Check embedding cache first
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cached_embedding = self.redis.get(f"embedding:cache:{query_hash}")

        if cached_embedding:
            query_vector = pickle.loads(cached_embedding)
        else:
            # Generate embedding
            query_vector = self.embedding_model.encode(query)
            # Cache it
            self.redis.set(
                f"embedding:cache:{query_hash}",
                pickle.dumps(query_vector),
                ex=3600
            )

        # Search across multiple collections
        all_results = []
        for collection_name in collections:
            try:
                results = self.qdrant.search(
                    collection_name=collection_name,
                    query_vector=query_vector.tolist(),
                    limit=top_k,
                    query_filter=filters,
                    score_threshold=0.7  # Only high-relevance results
                )

                for result in results:
                    all_results.append({
                        'collection': collection_name,
                        'score': result.score,
                        'payload': result.payload
                    })
            except Exception as e:
                print(f"Error searching {collection_name}: {e}")

        # Sort by score
        all_results.sort(key=lambda x: x['score'], reverse=True)

        # Return top-k across all collections
        return all_results[:top_k]

    def retrieve_sql(self, query_analysis: Dict) -> Dict:
        """Retrieve data from PostgreSQL based on query analysis"""
        entities = query_analysis['entities']
        intent = query_analysis['intent']

        results = {}

        # Real-time stats (from Redis first, then PostgreSQL)
        if query_analysis['requires_real_time']:
            results['current_index'] = self.redis.get_current_index()
            results['active_sessions'] = self._get_active_sessions()

        # Historical data
        if 'zone_id' in entities:
            zone_id = entities['zone_id']
            results['zone_stats'] = self._get_zone_stats(zone_id)
            results['zone_anomalies'] = self._get_zone_anomalies(zone_id)

        if 'worker_id' in entities:
            worker_id = entities['worker_id']
            results['worker_stats'] = self._get_worker_stats(worker_id)

        # Date-based queries
        if 'date' in entities:
            date = entities['date']
            results['index_records'] = self._get_index_records(date)

        return results

    def _get_active_sessions(self) -> List[Dict]:
        """Get all active sessions from Redis"""
        session_ids = self.redis.client.smembers("sessions:active:all")
        sessions = []
        for session_id in session_ids:
            session = self.redis.get_session(session_id)
            if session:
                sessions.append(session)
        return sessions

    def _get_zone_stats(self, zone_id: str, hours=24) -> Dict:
        """Get zone statistics from PostgreSQL"""
        query = """
        SELECT
            zone_id,
            COUNT(DISTINCT worker_id) as unique_workers,
            SUM(active_duration_seconds) as total_active,
            SUM(idle_duration_seconds) as total_idle,
            AVG(motion_score) as avg_motion
        FROM time_logs
        WHERE zone_id = %s
          AND timestamp > NOW() - INTERVAL '%s hours'
        GROUP BY zone_id
        """
        return self.postgres.execute_one(query, (zone_id, hours))

    def _get_zone_anomalies(self, zone_id: str, limit=10) -> List[Dict]:
        """Get recent anomalies for zone"""
        query = """
        SELECT *
        FROM anomalies
        WHERE zone_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        return self.postgres.execute_all(query, (zone_id, limit))

    def _get_worker_stats(self, worker_id: str, days=7) -> Dict:
        """Get worker statistics"""
        query = """
        SELECT
            worker_id,
            SUM(active_duration_seconds) as total_active,
            SUM(idle_duration_seconds) as total_idle,
            COUNT(DISTINCT DATE(timestamp)) as days_worked,
            AVG(motion_score) as avg_motion
        FROM time_logs
        WHERE worker_id = %s
          AND timestamp > CURRENT_DATE - INTERVAL '%s days'
        GROUP BY worker_id
        """
        return self.postgres.execute_one(query, (worker_id, days))

    def _get_index_records(self, date: str) -> List[Dict]:
        """Get index records for specific date"""
        query = """
        SELECT *
        FROM index_records
        WHERE date = %s
        ORDER BY index_number
        """
        return self.postgres.execute_all(query, (date,))
```

---

### 4. Prompt Builder

```python
# src/rag/prompt_builder.py

from typing import Dict, List
from datetime import datetime

class PromptBuilder:
    def __init__(self, language='th'):
        self.language = language

    def build_prompt(self, query: str, query_analysis: Dict, vector_results: List[Dict], sql_results: Dict) -> List[Dict]:
        """Build structured prompt for DeepSeek-R1"""

        # System message (bilingual)
        system_message = self._get_system_message()

        # Assemble context sections
        current_context = self._format_current_context(sql_results)
        historical_context = self._format_historical_context(vector_results)
        instructions = self._get_instructions()

        # Build user message
        user_message = f"""
# ข้อมูลปัจจุบัน (Current Context)
{current_context}

# ข้อมูลในอดีต (Historical Context)
{historical_context}

# คำถามจากผู้ใช้ (User Question)
{query}

# คำแนะนำ (Instructions)
{instructions}
"""

        # Return OpenAI-compatible messages format
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

    def _get_system_message(self) -> str:
        """System role definition (bilingual)"""
        if self.language == 'th':
            return """คุณคือผู้เชี่ยวชาญด้านการผลิตและการวิเคราะห์สายการผลิต (Manufacturing and Assembly Line Expert)

ความสามารถของคุณ:
- วิเคราะห์ข้อมูลการผลิตจากระบบ time-tracking
- ระบุปัญหาและอธิบายสาเหตุ (root cause analysis)
- แนะนำวิธีแก้ไขและปรับปรุง (recommendations)
- เปรียบเทียบประสิทธิภาพระหว่างโซน พนักงาน หรือช่วงเวลา
- ตอบคำถามเป็นภาษาไทยที่เข้าใจง่าย ชัดเจน และมีประโยชน์

หลักการทำงาน:
1. แสดงกระบวนการคิด (reasoning) ทีละขั้นตอน
2. อ้างอิงข้อมูลจากบริบทที่ให้มา (cite sources)
3. ให้คำตอบที่แม่นยำและสามารถนำไปปฏิบัติได้
4. ถ้าไม่มีข้อมูลเพียงพอ ให้บอกตรงๆ และแนะนำว่าต้องการข้อมูลอะไรเพิ่ม"""
        else:
            return """You are a Manufacturing and Assembly Line Expert specialized in production analytics and time-tracking systems.

Your capabilities:
- Analyze production data from time-tracking systems
- Identify issues and explain root causes
- Provide actionable recommendations for improvement
- Compare performance across zones, workers, or time periods
- Answer questions clearly and professionally in English

Working principles:
1. Show your reasoning process step-by-step
2. Cite sources from provided context
3. Give accurate and actionable answers
4. If insufficient data, be honest and suggest what additional data is needed"""

    def _format_current_context(self, sql_results: Dict) -> str:
        """Format real-time context from SQL results"""
        context_parts = []

        if 'current_index' in sql_results:
            context_parts.append(f"- ตอนนี้อยู่ Index: {sql_results['current_index']}/11")

        if 'active_sessions' in sql_results:
            sessions = sql_results['active_sessions']
            context_parts.append(f"- พนักงานที่กำลังทำงาน: {len(sessions)} คน")

            # Group by zone
            zones = {}
            for session in sessions:
                zone_id = session.get('zone_id', 'unknown')
                zones[zone_id] = zones.get(zone_id, 0) + 1

            for zone_id, count in zones.items():
                context_parts.append(f"  - Zone {zone_id}: {count} คน")

        if 'zone_stats' in sql_results:
            stats = sql_results['zone_stats']
            if stats:
                total_seconds = int(stats.get('total_active', 0)) + int(stats.get('total_idle', 0))
                productivity = int(stats.get('total_active', 0)) / total_seconds * 100 if total_seconds > 0 else 0
                context_parts.append(f"- สถิติ Zone {stats.get('zone_id')}: ประสิทธิภาพ {productivity:.1f}%")

        if not context_parts:
            context_parts.append("- ไม่มีข้อมูล real-time ในขณะนี้")

        return "\n".join(context_parts)

    def _format_historical_context(self, vector_results: List[Dict]) -> str:
        """Format historical context from vector search"""
        if not vector_results:
            return "- ไม่พบข้อมูลในอดีตที่เกี่ยวข้อง"

        context_parts = []
        for i, result in enumerate(vector_results[:3], 1):  # Top 3 only
            collection = result['collection']
            score = result['score']
            payload = result['payload']

            # Format based on collection type
            if collection == 'anomaly_patterns':
                desc = payload.get('description', 'N/A')
                root_cause = payload.get('root_cause', 'N/A')
                context_parts.append(
                    f"{i}. [Anomaly] {desc}\n"
                    f"   สาเหตุ: {root_cause}\n"
                    f"   (ความเกี่ยวข้อง: {score:.2f})"
                )
            elif collection == 'knowledge_base':
                title = payload.get('title', 'N/A')
                content_snippet = payload.get('content', '')[:200]
                context_parts.append(
                    f"{i}. [Knowledge] {title}\n"
                    f"   {content_snippet}...\n"
                    f"   (ความเกี่ยวข้อง: {score:.2f})"
                )
            else:
                # Generic format
                context_parts.append(
                    f"{i}. [{collection}] {payload}\n"
                    f"   (ความเกี่ยวข้อง: {score:.2f})"
                )

        return "\n\n".join(context_parts)

    def _get_instructions(self) -> str:
        """Get analysis instructions for LLM"""
        if self.language == 'th':
            return """
1. **วิเคราะห์** ข้อมูลจากบริบทที่ให้มาอย่างละเอียด
2. **แสดงกระบวนการคิด** ของคุณทีละขั้นตอน (reasoning chain)
3. **อ้างอิงแหล่งที่มา** ของข้อมูลที่ใช้ในการตอบ
4. **ให้คำตอบ** ที่ชัดเจน แม่นยำ และนำไปใช้ได้จริง
5. **เสนอแนะ** การแก้ไขหรือปรับปรุง (ถ้ามี)
6. **ระบุ** ถ้าข้อมูลไม่เพียงพอหรือต้องการข้อมูลเพิ่มเติม
"""
        else:
            return """
1. **Analyze** the provided context carefully
2. **Show your reasoning** step-by-step (reasoning chain)
3. **Cite sources** of information used in your answer
4. **Provide clear**, accurate, and actionable answers
5. **Suggest** fixes or improvements (if applicable)
6. **State** if data is insufficient or additional data is needed
"""
```

---

### 5. DeepSeek-R1 Client

```python
# src/rag/deepseek_client.py

import requests
import json
from typing import List, Dict, Iterator

class DeepSeekClient:
    def __init__(self, base_url="http://localhost:11434", model="deepseek-r1:14b"):
        self.base_url = base_url
        self.model = model
        self.api_endpoint = f"{base_url}/v1/chat/completions"

    def generate(
        self,
        messages: List[Dict],
        temperature=0.7,
        max_tokens=2000,
        stream=True
    ) -> Iterator[str]:
        """
        Generate response from DeepSeek-R1

        Args:
            messages: OpenAI-format messages
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Stream response (True) or return all at once (False)

        Yields:
            Streamed response chunks (if stream=True)
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        if stream:
            # Stream response
            response = requests.post(
                self.api_endpoint,
                json=payload,
                stream=True,
                timeout=60
            )

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            pass
        else:
            # Non-streaming response
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=60
            )
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                yield data['choices'][0]['message']['content']

    def extract_reasoning_and_answer(self, full_response: str) -> Dict:
        """
        Extract reasoning chain and final answer from DeepSeek-R1 response

        DeepSeek-R1 often outputs:
        <think> reasoning process </think>
        Final answer here
        """
        # Try to parse <think> tags (if model uses them)
        import re
        think_pattern = r'<think>(.*?)</think>'
        think_matches = re.findall(think_pattern, full_response, re.DOTALL)

        if think_matches:
            reasoning = "\n".join(think_matches)
            # Remove <think> blocks from full response to get answer
            answer = re.sub(think_pattern, '', full_response, flags=re.DOTALL).strip()
        else:
            # If no <think> tags, try to split by common patterns
            # Example: "Let me analyze...\n\nFinal answer:"
            split_patterns = [
                r'(?:Final answer|คำตอบสุดท้าย|In conclusion|สรุป):',
                r'\n\n---\n\n',
                r'\n\n## Answer\n\n'
            ]

            reasoning = full_response
            answer = full_response

            for pattern in split_patterns:
                parts = re.split(pattern, full_response, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2:
                    reasoning = parts[0].strip()
                    answer = parts[1].strip()
                    break

        return {
            'reasoning': reasoning,
            'answer': answer,
            'full_response': full_response
        }
```

---

### 6. RAG Engine (Main Orchestrator)

```python
# src/rag/rag_engine.py

from .query_analyzer import QueryAnalyzer
from .query_router import QueryRouter
from .retriever import Retriever
from .prompt_builder import PromptBuilder
from .deepseek_client import DeepSeekClient

class RAGEngine:
    def __init__(self, postgres_manager, qdrant_client, redis_manager, embedding_model):
        self.query_analyzer = QueryAnalyzer()
        self.query_router = QueryRouter(postgres_manager, qdrant_client, redis_manager)
        self.retriever = Retriever(qdrant_client, postgres_manager, redis_manager, embedding_model)
        self.prompt_builder = PromptBuilder()
        self.deepseek_client = DeepSeekClient()

    def query(self, user_query: str, stream=True):
        """
        Main RAG pipeline

        Args:
            user_query: User's natural language question
            stream: Stream response (True) or return all at once (False)

        Returns:
            Dict with reasoning, answer, sources
        """
        # Step 1: Analyze query
        query_analysis = self.query_analyzer.analyze(user_query)

        # Step 2: Route query to data sources
        routing = self.query_router.route(query_analysis)

        # Step 3: Retrieve context
        vector_results = []
        sql_results = {}

        if routing['qdrant']:
            vector_results = self.retriever.retrieve_vector(
                query=query_analysis['rewritten_query'],
                collections=routing['qdrant_collections'],
                top_k=5,
                filters=None  # TODO: Add filters from query_analysis
            )

        if routing['postgresql'] or routing['redis']:
            sql_results = self.retriever.retrieve_sql(query_analysis)

        # Step 4: Build prompt
        messages = self.prompt_builder.build_prompt(
            query=user_query,
            query_analysis=query_analysis,
            vector_results=vector_results,
            sql_results=sql_results
        )

        # Step 5: Generate response
        if stream:
            # Stream response
            full_response = ""
            for chunk in self.deepseek_client.generate(messages, stream=True):
                full_response += chunk
                yield chunk  # Stream to UI

            # After streaming is done, extract reasoning and answer
            parsed = self.deepseek_client.extract_reasoning_and_answer(full_response)

            # Return final result
            yield {
                'type': 'final',
                'reasoning': parsed['reasoning'],
                'answer': parsed['answer'],
                'sources': self._format_sources(vector_results, sql_results),
                'query_analysis': query_analysis
            }
        else:
            # Non-streaming
            full_response = ""
            for chunk in self.deepseek_client.generate(messages, stream=False):
                full_response += chunk

            parsed = self.deepseek_client.extract_reasoning_and_answer(full_response)

            return {
                'reasoning': parsed['reasoning'],
                'answer': parsed['answer'],
                'sources': self._format_sources(vector_results, sql_results),
                'query_analysis': query_analysis
            }

    def _format_sources(self, vector_results: List, sql_results: Dict) -> List[Dict]:
        """Format sources for citation"""
        sources = []

        # Vector search sources
        for result in vector_results:
            sources.append({
                'type': 'vector',
                'collection': result['collection'],
                'score': result['score'],
                'payload': result['payload']
            })

        # SQL sources
        for key, value in sql_results.items():
            sources.append({
                'type': 'sql',
                'query': key,
                'data': value
            })

        return sources
```

---

## 🔧 Ollama Setup for DeepSeek-R1

### Installation & Model Download

```bash
# 1. Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull DeepSeek-R1:14B model
ollama pull deepseek-r1:14b

# 3. Verify model is downloaded
ollama list

# 4. Test model
ollama run deepseek-r1:14b "สวัสดี วันนี้เป็นอย่างไรบ้าง"

# 5. Start Ollama server (if not running)
ollama serve
```

### Docker Configuration

```yaml
# docker-compose.yml

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_models:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

### Pull Model Inside Docker

```bash
# Enter Ollama container
docker exec -it ollama bash

# Pull model
ollama pull deepseek-r1:14b

# Verify
ollama list
```

---

## 📊 Performance Optimization

### 1. Embedding Cache (Redis)
```python
# Cache embeddings to avoid re-computation
# Average embedding time: ~100ms per query
# Cache hit saves 100ms per query
```

### 2. Concurrent Retrieval
```python
import asyncio

async def retrieve_all(query_analysis):
    # Run vector and SQL retrieval in parallel
    vector_task = asyncio.create_task(retrieve_vector(...))
    sql_task = asyncio.create_task(retrieve_sql(...))

    vector_results, sql_results = await asyncio.gather(vector_task, sql_task)
    return vector_results, sql_results
```

### 3. Context Pruning
```python
# Limit context size to avoid slow inference
# Max context: 4000 tokens for DeepSeek-R1:14B
# Keep most relevant: Top-3 vector results, recent SQL data
```

---

## ✅ RAG + DeepSeek-R1 Integration Complete

### Summary
- ✅ **7-Step Pipeline**: Query analysis → Routing → Retrieval → Context assembly → Prompt → Inference → Post-processing
- ✅ **Bilingual Support**: Thai + English
- ✅ **Reasoning Chain**: Show step-by-step thinking
- ✅ **Multi-Source**: PostgreSQL + Qdrant + Redis
- ✅ **OpenAI-Compatible**: Easy integration via Ollama
- ✅ **Streaming**: Real-time response streaming
- ✅ **Caching**: Redis for embeddings, connection pooling

Next: REST API & WebSocket Design →
