import psycopg2
from psycopg2.extras import Json
import os
from dotenv import load_dotenv

load_dotenv()

# DB 연결 정보 (환경 변수 또는 .env 활용 권장)
DB_CONFIG = {
    "dbname": "complaint_db",
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": "localhost",
    "port": 5432
}

def save_complaint(title, body, district=None, address_text=None):
    """민원 원본 내용을 저장하는 함수"""
    conn = psycopg2.connect(**DB_CONFIG, client_encoding='UTF8')
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO complaints (title, body, district, address_text, received_at) 
            VALUES (%s, %s, %s, %s, now())
            RETURNING id
        """, (title, body, district, address_text))
        
        complaint_id = cur.fetchone()[0]
        conn.commit()
        print(f"[*] 민원 {complaint_id} 원본 데이터 저장 완료")
        return complaint_id
    except Exception as e:
        conn.rollback()
        print(f"[!] 민원 저장 중 에러: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

def save_normalization(complaint_id, analysis, embedding):
    """
    1. 기존 데이터의 is_current를 false로 업데이트 
    2. 새로운 정규화 데이터 및 임베딩 벡터 저장 
    """
    conn = psycopg2.connect(**DB_CONFIG, client_encoding='UTF8')
    cur = conn.cursor()
    
    try:
        

        cur.execute("""
            INSERT INTO complaint_normalizations (
                complaint_id, 
                neutral_summary, 
                core_request, 
                core_cause, 
                target_object, 
                keywords_jsonb, 
                location_hint,
                urgency_signal,
                embedding, 
                is_current
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true)
        """, (
            complaint_id, 
            analysis.get('neutral_summary'), 
            analysis.get('core_request'), 
            analysis.get('core_cause'), 
            analysis.get('target_object'), 
            Json(analysis.get('keywords', [])), # 리스트를 JSONB로 변환
            analysis.get('location_hint'),      # 추가된 컬럼
            analysis.get('urgency_signal'),    # 추가된 컬럼
            embedding                           # 1024차원 리스트
        ))
        
        conn.commit()
        print(f"[*] 민원 {complaint_id} 정규화 데이터 저장 완료")
    except Exception as e:
        conn.rollback()
        print(f"[!] 정규화 데이터 저장 중 에러: {e}")
        raise e
    finally:
        cur.close()
        conn.close()