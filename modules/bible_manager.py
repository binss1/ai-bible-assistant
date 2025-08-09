# -*- coding: utf-8 -*-
"""
성경 데이터 관리 모듈
성경 임베딩 로드, 구절 검색, 카테고리 분류 기능을 담당합니다.
"""

import os
import json
import numpy as np
import logging
from typing import List, Dict, Optional, Any, Tuple, Union
try:
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    cosine_similarity = None
import re

from config import config
from utils import FileDownloader, MemoryManager, global_cache, log_function_call, safe_execute

logger = logging.getLogger(__name__)

if cosine_similarity is None:
    logger.warning("scikit-learn이 설치되지 않음 - 임베딩 검색 기능 제한")

class BibleVerse:
    """성경 구절 데이터 클래스"""
    
    def __init__(self, verse_id: str, text: str, book: str, chapter: int, verse: int, 
                 embedding: Optional[List[float]] = None):
        self.id = verse_id
        self.text = text
        self.book = book
        self.chapter = chapter
        self.verse = verse
        self.embedding = embedding
        self.similarity_score = 0.0
    
    def get_reference(self) -> str:
        """성경 구절 참조 형식 반환"""
        return f"{self.book} {self.chapter}:{self.verse}"
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'text': self.text,
            'book': self.book,
            'chapter': self.chapter,
            'verse': self.verse,
            'reference': self.get_reference(),
            'similarity_score': round(self.similarity_score, 3)
        }

class CategoryClassifier:
    """고민 카테고리 분류기"""
    
    def __init__(self):
        self.category_keywords = {
            '관계': [
                '가족', '부모', '자녀', '형제', '자매', '친구', '연인', '남편', '아내',
                '결혼', '이혼', '갈등', '다툼', '관계', '사랑', '미움', '용서',
                '배신', '신뢰', '소통', '이해', '외로움', '고립'
            ],
            '진로': [
                '진로', '직업', '취업', '직장', '회사', '사업', '창업', '학교',
                '공부', '시험', '성적', '진학', '대학', '전공', '선택', '결정',
                '미래', '꿈', '목표', '포기', '실패', '성공'
            ],
            '신앙': [
                '하나님', '예수', '성령', '기도', '예배', '교회', '믿음', '신앙',
                '구원', '죄', '회개', '감사', '찬양', '성경', '말씀', '은혜',
                '축복', '시험', '연단', '순종', '의심', '불신'
            ],
            '감정': [
                '우울', '슬픔', '기쁨', '행복', '분노', '화', '불안', '걱정',
                '두려움', '무서움', '스트레스', '좌절', '절망', '희망',
                '평안', '위로', '격려', '감정', '마음', '정신'
            ],
            '윤리': [
                '선악', '옳고', '그름', '도덕', '윤리', '양심', '정직', '거짓말',
                '속임', '진실', '정의', '공의', '공정', '불의', '부정', '타락',
                '유혹', '시험', '선택', '결정', '가치관'
            ],
            '건강': [
                '건강', '질병', '병', '아픔', '고통', '치료', '의사', '병원',
                '약', '수술', '회복', '죽음', '생명', '몸', '정신', '마음',
                '휴식', '피로', '스트레스', '운동', '식사'
            ],
            '경제': [
                '돈', '재정', '경제', '가난', '부', '가난한', '부자', '빚', '대출',
                '투자', '사업', '직장', '월급', '수입', '지출', '절약',
                '후원', '기부', '헌금', '물질', '재물'
            ]
        }
    
    def classify(self, text: str) -> List[Tuple[str, float]]:
        """
        텍스트를 분석하여 고민 카테고리를 분류합니다.
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            List[Tuple[str, float]]: (카테고리, 점수) 리스트 (점수 내림차순)
        """
        text = text.lower()
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    # 키워드 길이에 따라 가중치 부여
                    weight = len(keyword) / 3.0
                    score += weight
            
            # 텍스트 길이로 정규화
            if len(text) > 0:
                category_scores[category] = score / len(text) * 100
            else:
                category_scores[category] = 0
        
        # 점수 순으로 정렬
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 최소 점수 이상인 카테고리만 반환
        return [(cat, score) for cat, score in sorted_categories if score > 0.5]

class BibleManager:
    """성경 데이터 관리 메인 클래스"""
    
    def __init__(self):
        self.verses: List[BibleVerse] = []
        self.embeddings_matrix: Optional[np.ndarray] = None
        self.is_loaded = False
        self.category_classifier = CategoryClassifier()
        
        # 메모리 사용량 추적
        self._initial_memory = MemoryManager.get_memory_usage()
        
        logger.info("BibleManager 초기화 시작")
        
        # 성경 데이터 자동 로딩
        try:
            self.load_embeddings()
            logger.info("BibleManager 초기화 완료")
        except Exception as e:
            logger.error(f"BibleManager 초기화 중 오류: {e}")
            # 실패해도 인스턴스는 생성되도록 함
    
    def load_embeddings(self) -> bool:
        """
        성경 임베딩 데이터를 로드합니다.
        
        Returns:
            bool: 로드 성공 여부
        """
        log_function_call("load_embeddings")
        
        try:
            # 캐시 확인
            cached_data = global_cache.get('bible_embeddings')
            if cached_data:
                logger.info("캐시에서 성경 데이터 로드")
                self.verses, self.embeddings_matrix = cached_data
                self.is_loaded = True
                return True
            
            # 파일 소스 결정
            source = config.get_bible_embeddings_source()
            
            # URL에서 다운로드가 필요한 경우
            if source.startswith('http'):
                # 다중 URL 처리
                if ',' in source:
                    logger.info("다중 URL 감지됨 - 병합 처리")
                    return self._load_multiple_urls(source.split(','))
                else:
                    local_path = config.BIBLE_EMBEDDINGS_PATH
                    if not os.path.exists(local_path):
                        logger.info(f"임베딩 파일 다운로드: {source}")
                        if not FileDownloader.download_file(source, local_path):
                            logger.error("임베딩 파일 다운로드 실패")
                            return False
                    source = local_path
            
            # JSON 파일 로드
            logger.info(f"성경 임베딩 로드 시작: {source}")
            data = FileDownloader.load_json_file(source)
            
            if not data:
                logger.error("임베딩 데이터 로드 실패")
                return False
            
            # 데이터 구조 확인
            if isinstance(data, list):
                # 리스트 형태의 데이터
                verses_data = data
            elif isinstance(data, dict) and 'verses' in data:
                # 딕셔너리 형태의 데이터
                verses_data = data['verses']
            else:
                logger.error("지원하지 않는 데이터 형식")
                return False
            
            # 공통 데이터 처리 메서드 사용
            return self._process_verses_data(verses_data)
            
        except Exception as e:
            logger.error(f"임베딩 로드 오류: {str(e)}")
            return False
    
    def _load_multiple_urls(self, urls: List[str]) -> bool:
        """
        다중 URL에서 데이터를 로드하고 병합합니다.
        
        Args:
            urls: 다운로드할 URL 리스트
            
        Returns:
            bool: 로드 성공 여부
        """
        try:
            logger.info(f"{len(urls)}개의 파일을 병합 로드합니다")
            
            all_verses_data = []
            
            for i, url in enumerate(urls):
                url = url.strip()
                if not url:
                    continue
                    
                try:
                    logger.info(f"파일 {i+1}/{len(urls)} 다운로드: {url}")
                    
                    response = requests.get(url, timeout=300)
                    response.raise_for_status()
                    
                    # gzip 압축 해제
                    if url.endswith('.gz'):
                        import gzip
                        content = gzip.decompress(response.content)
                    else:
                        content = response.content
                    
                    data = json.loads(content)
                    
                    if isinstance(data, list):
                        all_verses_data.extend(data)
                        logger.info(f"파일 {i+1} 로드 완료: {len(data)}개 구절")
                    elif isinstance(data, dict) and 'verses' in data:
                        all_verses_data.extend(data['verses'])
                        logger.info(f"파일 {i+1} 로드 완료: {len(data['verses'])}개 구절")
                    
                    # 메모리 정리
                    del response, content, data
                    MemoryManager.force_gc()
                    
                except Exception as e:
                    logger.error(f"파일 {i+1} 다운로드 실패: {e}")
                    continue
            
            if not all_verses_data:
                logger.error("유효한 데이터를 찾을 수 없음")
                return False
            
            # 벑합된 데이터 처리
            return self._process_verses_data(all_verses_data)
            
        except Exception as e:
            logger.error(f"다중 URL 로드 오류: {e}")
            return False
    
    def _process_verses_data(self, verses_data: List[Dict]) -> bool:
        """
        구절 데이터를 처리합니다.
        
        Args:
            verses_data: 구절 데이터 리스트
            
        Returns:
            bool: 처리 성공 여부
        """
        try:
            self.verses = []
            embeddings_list = []
            
            for item in verses_data:
                try:
                    # 데이터 구조 유연하게 처리
                    verse_id = item.get('id', f"{item.get('book', '')}_{item.get('chapter', 0)}_{item.get('verse', 0)}")
                    text = item.get('text', '')
                    book = item.get('book', '알 수 없음')
                    chapter = item.get('chapter', 0)
                    verse = item.get('verse', 0)
                    embedding = item.get('embedding', [])
                    
                    if not text:
                        continue
                    
                    bible_verse = BibleVerse(verse_id, text, book, chapter, verse, embedding)
                    self.verses.append(bible_verse)
                    
                    if embedding:
                        embeddings_list.append(embedding)
                        
                except Exception as e:
                    logger.warning(f"구절 데이터 파싱 오류: {str(e)}")
                    continue
            
            if not self.verses:
                logger.error("유효한 구절 데이터가 없습니다")
                return False
            
            # 임베딩 매트릭스 생성
            if embeddings_list:
                self.embeddings_matrix = np.array(embeddings_list, dtype=np.float32)
                logger.info(f"임베딩 차원: {self.embeddings_matrix.shape[1]}")
            
            logger.info(f"성경 구절 로드 완료: {len(self.verses)}개 구절")
            
            # 메모리 사용량 체크
            current_memory = MemoryManager.get_memory_usage()
            memory_used = current_memory - self._initial_memory
            logger.info(f"임베딩 로드 후 메모리 사용량: +{memory_used:.1f}MB")
            
            # 캐시에 저장 (메모리가 충분한 경우에만)
            if not MemoryManager.is_memory_critical():
                global_cache.set('bible_embeddings', (self.verses, self.embeddings_matrix))
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"구절 데이터 처리 오류: {e}")
            return False
    
    def search_verses(self, query_text: str, query_embedding: Optional[List[float]] = None, 
                     top_k: int = None) -> List[BibleVerse]:
        """
        쿼리에 해당하는 성경 구절을 검색합니다.
        
        Args:
            query_text: 검색할 텍스트
            query_embedding: 쿼리의 임베딩 (없으면 키워드 기반 검색)
            top_k: 반환할 최대 결과 수
            
        Returns:
            List[BibleVerse]: 검색된 구절 리스트 (유사도 내림차순)
        """
        log_function_call("search_verses", query_length=len(query_text), top_k=top_k)
        
        if not self.is_loaded:
            logger.warning("성경 데이터가 로드되지 않음")
            return []
        
        if top_k is None:
            top_k = config.MAX_BIBLE_RESULTS
        
        results = []
        
        try:
            # 임베딩 기반 검색
            if query_embedding and self.embeddings_matrix is not None:
                results = self._embedding_search(query_embedding, top_k)
            
            # 키워드 기반 검색 (백업 또는 보완)
            if not results or len(results) < top_k:
                keyword_results = self._keyword_search(query_text, top_k)
                
                # 기존 결과와 병합 (중복 제거)
                existing_ids = {v.id for v in results}
                for verse in keyword_results:
                    if verse.id not in existing_ids and len(results) < top_k:
                        results.append(verse)
            
            # 최소 유사도 기준 필터링
            results = [v for v in results if v.similarity_score >= config.SIMILARITY_THRESHOLD]
            
            logger.info(f"구절 검색 완료: {len(results)}개 결과 (임계값: {config.SIMILARITY_THRESHOLD})")
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"구절 검색 오류: {str(e)}")
            return []
    
    def _embedding_search(self, query_embedding: List[float], top_k: int) -> List[BibleVerse]:
        """임베딩 기반 유사도 검색"""
        try:
            if cosine_similarity is None:
                logger.warning("cosine_similarity를 사용할 수 없음 - 키워드 검색으로 대체")
                return []
            
            query_vector = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(query_vector, self.embeddings_matrix)[0]
            
            # 상위 결과 선택
            top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # 여유분 확보
            
            results = []
            for idx in top_indices:
                if similarities[idx] >= config.SIMILARITY_THRESHOLD:
                    verse = self.verses[idx]
                    verse.similarity_score = float(similarities[idx])
                    results.append(verse)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"임베딩 검색 오류: {str(e)}")
            return []
    
    def _keyword_search(self, query_text: str, top_k: int) -> List[BibleVerse]:
        """키워드 기반 검색 (백업용)"""
        try:
            from utils import TextProcessor
            query_keywords = TextProcessor.extract_keywords(query_text)
            
            if not query_keywords:
                return []
            
            verse_scores = []
            
            for verse in self.verses:
                score = 0
                verse_text = verse.text.lower()
                
                for keyword in query_keywords:
                    keyword = keyword.lower()
                    if keyword in verse_text:
                        # 키워드 길이와 빈도에 따른 점수
                        count = verse_text.count(keyword)
                        score += len(keyword) * count / len(verse_text) * 100
                
                if score > 0:
                    verse.similarity_score = min(score, 1.0)  # 1.0으로 정규화
                    verse_scores.append(verse)
            
            # 점수순으로 정렬
            verse_scores.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"키워드 검색 결과: {len(verse_scores)}개")
            return verse_scores[:top_k]
            
        except Exception as e:
            logger.error(f"키워드 검색 오류: {str(e)}")
            return []
    
    def classify_concern(self, text: str) -> List[Tuple[str, float]]:
        """고민 내용을 카테고리별로 분류"""
        return self.category_classifier.classify(text)
    
    def get_popular_verses(self, category: Optional[str] = None, count: int = 5) -> List[BibleVerse]:
        """
        인기 있는 성경 구절을 반환합니다.
        
        Args:
            category: 특정 카테고리의 구절 (없으면 전체)
            count: 반환할 구절 수
            
        Returns:
            List[BibleVerse]: 인기 구절 리스트
        """
        # 잘 알려진 위로와 격려의 구절들
        popular_references = [
            ("시편", 23, 1),  # 여호와는 나의 목자시니
            ("요한복음", 3, 16),  # 하나님이 세상을 이처럼 사랑하사
            ("로마서", 8, 28),  # 하나님을 사랑하는 자들에게는
            ("빌립보서", 4, 13),  # 내게 능력 주시는 자 안에서
            ("마태복음", 11, 28),  # 수고하고 무거운 짐 진 자들아
            ("이사야", 40, 31),  # 여호와를 앙망하는 자는
            ("예레미야", 29, 11),  # 내가 너희를 향한 생각을 아노라
            ("고린도전서", 13, 4),  # 사랑은 오래 참고
            ("시편", 46, 1),  # 하나님은 우리의 피난처시요
            ("디모데후서", 1, 7)  # 하나님이 우리에게 주신 것은
        ]
        
        results = []
        
        for book, chapter, verse in popular_references:
            matching_verses = [
                v for v in self.verses 
                if v.book == book and v.chapter == chapter and v.verse == verse
            ]
            
            if matching_verses:
                verse_obj = matching_verses[0]
                verse_obj.similarity_score = 1.0  # 높은 점수 설정
                results.append(verse_obj)
                
                if len(results) >= count:
                    break
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """성경 데이터 통계 정보 반환"""
        if not self.is_loaded:
            return {'loaded': False}
        
        # 책별 구절 수 계산
        book_counts = {}
        for verse in self.verses:
            book_counts[verse.book] = book_counts.get(verse.book, 0) + 1
        
        current_memory = MemoryManager.get_memory_usage()
        memory_used = current_memory - self._initial_memory
        
        return {
            'loaded': True,
            'total_verses': len(self.verses),
            'books_count': len(book_counts),
            'embedding_dimension': self.embeddings_matrix.shape[1] if self.embeddings_matrix is not None else 0,
            'memory_usage_mb': round(memory_used, 1),
            'similarity_threshold': config.SIMILARITY_THRESHOLD,
            'categories': config.CATEGORIES,
            'book_distribution': book_counts
        }

# 전역 BibleManager 인스턴스
bible_manager = BibleManager()
