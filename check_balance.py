from pykoreainvestment import KoreaInvestment
import configparser

# 설정 파일 읽기
config = configparser.ConfigParser()
config.read('config.cfg')

# KIS API 객체 생성
api = KoreaInvestment(
    app_key=config['kis']['APP_KEY'],
    app_secret=config['kis']['APP_SECRET'],
    account_no=config['kis']['ACCOUNT_NO'],
    mock=True  # 모의투자 계좌일 경우 True, 실제 계좌는 False
)

# 잔고 조회
balance = api.get_balance()

# 결과 출력
print("--- 주식 잔고 ---")
for stock in balance['output1']:
    print(f"종목명: {stock['prdt_name']}, 보유수량: {stock['hldg_qty']}, 평가금액: {stock['evlu_amt']}원")

print("\n--- 현금 잔고 ---")
print(f"예수금: {balance['output2']['dnca_tot_amt']}원")
