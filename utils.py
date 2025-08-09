# -*- coding: utf-8 -*-
"""
AI Bible Assistant 유틸리티 함수들
공통으로 사용되는 유틸리티 함수들을 모아놓았습니다.
"""

import os
import gc
import json
import gzip
import requests
import psutil
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
import time

from config import config

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MemoryManager:
    """메모리 사용량 관리 클래스"""
    
    @staticmethod
    def get_memory_usage():
        """현재 메모리 사용량 반환 (MB)"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / 1024 / 1024  # MB 단위
    
    @staticmethod
    def is_memory_critical():
        """메모리 사용량이 임계치에 도달했는지 확인"""
        current_memory = MemoryManager.get_memory_usage()
        return current_memory > config.MAX_MEMORY_MB * 0.8  # 80% 임계치
    
    @staticmethod
    def force_gc():
        """가비지 컬렉션 강제 실행"""
        collected = gc.collect()
        logger.info(f"가비지 컬렉션: {collected}개 객체 정리")
        return collected

class FileDownloader:
    """파일 다운로드 관리 클래스"""
    
    @staticmethod
    def download_file(url: str, local_path: str, max_retries: int = 3) -> bool:
        """
        URL에서 파일을 다운로드합니다.
        
        Args:
            url: 다운로드할 URL
            local_path: 저장할 로컬 경로
            max_retries: 최대 재시도 횟수
            
        Returns:
            bool: 다운로드 성공 여부
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"파일 다운로드 시도 {attempt + 1}/{max_retries}: {url}")
                
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # 파일 크기 체크
                content_length = response.headers.get('content-length')
                if content_length:
                    file_size_mb = int(content_length) / 1024 / 1024
                    logger.info(f"파일 크기: {file_size_mb:.2f} MB")
                    
                    if file_size_mb > 50:  # 50MB 초과시 경고
                        logger.warning(f"파일이 큽니다 ({file_size_mb:.2f} MB). 다운로드에 시간이 걸릴 수 있습니다.")
                
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"파일 다운로드 완료: {local_path}")
                return True
                
            except Exception as e:
                logger.error(f"다운로드 실패 (시도 {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                
        logger.error(f"파일 다운로드 실패: {url}")
        return False
    
    @staticmethod
    def is_gzipped(file_path: str) -> bool:
        """파일이 gzip으로 압축되었는지 확인"""
        try:
            with gzip.open(file_path, 'rb') as f:
                f.read(1)
            return True
        except:
            return False
    
    @staticmethod
    def load_json_file(file_path: str) -> Optional[Dict]:
        """JSON 파일을 로드합니다 (gzip 지원)"""
        try:
            if FileDownloader.is_gzipped(file_path):
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"JSON 파일 로드 실패: {file_path}, 오류: {str(e)}")
            return None

class ResponseTimer:
    """응답 시간 측정 및 관리"""
    
    @staticmethod
    def timeout_handler(timeout_seconds: float = config.KAKAO_TIMEOUT):
        """타임아웃 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    
                    if elapsed > timeout_seconds * 0.8:  # 80% 시점에서 경고
                        logger.warning(f"응답 시간 지연: {elapsed:.2f}초")
                    
                    return result
                    
                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.error(f"함수 실행 오류 ({elapsed:.2f}초): {str(e)}")
                    raise
                    
            return wrapper
        return decorator

class TextProcessor:
    """텍스트 처리 유틸리티"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """텍스트 정리 (공백, 특수문자 등)"""
        if not text:
            return ""
        
        # 연속된 공백을 하나로
        text = ' '.join(text.split())
        
        # 줄바꿈 문자 정리
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 특수문자 정리 (기본적인 것만)
        text = text.strip()
        
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 1000) -> str:
        """텍스트 길이 제한"""
        if len(text) <= max_length:
            return text
        
        # 단어 단위로 자르기
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # 80% 이상이면 단어 단위로 자르기
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 2) -> List[str]:
        """간단한 키워드 추출"""
        # 한글, 영문, 숫자만 추출
        import re
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        
        # 최소 길이 이상의 단어만 반환
        keywords = [word for word in words if len(word) >= min_length]
        
        # 중복 제거하되 순서 유지
        seen = set()
        result = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                result.append(keyword)
        
        return result[:10]  # 최대 10개만

class CacheManager:
    """간단한 메모리 캐시 관리"""
    
    def __init__(self, max_size: int = config.CACHE_SIZE_LIMIT):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if key in self.cache:
            # LRU 업데이트
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """캐시에 값 저장"""
        # 캐시 크기 제한
        while len(self.cache) >= self.max_size:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        self.cache[key] = value
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def clear(self) -> None:
        """캐시 전체 삭제"""
        self.cache.clear()
        self.access_order.clear()
        
    def get_stats(self) -> Dict[str, int]:
        """캐시 통계 정보"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'usage_percent': int(len(self.cache) / self.max_size * 100)
        }

class DateTimeHelper:
    """날짜/시간 처리 유틸리티"""
    
    @staticmethod
    def get_kst_now():
        """한국 시간 현재 시각"""
        from datetime import timezone, timedelta
        kst = timezone(timedelta(hours=9))
        return datetime.now(kst)
    
    @staticmethod
    def is_session_expired(last_activity: datetime, timeout_hours: int = config.SESSION_TIMEOUT_HOURS) -> bool:
        """세션 만료 여부 확인"""
        if not last_activity:
            return True
        
        current_time = DateTimeHelper.get_kst_now()
        # timezone-naive datetime을 timezone-aware로 변환
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=current_time.tzinfo)
        
        elapsed = current_time - last_activity
        return elapsed.total_seconds() > (timeout_hours * 3600)
    
    @staticmethod
    def format_korean_datetime(dt: datetime) -> str:
        """한국어 형식으로 날짜 포맷팅"""
        return dt.strftime("%Y년 %m월 %d일 %H시 %M분")

# 전역 캐시 인스턴스
global_cache = CacheManager()

def log_function_call(func_name: str, **kwargs):
    """함수 호출 로그"""
    args_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"함수 호출: {func_name}({args_str})")

def safe_execute(func, default_return=None, log_errors=True):
    """안전한 함수 실행 (예외 처리 포함)"""
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"함수 실행 오류: {str(e)}")
        return default_return
