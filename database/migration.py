#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agentic Workflow 통합 CRM 데이터베이스 마이그레이션 v4.0
JSON (교회) + Excel (학원) + Excel (교회) 데이터 AI 기반 지능적 통합
주소 기반 중복 제거 + AI Agents 협력 분석
"""

import json
import os
import sys
import sqlite3
import hashlib
import secrets
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager
from pathlib import Path

import logging
import sys

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_workflow.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# AI 전용 로거
ai_logger = logging.getLogger('AI_WORKFLOW')

# Gemini AI 설정 (수정된 부분)
try:
    import google.generativeai as genai
    
    # 1. settings.py에서 먼저 시도
    try:
        from settings import GEMINI_API_KEY
        ai_logger.info("🔑 settings.py에서 API 키 로드")
    except ImportError:
        # 2. .env 파일에서 직접 읽기
        GEMINI_API_KEY = None
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('GEMINI_API_KEY'):
                            # GEMINI_API_KEY = "AI....DY" 형태 파싱
                            if '=' in line:
                                key, value = line.split('=', 1)
                                value = value.strip()
                                # 따옴표 제거
                                if value.startswith('"') and value.endswith('"'):
                                    value = value[1:-1]
                                elif value.startswith("'") and value.endswith("'"):
                                    value = value[1:-1]
                                GEMINI_API_KEY = value
                                ai_logger.info(f"🔑 .env 파일에서 API 키 로드: {env_path}")
                                break
            except Exception as e:
                ai_logger.error(f"❌ .env 파일 읽기 실패: {e}")
        
        # 3. 환경변수에서 최종 시도
        if not GEMINI_API_KEY:
            GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
            if GEMINI_API_KEY:
                ai_logger.info("🔑 환경변수에서 API 키 로드")
    
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        print(f"🔑 Gemini API 키 로드 성공: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}")
        ai_logger.info(f"✅ Gemini API 설정 완료")
        AI_AVAILABLE = True
    else:
        print("❌ GEMINI_API_KEY를 찾을 수 없습니다.")
        print("📋 확인 경로:")
        print(f"  1. settings.py")
        print(f"  2. .env 파일: {env_path}")
        print(f"  3. 환경변수: GEMINI_API_KEY")
        AI_AVAILABLE = False
        
except ImportError as e:
    print(f"⚠️ Gemini AI 모듈을 가져올 수 없습니다: {e}")
    ai_logger.error(f"Gemini AI 모듈 import 실패: {e}")
    AI_AVAILABLE = False

# ==================== 직접 Enum 정의 ====================

class UserRole:
    ADMIN1 = "대표"
    ADMIN2 = "팀장"  
    SALES = "영업"
    DEVELOPER = "개발자"

class OrganizationType:
    CHURCH = "교회"
    ACADEMY = "학원"
    PUBLIC = "공공기관"
    SCHOOL = "학교"

# ==================== AI Agent 클래스들 ====================

class AIAgent:
    """기본 AI Agent 클래스"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.model = None
        
        if AI_AVAILABLE:
            try:
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                print(f"🤖 {self.name} Agent 초기화 완료")
            except Exception as e:
                print(f"❌ {self.name} Agent 초기화 실패: {e}")
    
    def analyze(self, prompt: str) -> str:
        """AI 분석 수행"""
        if not self.model:
            return f"AI 기능을 사용할 수 없습니다. ({self.name})"
        
        # 프롬프트 로깅
        ai_logger.info(f"🤖 [{self.name}] AI 프롬프트 전송:")
        ai_logger.info(f"📝 프롬프트 길이: {len(prompt)}자")
        ai_logger.debug(f"📋 전체 프롬프트:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        try:
            full_prompt = f"당신은 {self.role}입니다.\n\n{prompt}"
            
            # AI 호출 시작 로깅
            ai_logger.info(f"⏳ [{self.name}] Gemini API 호출 중...")
            
            response = self.model.generate_content(full_prompt)
            result = response.text.strip()
            
            # 응답 로깅
            ai_logger.info(f"✅ [{self.name}] AI 응답 수신 완료")
            ai_logger.info(f"📊 응답 길이: {len(result)}자")
            ai_logger.debug(f"🎯 AI 응답 내용:\n{'-'*50}\n{result}\n{'-'*50}")
            
            return result
            
        except Exception as e:
            ai_logger.error(f"❌ [{self.name}] AI 분석 중 오류: {str(e)}")
            return f"AI 분석 중 오류 발생: {str(e)}"

class DataAnalystAgent(AIAgent):
    """데이터 분석 전문 Agent"""
    
    def __init__(self):
        super().__init__("DataAnalyst", "데이터베이스 설계 및 데이터 분석 전문가")
    
    def analyze_data_source(self, source_info: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 소스 분석"""
        ai_logger.info(f"🔍 [{self.name}] 데이터 소스 분석 시작: {source_info['path']}")
        prompt = f"""
다음 데이터 소스를 분석해주세요:

**파일 정보:**
- 경로: {source_info['path']}
- 타입: {source_info['type']}
- 데이터 수: {source_info['count']:,}개
- 컬럼: {source_info['columns'][:10]}... (총 {len(source_info['columns'])}개)

**샘플 데이터:**
{json.dumps(source_info['sample_data'][:2], ensure_ascii=False, indent=2)}

**분석 요청:**
1. 데이터 품질 평가 (상/중/하)
2. 핵심 필드 식별 (기관명, 주소, 연락처 등)
3. 통합 시 고려사항
4. 권장 매핑 전략

간결하고 구체적으로 답변해주세요.
"""
        
        analysis_text = self.analyze(prompt)
        
        ai_logger.info(f"✅ [{self.name}] 데이터 소스 분석 완료")
        
        return {
            "agent": self.name,
            "source_path": source_info['path'],
            "analysis": analysis_text,
            "timestamp": datetime.now().isoformat()
        }

class IntegrationAgent(AIAgent):
    """통합 설계 전문 Agent"""
    
    def __init__(self):
        super().__init__("Integration", "데이터베이스 통합 및 스키마 설계 전문가")
    
    def design_integration_strategy(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """통합 전략 설계"""
        
        # DataFrame을 제거한 AI용 분석 결과 생성
        ai_analyses = []
        for analysis in analyses:
            ai_analysis = {
                "agent": analysis["agent"],
                "source_path": analysis["source_path"],
                "source_name": analysis["source_name"],
                "analysis": analysis["analysis"],
                "timestamp": analysis["timestamp"]
            }
            
            # data_info에서 raw_data 제거하고 메타데이터만 포함
            if "data_info" in analysis:
                data_info = analysis["data_info"].copy()
                data_info.pop("raw_data", None)  # DataFrame 제거
                ai_analysis["data_info"] = data_info
            
            ai_analyses.append(ai_analysis)
        
        prompt = f"""
    다음 데이터 소스 분석 결과를 바탕으로 통합 전략을 설계해주세요:

    **데이터 소스 요약:**
    """
        
        for i, analysis in enumerate(ai_analyses, 1):
            data_info = analysis.get("data_info", {})
            prompt += f"""
    {i}. {analysis["source_name"]}
    - 경로: {analysis["source_path"]}
    - 데이터 수: {data_info.get("count", "N/A"):,}개
    - 컬럼 수: {len(data_info.get("columns", [])):,}개
    - AI 분석: {analysis["analysis"][:200]}...
    """

        prompt += """

    **통합 전략 설계 요청:**

    1. **컬럼 매핑 전략**
    각 소스의 컬럼을 통합 테이블로 어떻게 매핑할지 구체적으로 제시해주세요.

    2. **중복 제거 규칙**
    주소 기반 중복 제거 로직을 어떻게 적용할지 설명해주세요.

    3. **데이터 변환 규칙**
    각 소스별로 필요한 데이터 정제 및 변환 방법을 제시해주세요.

    4. **통합 순서 및 우선순위**
    어떤 순서로 데이터를 통합하고 충돌 시 우선순위는 어떻게 할지 설명해주세요.

    **답변 형식:**
    마크다운 형태로 구조화해서 답변해주세요.
    """
        
        strategy_text = self.analyze(prompt)
        
        return {
            "agent": self.name,
            "strategy": strategy_text,
            "timestamp": datetime.now().isoformat()
        }

class ReviewerAgent(AIAgent):
    """검토 및 검증 전문 Agent"""
    
    def __init__(self):
        super().__init__("Reviewer", "데이터베이스 설계 검토 및 품질 보증 전문가")
    
    def review_integration_plan(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """통합 계획 검토"""
        prompt = f"""
    다음 통합 전략을 검토하고 승인 여부를 결정해주세요:

    **통합 전략:**
    {strategy.get("strategy", "전략 정보 없음")}

    **검토 관점:**
    1. 전략의 적절성 - 데이터 소스별 특성을 잘 고려했는가?
    2. 데이터 무결성 - 중복 제거 및 데이터 품질 보장 방안은 적절한가?
    3. 성능 고려사항 - 대용량 데이터 처리에 적합한가?
    4. 구현 가능성 - 실제 구현이 가능한 현실적인 방안인가?

    **검토 결과:**
    - 전체 평가: 승인/보류/거부 중 하나로 명시
    - 점수: 10점 만점 중 몇 점
    - 주요 장점: 
    - 개선이 필요한 부분:
    - 최종 결론:

    구체적이고 실용적으로 검토해주세요.
    """
        
        review_text = self.analyze(prompt)
        
        # 승인 상태 파악 (텍스트에서 키워드 추출)
        approval_status = "검토중"
        if "승인" in review_text and ("보류" not in review_text and "거부" not in review_text):
            approval_status = "승인"
        elif "보류" in review_text:
            approval_status = "보류"
        elif "거부" in review_text:
            approval_status = "거부"
        
        return {
            "agent": self.name,
            "review": review_text,
            "timestamp": datetime.now().isoformat(),
            "approval": approval_status
        }

# ==================== 통합 CRM 데이터베이스 클래스 ====================

class EnhancedCRMDatabase:
    """AI 기반 통합 CRM 데이터베이스 클래스"""
    
    def __init__(self, db_path: str = "churches_crm.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._create_tables(conn)
    
    def _create_tables(self, conn):
        """테이블 생성 (확장된 구조)"""
        # Users 테이블
        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            role TEXT NOT NULL,
            team TEXT,
            is_active BOOLEAN DEFAULT 1,
            last_login DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Organizations 테이블 (3개 소스 통합 지원)
        conn.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'UNKNOWN',
            category TEXT DEFAULT '기타',
            subcategory TEXT,  -- 교습과정명, 교단 등
            
            -- 연락처 정보
            homepage TEXT,
            phone TEXT,
            fax TEXT,
            email TEXT,
            mobile TEXT,
            postal_code TEXT,
            address TEXT,
            
            -- 상세 정보
            organization_size TEXT,
            founding_year INTEGER,
            member_count INTEGER,
            denomination TEXT,
            
            -- CRM 정보
            contact_status TEXT DEFAULT 'NEW',
            priority TEXT DEFAULT 'MEDIUM',
            assigned_to TEXT,
            lead_source TEXT DEFAULT 'DATABASE',
            estimated_value INTEGER DEFAULT 0,
            
            -- 영업 노트
            sales_notes TEXT,
            internal_notes TEXT,
            last_contact_date DATE,
            next_follow_up_date DATE,
            
            -- 메타데이터
            data_source TEXT,  -- JSON/EXCEL_ACADEMY/EXCEL_CHURCH
            ai_analysis TEXT,  -- AI 분석 결과
            crawling_data TEXT,  -- 크롤링 원본 데이터
            
            -- 시스템 필드
            created_by TEXT,
            updated_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        # 인덱스 생성 (성능 최적화)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_org_name ON organizations(name)",
            "CREATE INDEX IF NOT EXISTS idx_org_type ON organizations(type)",
            "CREATE INDEX IF NOT EXISTS idx_org_address ON organizations(address)",
            "CREATE INDEX IF NOT EXISTS idx_org_phone ON organizations(phone)",
            "CREATE INDEX IF NOT EXISTS idx_org_source ON organizations(data_source)",
            "CREATE INDEX IF NOT EXISTS idx_org_status ON organizations(contact_status)"
        ]
        
        for index in indexes:
            conn.execute(index)
        
        conn.commit()
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return f"{salt}:{password_hash.hex()}"
    
    def create_user(self, user_data: Dict[str, Any]) -> int:
        """사용자 생성"""
        with sqlite3.connect(self.db_path) as conn:
            password_hash = self._hash_password(user_data['password'])
            cursor = conn.execute('''
            INSERT INTO users (username, password_hash, full_name, email, phone, role, team)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data['username'],
                password_hash,
                user_data['full_name'],
                user_data.get('email', ''),
                user_data.get('phone', ''),
                user_data['role'],
                user_data.get('team', '')
            ))
            return cursor.lastrowid
    
    def create_organization(self, org_data: Dict[str, Any]) -> int:
        """기관 정보 생성 (확장된 구조)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
            INSERT INTO organizations (
                name, type, category, subcategory, homepage, phone, fax, email, mobile,
                postal_code, address, organization_size, founding_year, member_count,
                denomination, contact_status, priority, assigned_to, lead_source,
                estimated_value, sales_notes, internal_notes, data_source,
                ai_analysis, crawling_data, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                org_data.get('name', ''),
                org_data.get('type', 'UNKNOWN'),
                org_data.get('category', '기타'),
                org_data.get('subcategory', ''),
                org_data.get('homepage', ''),
                org_data.get('phone', ''),
                org_data.get('fax', ''),
                org_data.get('email', ''),
                org_data.get('mobile', ''),
                org_data.get('postal_code', ''),
                org_data.get('address', ''),
                org_data.get('organization_size', ''),
                org_data.get('founding_year'),
                org_data.get('member_count'),
                org_data.get('denomination', ''),
                org_data.get('contact_status', 'NEW'),
                org_data.get('priority', 'MEDIUM'),
                org_data.get('assigned_to', ''),
                org_data.get('lead_source', 'DATABASE'),
                org_data.get('estimated_value', 0),
                org_data.get('sales_notes', ''),
                org_data.get('internal_notes', ''),
                org_data.get('data_source', 'UNKNOWN'),
                org_data.get('ai_analysis', ''),
                json.dumps(org_data.get('crawling_data', {})),
                org_data.get('created_by', 'MIGRATION')
            ))
            return cursor.lastrowid
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """대시보드 통계 (소스별 분포 포함)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            total_orgs = conn.execute("SELECT COUNT(*) FROM organizations WHERE is_active = 1").fetchone()[0]
            
            # 타입별 분포
            type_counts = {}
            for row in conn.execute("SELECT type, COUNT(*) FROM organizations WHERE is_active = 1 GROUP BY type"):
                type_counts[row[0]] = row[1]
            
            # 소스별 분포
            source_counts = {}
            for row in conn.execute("SELECT data_source, COUNT(*) FROM organizations WHERE is_active = 1 GROUP BY data_source"):
                source_counts[row[0]] = row[1]
            
            return {
                "total_organizations": total_orgs,
                "type_counts": type_counts,
                "source_counts": source_counts
            }

# ==================== AI 기반 통합 마이그레이션 클래스 ====================

class AIAgenticDataMigrator:
    """AI Agentic Workflow 기반 데이터 마이그레이션"""
    
    def __init__(self, db_path: str = "churches_crm.db"):
        self.db = EnhancedCRMDatabase(db_path)
        
        # AI Agents 초기화
        self.data_analyst = DataAnalystAgent()
        self.integration_agent = IntegrationAgent()
        self.reviewer_agent = ReviewerAgent()
        
        # 통계
        self.stats = {
            "total_processed": 0,
            "successfully_migrated": 0,
            "failed": 0,
            "duplicates_skipped": 0,
            "sources": {},
            "errors": []
        }
    
        # AI 분석 결과
        self.analyses = []
        self.integration_strategy = None
        self.review_result = None
        
        print("🤖 AI Agentic Data Migrator 초기화 완료")
    
    def load_json_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """JSON 데이터 로드 및 분석"""
        try:
            if not os.path.exists(file_path):
                return None
            
            print(f"📂 JSON 파일 로드 중: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'churches' in data:
                items = data['churches']
            elif isinstance(data, list):
                items = data
            else:
                items = [data]
            
            columns = list(items[0].keys()) if items and isinstance(items[0], dict) else []
            sample_data = items[:3] if items else []
            
            return {
                "path": file_path,
                "type": "JSON",
                "count": len(items),
                "columns": columns,
                "sample_data": sample_data,
                "raw_data": items
            }
            
        except Exception as e:
            print(f"❌ JSON 로드 실패: {e}")
            return None
    
    def load_excel_data(self, file_path: str, header_row: int = 0) -> Optional[Dict[str, Any]]:
        """Excel 데이터 로드 및 분석"""
        try:
            if not os.path.exists(file_path):
                return None
            
            print(f"📂 Excel 파일 로드 중: {file_path} (헤더: {header_row+1}행)")
            
            df = pd.read_excel(file_path, sheet_name=0, header=header_row)
            df = df.dropna(how='all')
            df.columns = [str(col).strip() for col in df.columns]
            
            sample_data = []
            for i, row in df.head(3).iterrows():
                sample_data.append(row.to_dict())
            
            return {
                "path": file_path,
                "type": "Excel",
                "count": len(df),
                "columns": df.columns.tolist(),
                "sample_data": sample_data,
                "raw_data": df
            }
            
        except Exception as e:
            print(f"❌ Excel 로드 실패: {e}")
            return None
    
    def execute_ai_analysis_phase(self, data_sources: List[Dict[str, Any]]):
        """AI 분석 단계 실행"""
        print("\n🤖 Phase 1: AI Agents 데이터 분석")
        print("-" * 50)
        
        for i, source in enumerate(data_sources, 1):
            print(f"\n🔍 {i}. {source['name']} 분석 중...")
            
            # 데이터 로드
            if source['type'] == 'JSON':
                data_info = self.load_json_data(source['path'])
            elif source['type'] == 'Excel':
                header_row = source.get('header_row', 0)
                data_info = self.load_excel_data(source['path'], header_row)
            else:
                print(f"❌ 지원하지 않는 타입: {source['type']}")
                continue
            
            if not data_info:
                print(f"❌ {source['name']} 로드 실패")
                continue
            
            # AI 분석 수행
            if AI_AVAILABLE:
                analysis = self.data_analyst.analyze_data_source(data_info)
                print(f"🤖 DataAnalyst가 {source['name']} 분석 완료")
            else:
                analysis = {
                    "agent": "Manual",
                    "source_path": data_info['path'],
                    "analysis": "AI 기능 비활성화로 수동 분석",
                    "timestamp": datetime.now().isoformat()
                }
                print(f"🔧 {source['name']} 수동 분석 완료")
            
            analysis['source_name'] = source['name']
            analysis['data_info'] = data_info
            self.analyses.append(analysis)
            
            print(f"✅ {source['name']}: {data_info['count']:,}개, {len(data_info['columns'])}개 컬럼")
    
    def execute_integration_design_phase(self):
        """통합 설계 단계 실행"""
        print("\n🏗️ Phase 2: 통합 전략 설계")
        print("-" * 50)
        
        if AI_AVAILABLE:
            print("🤖 Integration Agent가 통합 전략 설계 중...")
            self.integration_strategy = self.integration_agent.design_integration_strategy(self.analyses)
            print("✅ 통합 전략 설계 완료")
        else:
            print("🔧 수동 통합 전략 사용")
            self.integration_strategy = {
                "agent": "Manual",
                "strategy": "AI 기능 비활성화로 기본 전략 사용",
                "timestamp": datetime.now().isoformat()
            }

    def execute_review_phase(self):
        """검토 단계 실행"""
        print("\n🔍 Phase 3: 설계 검토")
        print("-" * 50)
        
        if AI_AVAILABLE:
            print("🤖 Reviewer Agent가 설계 검토 중...")
            self.review_result = self.reviewer_agent.review_integration_plan(self.integration_strategy)
            approval = self.review_result.get('approval', '검토중')
            print(f"✅ 검토 완료 - 상태: {approval}")
        else:
            print("🔧 수동 검토 승인")
            self.review_result = {
                "agent": "Manual",
                "review": "AI 기능 비활성화로 자동 승인",
                "approval": "승인",
                "timestamp": datetime.now().isoformat()
            }
    
    def create_column_mapping(self, data_info: Dict[str, Any], source_type: str) -> Dict[str, str]:
        """컬럼 매핑 생성"""
        columns = data_info['columns']
        mapping = {}
        
        # 기본 매핑 규칙
        for col in columns:
            col_lower = col.lower().strip()
            
            # 기관명 매핑
            if any(keyword in col_lower for keyword in ['학원명', '기관명', '상호명', 'name', '교회명']):
                mapping['name'] = col
            # 주소 매핑
            elif any(keyword in col_lower for keyword in ['도로명주소', '주소', 'address', '소재지']):
                mapping['address'] = col
            # 전화번호 매핑
            elif any(keyword in col_lower for keyword in ['전화번호', 'phone', '연락처']) and '팩스' not in col_lower:
                mapping['phone'] = col
            # 팩스 매핑
            elif any(keyword in col_lower for keyword in ['팩스', 'fax']):
                mapping['fax'] = col
            # 이메일 매핑
            elif any(keyword in col_lower for keyword in ['이메일', 'email', 'e-mail']):
                mapping['email'] = col
            # 홈페이지 매핑
            elif any(keyword in col_lower for keyword in ['홈페이지', 'homepage', 'website', 'url']):
                mapping['homepage'] = col
            # 카테고리 매핑
            elif any(keyword in col_lower for keyword in ['분야명', '교습과정', 'category', '업종']):
                mapping['category'] = col
            # 서브카테고리 매핑
            elif any(keyword in col_lower for keyword in ['교습과정명', '계열', '교단']):
                mapping['subcategory'] = col
        
        return mapping
    
    def transform_json_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """JSON 데이터 변환 (교회)"""
        crawling_fields = ['homepage_parsed', 'page_title', 'ai_summary', 'parsing_timestamp']
        crawling_data = {k: v for k, v in item.items() if k in crawling_fields}
        
        return {
            'name': item.get('name', '').strip(),
            'type': OrganizationType.CHURCH,
            'category': item.get('category', '종교시설'),
            'homepage': item.get('homepage', '').strip(),
            'phone': item.get('phone', '').strip(),
            'fax': item.get('fax', '').strip(),
            'email': item.get('email', '').strip(),
            'mobile': item.get('mobile', '').strip(),
            'postal_code': item.get('postal_code', '').strip(),
            'address': item.get('address', '').strip(),
            'contact_status': 'NEW',
            'priority': 'MEDIUM',
            'lead_source': 'DATABASE',
            'data_source': 'JSON_CHURCH',
            'crawling_data': crawling_data,
            'created_by': 'AI_MIGRATION'
        }
    
    def transform_excel_data(self, row: pd.Series, mapping: Dict[str, str], source_type: str) -> Dict[str, Any]:
        """Excel 데이터 변환"""
        def safe_get(field: str) -> str:
            col = mapping.get(field)
            if col and col in row.index:
                value = row[col]
                if pd.isna(value):
                    return ""
                return str(value).strip()
            return ""
        
        org_type = OrganizationType.ACADEMY if 'ACADEMY' in source_type else OrganizationType.CHURCH
        
        return {
            'name': safe_get('name'),
            'type': org_type,
            'category': safe_get('category') or ('학원' if org_type == OrganizationType.ACADEMY else '종교시설'),
            'subcategory': safe_get('subcategory'),
            'phone': safe_get('phone'),
            'fax': safe_get('fax'),
            'email': safe_get('email'),
            'homepage': safe_get('homepage'),
            'address': safe_get('address'),
            'contact_status': 'NEW',
            'priority': 'MEDIUM',
            'lead_source': 'DATABASE',
            'data_source': source_type,
            'created_by': 'AI_MIGRATION'
        }
    
    def is_duplicate_by_address(self, org_data: Dict[str, Any]) -> bool:
        """주소 기반 중복 체크"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                address = org_data.get('address', '').strip()
                name = org_data.get('name', '').strip()
                
                if not name:
                    return False
                
                if address:
                    # 주소와 상호명이 모두 같은 경우
                    existing = conn.execute('''
                    SELECT COUNT(*) FROM organizations 
                    WHERE address = ? AND name = ? AND is_active = 1
                    ''', (address, name)).fetchone()[0]
                else:
                    # 주소가 없으면 상호명 + 전화번호로 체크
                    phone = org_data.get('phone', '').strip()
                existing = conn.execute('''
                SELECT COUNT(*) FROM organizations 
                    WHERE name = ? AND phone = ? AND is_active = 1
                    ''', (name, phone)).fetchone()[0]
                
                return existing > 0
                
        except Exception as e:
            print(f"⚠️  중복 체크 실패: {e}")
            return False
    
    def migrate_all_sources(self, batch_size: int = 1000) -> bool:
        """모든 소스 통합 마이그레이션"""
        ai_logger.info("🚀 통합 데이터 마이그레이션 시작")
        ai_logger.info(f"📊 배치 크기: {batch_size:,}개")
        
        total_success = 0
        
        for analysis in self.analyses:
            source_name = analysis['source_name']
            data_info = analysis['data_info']
            
            ai_logger.info(f"📂 {source_name} 마이그레이션 시작 - {data_info['count']:,}개 데이터")
            
            print(f"\n📊 {source_name} 마이그레이션 중...")
            
            if data_info['type'] == 'JSON':
                success = self._migrate_json_data(data_info, batch_size)
            else:  # Excel
                source_type = 'EXCEL_ACADEMY' if '학원' in source_name else 'EXCEL_CHURCH'
                success = self._migrate_excel_data(data_info, source_type, batch_size)
            
            total_success += success
            self.stats['sources'][source_name] = success
            
            ai_logger.info(f"✅ {source_name} 완료: {success:,}개 추가")
        
        ai_logger.info(f"🎉 전체 마이그레이션 완료: {total_success:,}개 추가")
        
        return total_success > 0
    
    def _migrate_json_data(self, data_info: Dict[str, Any], batch_size: int) -> int:
        """JSON 데이터 마이그레이션"""
        items = data_info['raw_data']
        success_count = 0
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            for item in batch:
                self.stats["total_processed"] += 1
                
                try:
                    org_data = self.transform_json_data(item)
                    
                    if not org_data.get('name'):
                        self.stats["failed"] += 1
                        continue
                    
                    if self.is_duplicate_by_address(org_data):
                        self.stats["duplicates_skipped"] += 1
                        continue
                    
                    org_id = self.db.create_organization(org_data)
                    
                    if org_id:
                        self.stats["successfully_migrated"] += 1
                        success_count += 1
                    else:
                        self.stats["failed"] += 1
                        
                except Exception as e:
                    self.stats["failed"] += 1
                    error_msg = f"JSON '{item.get('name', 'Unknown')}' 실패: {str(e)[:100]}"
                    self.stats["errors"].append(error_msg)
        
        return success_count
    
    def _migrate_excel_data(self, data_info: Dict[str, Any], source_type: str, batch_size: int) -> int:
        """Excel 데이터 마이그레이션"""
        df = data_info['raw_data']
        mapping = self.create_column_mapping(data_info, source_type)
        success_count = 0
        
        print(f"🔗 컬럼 매핑: {mapping}")
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]
            
            for _, row in batch.iterrows():
                self.stats["total_processed"] += 1
                
                try:
                    org_data = self.transform_excel_data(row, mapping, source_type)
                    
                    if not org_data.get('name'):
                        self.stats["failed"] += 1
                        continue
                    
                    if self.is_duplicate_by_address(org_data):
                        self.stats["duplicates_skipped"] += 1
                        continue
                    
                    org_id = self.db.create_organization(org_data)
                    
                    if org_id:
                        self.stats["successfully_migrated"] += 1
                        success_count += 1
                    else:
                        self.stats["failed"] += 1
                        
                except Exception as e:
                    self.stats["failed"] += 1
                    error_msg = f"Excel '{row.get(mapping.get('name', ''), 'Unknown')}' 실패: {str(e)[:100]}"
                    self.stats["errors"].append(error_msg)
        
        return success_count
    
    def create_default_users(self):
        """기본 사용자 계정 생성"""
        print("\n👥 기본 사용자 계정 생성 중...")
        
        default_users = [
            {"username": "admin", "password": "admin123", "full_name": "시스템 관리자", 
             "email": "admin@company.com", "role": UserRole.ADMIN1},
            {"username": "manager", "password": "manager123", "full_name": "영업 팀장", 
             "email": "manager@company.com", "role": UserRole.ADMIN2},
            {"username": "sales1", "password": "sales123", "full_name": "영업팀원1", 
             "email": "sales1@company.com", "role": UserRole.SALES, "team": "A팀"}
        ]
        
        for user_data in default_users:
            try:
                self.db.create_user(user_data)
                print(f"✅ 사용자 생성: {user_data['username']}")
            except Exception as e:
                if "UNIQUE" in str(e):
                    print(f"⚠️  사용자 이미 존재: {user_data['username']}")
    
    def print_final_summary(self):
        """최종 결과 요약"""
        print("\n" + "="*70)
        print("🎉 AI Agentic Workflow 통합 마이그레이션 완료")
        print("="*70)
        
        # 소스별 통계
        print("📋 데이터 소스별 결과:")
        for source, count in self.stats["sources"].items():
            print(f"  - {source}: {count:,}개")
        
        print(f"\n📈 총 처리: {self.stats['total_processed']:,}개")
        print(f"✅ 성공 마이그레이션: {self.stats['successfully_migrated']:,}개")
        print(f"🔄 중복 제거: {self.stats['duplicates_skipped']:,}개")
        print(f"❌ 실패: {self.stats['failed']:,}개")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successfully_migrated'] / self.stats['total_processed']) * 100
            print(f"📊 성공률: {success_rate:.1f}%")
        
        # 최종 DB 통계
        try:
            final_stats = self.db.get_dashboard_stats()
            print(f"\n🎯 최종 데이터베이스 통계:")
            print(f"  - 총 기관 수: {final_stats['total_organizations']:,}개")
            print(f"  - 타입별 분포:")
            for org_type, count in final_stats['type_counts'].items():
                print(f"    * {org_type}: {count:,}개")
            print(f"  - 소스별 분포:")
            for source, count in final_stats['source_counts'].items():
                print(f"    * {source}: {count:,}개")
        except Exception as e:
            print(f"⚠️  최종 통계 조회 실패: {e}")
        
        # AI 분석 결과 요약
        if AI_AVAILABLE and self.review_result:
            approval = self.review_result.get('approval', '확인불가')
            print(f"\n🤖 AI 검토 결과: {approval}")
        
        print("="*70)

def main():
    """메인 실행 함수"""
    print("🚀 AI Agentic Workflow 통합 CRM 마이그레이션 v4.0")
    print("🎯 3개 데이터 소스 AI 기반 지능적 통합")
    print("="*70)
    
    # 데이터 소스 정의
    data_sources = [
        {
            "name": "교회 JSON 데이터",
            "type": "JSON",
            "path": "data/json/merged_church_data_20250618_174032.json"
        },
        {
            "name": "학원 Excel 데이터",
            "type": "Excel",
            "path": "학원교습소정보_2024년10월31일기준20250617수정.xlsx",
            "header_row": 0
        },
        {
            "name": "교회 Excel 데이터",
            "type": "Excel",
            "path": "data/excel/교회_원본_수정01.xlsx",
            "header_row": 2  # 3행이 헤더
        }
    ]
    
    # 파일 존재 확인
    available_sources = []
    for source in data_sources:
        if os.path.exists(source['path']):
            available_sources.append(source)
            print(f"✅ {source['name']}: {source['path']}")
        else:
            alt_path = f"../{source['path']}"
            if os.path.exists(alt_path):
                source['path'] = alt_path
                available_sources.append(source)
                print(f"✅ {source['name']}: {alt_path}")
            else:
                print(f"❌ {source['name']}: 파일을 찾을 수 없음")
    
    if not available_sources:
        print("❌ 사용 가능한 데이터 소스가 없습니다.")
        return False
    
    print(f"\n📊 처리할 데이터 소스: {len(available_sources)}개")
    
    # AI 기능 상태 확인
    if AI_AVAILABLE:
        print("🤖 AI Agentic Workflow 활성화")
    else:
        print("🔧 AI 기능 비활성화 - 기본 마이그레이션 모드")
    
    # 실행 확인
    response = input("\n🚀 AI Agentic Workflow 마이그레이션을 시작하시겠습니까? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ 마이그레이션이 취소되었습니다.")
        return False
    
    # AI Agentic Workflow 실행
    migrator = AIAgenticDataMigrator("churches_crm.db")
    
    try:
        start_time = datetime.now()
        print(f"\n⏰ 시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 기본 사용자 생성
        migrator.create_default_users()
        
        # 2. AI 분석 단계
        migrator.execute_ai_analysis_phase(available_sources)
        
        # 3. 통합 설계 단계
        migrator.execute_integration_design_phase()
        
        # 4. 검토 단계
        migrator.execute_review_phase()
        
        # 5. 데이터 마이그레이션 실행
        success = migrator.migrate_all_sources(batch_size=1000)
    
        end_time = datetime.now()
        duration = end_time - start_time
    
        # 6. 최종 결과 요약
        migrator.print_final_summary()
        print(f"⏱️  총 소요 시간: {duration}")
    
        if success:
            print("\n🎉 AI Agentic Workflow 마이그레이션이 성공적으로 완료되었습니다!")
            print(f"📊 데이터베이스: {migrator.db.db_path}")
            return True
        else:
            print("\n❌ 마이그레이션 중 오류가 발생했습니다.")
            return False
        
    except Exception as e:
        print(f"\n❌ 워크플로우 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        sys.exit(1)