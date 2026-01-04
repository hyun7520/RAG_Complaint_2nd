import requests
import json

OLLAMA_URL = "http://localhost:11434/api"

async def get_normalization(body: str):
    """LLM을 호출하여 민원을 정규화된 JSON 구조로 변환합니다."""
    prompt = f"""
    당신은 민원 분석 전문가입니다. 다음 민원을 분석하여 반드시 JSON 형식으로만 응답하세요. 
    - neutral_summary: 감정이 배제된 객관적 사실 요약
    - core_request: 핵심 요구사항
    - core_cause: 발생 원인 추정
    - target_object: 민원 대상물 (예: 가로등, 맨홀 등)
    - keywords: 핵심 키워드 5개 (배열)

    민원 내용: {body}
    """
    
    response = requests.post(f"{OLLAMA_URL}/generate", json={
        "model": "llama3.1", "prompt": prompt, "format": "json", "stream": False
    })
    if response.status_code == 200:
        # JSON 문자열 내부의 응답 텍스트를 파싱
        return json.loads(response.json()['response'])
    else:
        raise Exception(f"Ollama API Error: {response.text}")

async def get_embedding(text: str):
    """텍스트를 벡터로 변환합니다. (설계상 1024차원 필요) """
    # 주의: 사용 중인 모델의 차원이 1024인지 확인 필수!
    response = requests.post(f"{OLLAMA_URL}/embeddings", json={
        "model": "mxbai-embed-large", "prompt": text
    })
    if response.status_code == 200:
        return response.json()['embedding']
    else:
        raise Exception(f"Ollama Embedding Error: {response.text}")