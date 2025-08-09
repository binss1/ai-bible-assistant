# -*- coding: utf-8 -*-
"""
Railway 환경용 임베딩 로더
Railway 배포 환경에서 효율적으로 임베딩을 로드합니다.
"""

import os
import sys
import json
import gzip
import logging
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import FileDownloader, MemoryManager

logger = logging.getLogger(__name__)

class RailwayEmbeddingsLoader:
    """Railway 환경 특화 임베딩 로더"""
    
    def __init__(self, embeddings_url: str = None, local_path: str = None):
        self.embeddings_url = embeddings_url
        self.local_path = local_path or 'bible_embeddings.json'
        self.temp_path = '/tmp/bible_embeddings.json'  # Railway 임시 디렉토리
        
    def load_embeddings(self) -> dict:
        """
        Railway 환경에서 임베딩을 로드합니다.
        
        Returns:
            dict: 로드된 임베딩 데이터
        """
        logger.info("Railway 환경에서 임베딩 로드 시작")
        
        # 1. 로컬 파일 먼저 확인
        if os.path.exists(self.local_path):
            logger.info(f"로컬 파일 사용: {self.local_path}")
            return self._load_from_file(self.local_path)
        
        # 2. URL에서 다운로드
        if self.embeddings_url:
            logger.info(f"URL에서 다운로드: {self.embeddings_url}")
            
            # Railway 환경에서는 임시 디렉토리 사용
            download_path = self.temp_path
            
            if FileDownloader.download_file(self.embeddings_url, download_path):
                data = self._load_from_file(download_path)
                
                # 메모리 절약을 위해 임시 파일 삭제
                try:
                    os.remove(download_path)
                    logger.info("임시 파일 삭제 완료")
                except:
                    pass
                
                return data
            else:
                logger.error("다운로드 실패")
                return None
        
        logger.error("임베딩 파일을 찾을 수 없습니다")
        return None
    
    def _load_from_file(self, file_path: str) -> dict:
        """파일에서 임베딩 데이터 로드"""
        try:
            # 메모리 사용량 모니터링
            initial_memory = MemoryManager.get_memory_usage()
            logger.info(f"로딩 전 메모리 사용량: {initial_memory:.1f}MB")
            
            # 파일 크기 확인
            file_size = os.path.getsize(file_path) / 1024 / 1024
            logger.info(f"파일 크기: {file_size:.2f}MB")
            
            # gzip 파일인지 확인
            if FileDownloader.is_gzipped(file_path):
                logger.info("gzip 압축 파일 로드")
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                logger.info("일반 JSON 파일 로드")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # 메모리 사용량 체크
            final_memory = MemoryManager.get_memory_usage()
            memory_used = final_memory - initial_memory
            logger.info(f"로딩 후 메모리 사용량: {final_memory:.1f}MB (+{memory_used:.1f}MB)")
            
            # 데이터 구조 확인
            if isinstance(data, dict) and 'verses' in data:
                verses_count = len(data['verses'])
                metadata = data.get('metadata', {})
                logger.info(f"구절 수: {verses_count}")
                logger.info(f"메타데이터: {metadata}")
                return data
            elif isinstance(data, list):
                logger.info(f"구절 수: {len(data)}")
                return {'verses': data, 'metadata': {}}
            else:
                logger.error("지원하지 않는 데이터 형식")
                return None
            
        except Exception as e:
            logger.error(f"파일 로드 오류: {str(e)}")
            return None
    
    def optimize_for_railway(self, data: dict) -> dict:
        """Railway 환경에 맞게 데이터 최적화"""
        if not data or 'verses' not in data:
            return data
        
        logger.info("Railway 환경용 데이터 최적화 시작")
        
        verses = data['verses']
        optimized_verses = []
        
        # 메모리 절약을 위한 배치 처리
        batch_size = 1000
        
        for i in range(0, len(verses), batch_size):
            batch = verses[i:i + batch_size]
            
            for verse in batch:
                # 필수 필드만 유지
                optimized_verse = {
                    'id': verse.get('id', ''),
                    'text': verse.get('text', ''),
                    'book': verse.get('book', ''),
                    'chapter': verse.get('chapter', 0),
                    'verse': verse.get('verse', 0)
                }
                
                # 임베딩은 float32로 변환하여 메모리 절약
                embedding = verse.get('embedding', [])
                if embedding:
                    # 정밀도를 줄여 메모리 절약
                    optimized_verse['embedding'] = [round(float(x), 6) for x in embedding]
                
                optimized_verses.append(optimized_verse)
            
            # 메모리 상태 체크
            if MemoryManager.is_memory_critical():
                logger.warning(f"메모리 부족 감지 - 가비지 컬렉션 실행 (배치 {i // batch_size + 1})")
                MemoryManager.force_gc()
        
        logger.info(f"최적화 완료: {len(optimized_verses)}개 구절")
        
        return {
            'verses': optimized_verses,
            'metadata': data.get('metadata', {}),
            'optimized_for_railway': True
        }
    
    def preload_and_cache(self) -> bool:
        """임베딩을 미리 로드하고 캐시합니다"""
        try:
            logger.info("임베딩 프리로드 시작")
            
            data = self.load_embeddings()
            if not data:
                return False
            
            # Railway 환경용 최적화
            optimized_data = self.optimize_for_railway(data)
            
            # 글로벌 캐시에 저장
            from utils import global_cache
            global_cache.set('preloaded_embeddings', optimized_data)
            
            logger.info("임베딩 프리로드 완료")
            return True
            
        except Exception as e:
            logger.error(f"프리로드 실패: {str(e)}")
            return False

def test_embedding_load():
    """임베딩 로드 테스트"""
    print("🧪 임베딩 로드 테스트")
    
    # 환경변수에서 URL 가져오기
    embeddings_url = os.getenv('BIBLE_EMBEDDINGS_URL')
    
    loader = RailwayEmbeddingsLoader(embeddings_url)
    
    print(f"📡 URL: {embeddings_url}")
    print(f"💾 로컬 파일: {loader.local_path}")
    
    # 로드 테스트
    data = loader.load_embeddings()
    
    if data:
        verses_count = len(data.get('verses', []))
        metadata = data.get('metadata', {})
        
        print(f"✅ 로드 성공!")
        print(f"📊 구절 수: {verses_count}")
        print(f"📋 메타데이터: {metadata}")
        
        # 메모리 사용량 확인
        memory_usage = MemoryManager.get_memory_usage()
        print(f"💾 메모리 사용량: {memory_usage:.1f}MB")
        
        return True
    else:
        print("❌ 로드 실패")
        return False

def main():
    """메인 실행 함수"""
    print("🚂 Railway 임베딩 로더 테스트")
    print("=" * 40)
    
    # 환경변수 확인
    embeddings_url = os.getenv('BIBLE_EMBEDDINGS_URL')
    if embeddings_url:
        print(f"환경변수 URL: {embeddings_url}")
    else:
        print("⚠️  BIBLE_EMBEDDINGS_URL 환경변수가 설정되지 않음")
    
    # 테스트 실행
    success = test_embedding_load()
    
    if success:
        print("\n🎉 테스트 성공!")
    else:
        print("\n❌ 테스트 실패")

if __name__ == "__main__":
    main()
