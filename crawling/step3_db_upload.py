import pandas as pd
import psycopg2
import glob
import os
from tqdm import tqdm

# DB 정보
DB_CONFIG = {
    "host": "localhost",
    "database": "complaint_db",
    "user": "postgres",
    "password": "0000",
    "port": "5432"
}

def upload_to_db():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("[*] DB 연결 성공. 업로드를 시작합니다.")

        vector_files = glob.glob("data/step2_vectors/*.parquet")

        for file_path in vector_files:
            # parquet 파일 읽기
            df = pd.read_parquet(file_path)
            print(f"\n[*] {os.path.basename(file_path)} 업로드 중...")

            # 배치 처리를 위해 iterrows 사용 (속도가 느리면 bulk insert로 변경 가능)
            for _, row in tqdm(df.iterrows(), total=len(df), desc="  └ DB Insert"):
                
                # 1. complaints 테이블 저장 (새로운 스키마 적용)
                # 없는 데이터(위도, 경도 등)는 제외하고 INSERT
                cursor.execute("""
                    INSERT INTO complaints (
                        received_at, title, body, answer, district, 
                        status, created_at, updated_at
                    )
                    VALUES (
                        NOW(), %s, %s, %s, %s, 
                        'CLOSED', NOW(), NOW()
                    ) RETURNING id;
                """, (
                    row.get('req_title', '제목없음'), 
                    row.get('req_content', ''), 
                    row.get('resp_content', ''), 
                    row.get('resp_dept', '')
                ))
                
                complaint_id = cursor.fetchone()[0]

                # 2. complaint_normalizations 테이블 저장
                # embedding 컬럼 하나에 통합 벡터를 넣습니다.
                # keywords_jsonb 등 AI 분석 필드는 현재 없으므로 일단 NULL 또는 기본값
                cursor.execute("""
                    INSERT INTO complaint_normalizations (
                        complaint_id, 
                        neutral_summary, 
                        embedding, 
                        is_current, 
                        created_at
                    ) VALUES (%s, %s, %s, true, NOW());
                """, (
                    complaint_id, 
                    row.get('processed_body', ''), # 요약본(전처리본) 저장
                    row['embedding'].tolist()      # ★ 통합 벡터 (1024차원)
                ))

            conn.commit() 
            print(f"[+] {os.path.basename(file_path)} 완료!")

    except Exception as e:
        print(f"[!] 오류 발생: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    upload_to_db()