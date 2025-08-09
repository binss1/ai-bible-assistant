# -*- coding: utf-8 -*-
"""
대화 관리 모듈
MongoDB를 사용하여 사용자 대화를 저장하고 관리합니다.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import hashlib

from config import config
from utils import DateTimeHelper, log_function_call, safe_execute

logger = logging.getLogger(__name__)

class UserSession:
    """사용자 세션 데이터 클래스"""
    
    def __init__(self, user_id: str, session_data: Dict = None):
        self.user_id = user_id
        self.session_id = self._generate_session_id(user_id)
        self.created_at = DateTimeHelper.get_kst_now()
        self.last_activity = self.created_at
        self.conversation_history: List[Dict] = []
        self.user_categories: List[str] = []
        self.interaction_count = 0
        
        if session_data:
            self._load_from_dict(session_data)
    
    def _generate_session_id(self, user_id: str) -> str:
        """사용자 ID 기반 세션 ID 생성"""
        today = DateTimeHelper.get_kst_now().strftime("%Y-%m-%d")
        session_string = f"{user_id}_{today}"
        return hashlib.md5(session_string.encode()).hexdigest()[:12]
    
    def _load_from_dict(self, data: Dict):
        """딕셔너리 데이터에서 세션 정보 로드"""
        self.created_at = data.get('created_at', self.created_at)
        self.last_activity = data.get('last_activity', self.last_activity)
        self.conversation_history = data.get('conversation_history', [])
        self.user_categories = data.get('user_categories', [])
        self.interaction_count = data.get('interaction_count', 0)
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """대화에 메시지 추가"""
        message = {
            'role': role,  # 'user' 또는 'assistant'
            'content': content,
            'timestamp': DateTimeHelper.get_kst_now(),
            'metadata': metadata or {}
        }
        
        self.conversation_history.append(message)
        
        # 대화 기록 제한
        if len(self.conversation_history) > config.MAX_CONVERSATION_HISTORY * 2:
            # 절반만 남기기
            self.conversation_history = self.conversation_history[-config.MAX_CONVERSATION_HISTORY:]
        
        self.last_activity = DateTimeHelper.get_kst_now()
        self.interaction_count += 1
    
    def update_categories(self, categories: List[str]):
        """사용자 관심 카테고리 업데이트"""
        for category in categories:
            if category not in self.user_categories:
                self.user_categories.append(category)
        
        # 카테고리 수 제한
        if len(self.user_categories) > 10:
            self.user_categories = self.user_categories[-10:]
    
    def get_recent_messages(self, count: int = 5) -> List[Dict]:
        """최근 메시지 반환"""
        return self.conversation_history[-count:] if count > 0 else self.conversation_history
    
    def is_expired(self) -> bool:
        """세션 만료 여부 확인"""
        return DateTimeHelper.is_session_expired(self.last_activity)
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'created_at': self.created_at,
            'last_activity': self.last_activity,
            'conversation_history': self.conversation_history,
            'user_categories': self.user_categories,
            'interaction_count': self.interaction_count
        }

class ConversationManager:
    """대화 관리 메인 클래스"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.conversations_collection: Optional[Collection] = None
        self.analytics_collection: Optional[Collection] = None
        
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        
        logger.info("ConversationManager 초기화 완료")
    
    def _connect_to_mongodb(self) -> bool:
        """MongoDB 연결 초기화"""
        if self.client is not None and self.database is not None:
            return True
        
        if self._connection_attempts >= self._max_connection_attempts:
            logger.error("MongoDB 연결 시도 한도 초과")
            return False
        
        self._connection_attempts += 1
        
        try:
            if not config.MONGODB_URI:
                logger.error("MongoDB URI가 설정되지 않았습니다")
                return False
            
            # MongoDB 클라이언트 생성
            self.client = MongoClient(
                config.MONGODB_URI,
                serverSelectionTimeoutMS=5000,  # 5초 타임아웃
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=1  # Railway 환경에서 연결 수 제한
            )
            
            # 연결 테스트
            self.client.admin.command('ismaster')
            
            # 데이터베이스 및 컬렉션 설정
            self.database = self.client[config.DATABASE_NAME]
            self.conversations_collection = self.database[config.CONVERSATIONS_COLLECTION]
            self.analytics_collection = self.database[config.ANALYTICS_COLLECTION]
            
            # 인덱스 생성
            self._create_indexes()
            
            logger.info(f"MongoDB 연결 성공 - DB: {config.DATABASE_NAME}")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB 연결 실패 (시도 {self._connection_attempts}): {str(e)}")
            self.client = None
            self.database = None
            return False
    
    def _create_indexes(self):
        """필요한 인덱스 생성"""
        try:
            # conversations 컬렉션 인덱스
            self.conversations_collection.create_index("user_id")
            self.conversations_collection.create_index("session_id")
            self.conversations_collection.create_index("last_activity")
            
            # analytics 컬렉션 인덱스
            self.analytics_collection.create_index("timestamp")
            self.analytics_collection.create_index("event_type")
            
            logger.info("MongoDB 인덱스 생성 완료")
            
        except Exception as e:
            logger.warning(f"인덱스 생성 오류: {str(e)}")
    
    def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """
        사용자 세션 정보를 가져옵니다.
        
        Args:
            user_id: 사용자 ID (카카오톡 사용자 ID)
            
        Returns:
            Optional[UserSession]: 사용자 세션 객체
        """
        log_function_call("get_user_session", user_id=user_id[:8] + "***")
        
        if not self._connect_to_mongodb():
            return UserSession(user_id)  # 오프라인 세션 반환
        
        try:
            # 최근 세션 조회
            session_data = self.conversations_collection.find_one(
                {"user_id": user_id},
                sort=[("last_activity", -1)]
            )
            
            if session_data:
                session = UserSession(user_id, session_data)
                
                # 세션 만료 확인
                if session.is_expired():
                    logger.info(f"만료된 세션 감지: {user_id}")
                    session = UserSession(user_id)  # 새 세션 생성
                else:
                    logger.info(f"기존 세션 로드: {user_id}, 메시지 수: {len(session.conversation_history)}")
                
                return session
            else:
                logger.info(f"새 사용자 세션 생성: {user_id}")
                return UserSession(user_id)
                
        except Exception as e:
            logger.error(f"사용자 세션 조회 오류: {str(e)}")
            return UserSession(user_id)  # 오프라인 세션 반환
    
    def save_user_session(self, session: UserSession) -> bool:
        """
        사용자 세션 정보를 저장합니다.
        
        Args:
            session: 저장할 사용자 세션
            
        Returns:
            bool: 저장 성공 여부
        """
        log_function_call("save_user_session", 
                         user_id=session.user_id[:8] + "***", 
                         message_count=len(session.conversation_history))
        
        if not self._connect_to_mongodb():
            logger.warning("MongoDB 연결 실패 - 세션 저장 스킵")
            return False
        
        try:
            # 세션 데이터 준비
            session_dict = session.to_dict()
            
            # upsert 실행
            result = self.conversations_collection.replace_one(
                {"session_id": session.session_id},
                session_dict,
                upsert=True
            )
            
            logger.info(f"사용자 세션 저장 완료: {session.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"사용자 세션 저장 오류: {str(e)}")
            return False
    
    def log_interaction(self, user_id: str, event_type: str, data: Dict = None) -> bool:
        """
        사용자 상호작용을 로그로 기록합니다.
        
        Args:
            user_id: 사용자 ID
            event_type: 이벤트 타입 (message, error, etc.)
            data: 추가 데이터
            
        Returns:
            bool: 로그 기록 성공 여부
        """
        if not self._connect_to_mongodb():
            return False
        
        try:
            log_entry = {
                'user_id': user_id,
                'event_type': event_type,
                'timestamp': DateTimeHelper.get_kst_now(),
                'data': data or {}
            }
            
            self.analytics_collection.insert_one(log_entry)
            return True
            
        except Exception as e:
            logger.error(f"상호작용 로그 기록 오류: {str(e)}")
            return False
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """사용자 통계 정보 조회"""
        if not self._connect_to_mongodb():
            return {}
        
        try:
            # 총 대화 수
            total_conversations = self.conversations_collection.count_documents({"user_id": user_id})
            
            # 최근 활동 날짜
            recent_session = self.conversations_collection.find_one(
                {"user_id": user_id},
                sort=[("last_activity", -1)]
            )
            
            last_activity = None
            if recent_session:
                last_activity = recent_session.get('last_activity')
            
            # 상호작용 통계
            interaction_stats = list(self.analytics_collection.aggregate([
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$event_type",
                    "count": {"$sum": 1}
                }}
            ]))
            
            return {
                'total_conversations': total_conversations,
                'last_activity': last_activity,
                'interaction_stats': {stat['_id']: stat['count'] for stat in interaction_stats}
            }
            
        except Exception as e:
            logger.error(f"사용자 통계 조회 오류: {str(e)}")
            return {}
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """오래된 세션 정리"""
        if not self._connect_to_mongodb():
            return 0
        
        try:
            cutoff_date = DateTimeHelper.get_kst_now() - timedelta(days=days_old)
            
            result = self.conversations_collection.delete_many({
                "last_activity": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"오래된 세션 정리 완료: {deleted_count}개")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"세션 정리 오류: {str(e)}")
            return 0
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """전체 서비스 통계"""
        if not self._connect_to_mongodb():
            return {'connected': False}
        
        try:
            # 총 사용자 수
            total_users = len(self.conversations_collection.distinct("user_id"))
            
            # 총 대화 수
            total_conversations = self.conversations_collection.count_documents({})
            
            # 최근 24시간 활성 사용자
            yesterday = DateTimeHelper.get_kst_now() - timedelta(hours=24)
            active_users_24h = len(self.conversations_collection.distinct("user_id", {
                "last_activity": {"$gte": yesterday}
            }))
            
            # 인기 카테고리 (최근 7일)
            week_ago = DateTimeHelper.get_kst_now() - timedelta(days=7)
            category_stats = list(self.analytics_collection.aggregate([
                {"$match": {
                    "timestamp": {"$gte": week_ago},
                    "data.categories": {"$exists": True}
                }},
                {"$unwind": "$data.categories"},
                {"$group": {
                    "_id": "$data.categories",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]))
            
            return {
                'connected': True,
                'total_users': total_users,
                'total_conversations': total_conversations,
                'active_users_24h': active_users_24h,
                'popular_categories': [
                    {'category': stat['_id'], 'count': stat['count']} 
                    for stat in category_stats
                ],
                'database_name': config.DATABASE_NAME
            }
            
        except Exception as e:
            logger.error(f"전체 통계 조회 오류: {str(e)}")
            return {'connected': False, 'error': str(e)}
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            return self._connect_to_mongodb()
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {str(e)}")
            return False

# 전역 ConversationManager 인스턴스
conversation_manager = ConversationManager()
