

import configparser
from pykis.public_api import Api, DomainInfo
import traceback

print("--- KIS API 연결 테스트 시작 ---")

try:
    # 1. 설정 파일 읽기
    config = configparser.ConfigParser()
    config.read('config.cfg')

    app_key = config['kis']['APP_KEY']
    app_secret = config['kis']['APP_SECRET']
    account_no = config['kis']['ACCOUNT_NO']
    
    print(f"사용할 APP_KEY (앞 5자리): {app_key[:5]}...")
    print(f"사용할 계좌번호: {account_no}")

    # 2. 실전투자 환경 설정
    domain_info = DomainInfo(kind="real")
    
    key_info = {
        "appkey": app_key,
        "appsecret": app_secret
    }

    account_info = {
        "account_code": account_no.split('-')[0],
    }
    
    print(f"계좌번호 앞 8자리: {account_info['account_code']}")

    # 3. API 객체 초기화
    print("API 객체 초기화를 시도합니다...")
    print(key_info)
    api = Api(key_info=key_info, domain_info=domain_info, account_info=account_info)
    print("API 객체 초기화 완료.")

    # 4. 간단한 API 호출 (현재가 조회)
    stock_code = "005930" # 삼성전자
    print(f"삼성전자({stock_code}) 현재가 조회를 시도합니다...")
    
    price = api.get_kr_current_price(stock_code)
    
    print(f"성공적으로 현재가를 조회했습니다: {price}원")
    print("\n--- 테스트 성공! API 연결에 문제가 없습니다. ---")

except Exception as e:
    print("\n--- 테스트 실패! ---")
    print(f"오류가 발생했습니다: {e}")
    print("\n--- 상세 오류 정보 --- ")
    traceback.print_exc()

