def check_status_code(status_code):
    """
    HTTP 상태 코드를 받아 해당하는 의미를 반환하는 함수
    
    Args:
        status_code (int): HTTP 상태 코드
        
    Returns:
        str: 상태 코드에 해당하는 의미
    """
    status_messages = {
        200: "성공 (OK)",
        301: "영구 이동 (리디렉션)",
        302: "임시 이동 (리디렉션)",
        400: "잘못된 요청 (Bad Request)",
        403: "접근 금지 (Forbidden)",
        404: "페이지 없음 (Not Found)",
        500: "서버 오류 (Internal Server Error)"
    }
    
    return status_messages.get(status_code, f"알 수 없는 상태 코드: {status_code}")

# 사용 예시
if __name__ == "__main__":
    print(check_status_code(200))  # "성공 (OK)" 출력
    print(check_status_code(404))  # "페이지 없음 (Not Found)" 출력
    print(check_status_code(999))  # "알 수 없는 상태 코드: 999" 출력
