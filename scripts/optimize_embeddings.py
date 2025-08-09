#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
성경 임베딩 파일 최적화 스크립트
514MB → 25MB 이하로 압축
"""

import json
import gzip
import numpy as np
import os
from typing import List, Dict, Any

def optimize_bible_embeddings():
    """성경 임베딩 파일을 Railway 배포용으로 최적화"""
    
    input_file = r"C:\Users\user\Desktop\ai-bible-assistant\bible_embeddings.json"
    
    print("🔄 성경 임베딩 파일 최적화 시작...")
    print(f"📁 원본 파일 크기: {os.path.getsize(input_file) / (1024*1024):.2f} MB")
    
    # 1단계: 원본 파일 로드 (JSONL 형태 지원)
    print("\n📖 원본 파일 로딩...")
    data = []
    
    try:
        # 먼저 일반 JSON 시도
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ JSON 배열 형태로 로딩 성공")
    except json.JSONDecodeError:
        # JSONL 형태로 다시 시도
        print("🔄 JSONL 형태로 재시도...")
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                if line.strip():  # 빈 줄 무시
                    try:
                        item = json.loads(line.strip())
                        data.append(item)
                        
                        # 진행률 표시 (1000줄마다)
                        if line_num % 1000 == 0:
                            print(f"로딩 중... {line_num + 1} 줄")
                    except json.JSONDecodeError as e:
                        print(f"⚠️ {line_num + 1}번째 줄 파싱 오류: {e}")
                        continue
        print("✅ JSONL 형태로 로딩 성공")
    
    print(f"📊 총 구절 수: {len(data)}")
    print(f"📊 임베딩 차원: {len(data[0]['embedding']) if data else 'N/A'}")
    
    # 2단계: 임베딩 벡터 정밀도 감소 (float64 → float16)
    print("\n🔧 임베딩 벡터 정밀도 최적화...")
    optimized_data = []
    
    for i, item in enumerate(data):
        # 진행률 표시
        if i % 1000 == 0:
            print(f"진행률: {i}/{len(data)} ({i/len(data)*100:.1f}%)")
        
        # 임베딩 벡터를 float16으로 변환 (메모리 50% 절약)
        embedding_array = np.array(item['embedding'], dtype=np.float16)
        
        optimized_item = {
            'id': item['id'],
            'embedding': embedding_array.tolist(),
            'text': item['text'],
            'book': item['book'],
            'chapter': item['chapter'],
            'verse': item['verse']
        }
        optimized_data.append(optimized_item)
    
    # 3단계: JSON 압축 저장
    print("\n💾 압축 파일 저장...")
    compressed_file = "bible_embeddings_optimized.json.gz"
    
    with gzip.open(compressed_file, 'wt', encoding='utf-8') as f:
        json.dump(optimized_data, f, separators=(',', ':'), ensure_ascii=False)
    
    # 4단계: 결과 확인
    compressed_size = os.path.getsize(compressed_file)
    compression_ratio = (1 - compressed_size / os.path.getsize(input_file)) * 100
    
    print(f"\n✅ 최적화 완료!")
    print(f"📁 압축 파일 크기: {compressed_size / (1024*1024):.2f} MB")
    print(f"📉 압축률: {compression_ratio:.1f}%")
    
    # 5단계: Railway 호환성 체크
    if compressed_size < 25 * 1024 * 1024:  # 25MB
        print("✅ Railway 배포 적합 (25MB 이하)")
    else:
        print("⚠️  추가 최적화 필요 (25MB 초과)")
        
        # 추가 최적화: 파일 분할
        print("\n🔄 파일 분할 진행...")
        split_large_file(optimized_data)
    
    return compressed_file

def split_large_file(data: List[Dict[str, Any]]):
    """큰 파일을 여러 개로 분할"""
    
    chunk_size = len(data) // 4  # 4개 파일로 분할
    
    for i in range(4):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size if i < 3 else len(data)
        
        chunk_data = data[start_idx:end_idx]
        chunk_file = f"bible_embeddings_part_{i+1}.json.gz"
        
        with gzip.open(chunk_file, 'wt', encoding='utf-8') as f:
            json.dump(chunk_data, f, separators=(',', ':'), ensure_ascii=False)
        
        chunk_size_mb = os.path.getsize(chunk_file) / (1024*1024)
        print(f"📦 Part {i+1}: {chunk_size_mb:.2f} MB ({len(chunk_data)} 구절)")

def create_index_file(data: List[Dict[str, Any]]):
    """빠른 검색을 위한 인덱스 파일 생성"""
    
    index_data = []
    for item in data:
        index_item = {
            'id': item['id'],
            'text': item['text'],
            'book': item['book'],
            'chapter': item['chapter'],
            'verse': item['verse']
        }
        index_data.append(index_item)
    
    with gzip.open('bible_index.json.gz', 'wt', encoding='utf-8') as f:
        json.dump(index_data, f, separators=(',', ':'), ensure_ascii=False)
    
    index_size = os.path.getsize('bible_index.json.gz') / (1024*1024)
    print(f"📚 인덱스 파일: {index_size:.2f} MB")

def test_optimized_file():
    """최적화된 파일 테스트"""
    
    print("\n🧪 최적화 파일 테스트...")
    
    try:
        with gzip.open('bible_embeddings_optimized.json.gz', 'rt', encoding='utf-8') as f:
            test_data = json.load(f)
        
        print(f"✅ 로딩 성공: {len(test_data)} 구절")
        print(f"📊 첫 번째 구절: {test_data[0]['text']}")
        print(f"📊 임베딩 차원: {len(test_data[0]['embedding'])}")
        
        # 임베딩 벡터 복원 테스트
        embedding = np.array(test_data[0]['embedding'], dtype=np.float32)
        print(f"📊 임베딩 범위: {embedding.min():.3f} ~ {embedding.max():.3f}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    # 메인 최적화 실행
    optimized_file = optimize_bible_embeddings()
    
    # 테스트 실행
    test_optimized_file()
    
    print("\n🎯 다음 단계:")
    print("1. 생성된 .gz 파일을 GitHub Releases에 업로드")
    print("2. 다운로드 URL을 환경변수에 설정")
    print("3. Railway 배포 진행")
    
    print(f"\n📋 생성된 파일들:")
    for file in ['bible_embeddings_optimized.json.gz', 'bible_index.json.gz']:
        if os.path.exists(file):
            size = os.path.getsize(file) / (1024*1024)
            print(f"  - {file}: {size:.2f} MB")