import sys
import traceback
from datetime import datetime


def current_date() -> str:
    """
    현재 날짜와 시간을 문자열로 반환합니다.

    Returns:
        str: 연-월-일 시:분:초 형식의 시간 문자열
    """
    now = datetime.now()
    ret = now.strftime("%Y-%m-%d %H:%M:%S")

    return ret


def print_err(text):
    """
    오류 메시지를 출력합니다. (except 구문에 넣어서 사용)

    Args:
        text (str): 출력할 문장
    """
    print('\033[91m' + f"{current_date()} | {text}" + f"\n{traceback.format_exc()}" + '\033[0m', file=sys.stderr)
