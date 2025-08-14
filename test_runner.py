import pandas as pd
from kis_broker import KISBroker, MarketClosedError
from indicators import add_all_indicators
from stock_selector import screen_stocks
from strategy import check_buy_signal, check_sell_signal
from portfolio import Portfolio
from order_manager import OrderManager

def get_sample_dataframe(rows=40):
    """ 테스트에 사용할 샘플 데이터프레임을 생성합니다. """
    return pd.DataFrame({
        'code': ['005930'] * rows,
        'close': [100 + i + (10 if i > 35 else 0) for i in range(rows)],
        'volume': [10000 * (1.5 if i > 38 else 1) for i in range(rows)]
    })

def test_kis_broker():
    """ kis_broker.py 기능 테스트 """
    print("--- KISBroker 모듈 테스트 시작 ---")
    try:
        broker = KISBroker(mock=True)
        
        # 1. 현재가 조회
        price = broker.get_current_price("005930")
        if price:
            print(f"[성공] 삼성전자 현재가: {price}원")
        else:
            print("[실패] 삼성전자 현재가 조회")

        # 2. 잔고 조회
        balance = broker.get_balance()
        if balance is not None:
            print(f"[성공] 계좌 잔고 조회 완료")
            # print(balance)
        else:
            print("[실패] 계좌 잔고 조회")
            
    except MarketClosedError as e:
        print(f"[정보] {e}")
    except Exception as e:
        print(f"[오류] KISBroker 테스트 중 예외 발생: {e}")
    print("--- KISBroker 모듈 테스트 종료 ---\n")

def test_indicators():
    """ indicators.py 기능 테스트 """
    print("--- Indicators 모듈 테스트 시작 ---")
    df = get_sample_dataframe()
    df_with_indicators = add_all_indicators(df)
    print("[성공] 모든 기술적 지표 추가 완료")
    print("추가된 컬럼:", [col for col in df_with_indicators.columns if col not in df.columns])
    # print(df_with_indicators.tail())
    print("--- Indicators 모듈 테스트 종료 ---\n")

def test_stock_selector():
    """ stock_selector.py 기능 테스트 """
    print("--- StockSelector 모듈 테스트 시작 ---")
    # stock_selector는 내부적으로 indicators를 사용하므로, 별도 데이터 생성 불필요
    sample_codes = ['005930', '000660', '035720']
    selected = screen_stocks(sample_codes)
    print(f"[완료] 종목 스크리닝 완료. 선정된 종목: {selected}")
    print("--- StockSelector 모듈 테스트 종료 ---\n")

def test_strategy():
    """ strategy.py 기능 테스트 """
    print("--- Strategy 모듈 테스트 시작 ---")
    df = get_sample_dataframe()
    df = add_all_indicators(df)
    
    # 매수 신호 테스트
    df.loc[len(df)-1, 'ewo'] = 6
    df.loc[len(df)-1, 'rsi'] = 45
    buy_signal, reason = check_buy_signal(df)
    print(f"매수 신호 테스트 (기대: True): {buy_signal}, 이유: {reason}")

    # 매도 신호 테스트
    avg_price = 100
    df.loc[len(df)-1, 'close'] = 110 # 100 * 1.05 = 105
    sell_signal, reason = check_sell_signal(df, avg_price)
    print(f"매도 신호 테스트 (기대: True): {sell_signal}, 이유: {reason}")
    print("--- Strategy 모듈 테스트 종료 ---\n")

def test_portfolio_and_order_manager():
    """ portfolio.py 및 order_manager.py 기능 테스트 """
    print("--- Portfolio & OrderManager 모듈 테스트 시작 ---")
    try:
        broker = KISBroker(mock=True)
        
        # 1. 포트폴리오 초기화 테스트
        portfolio = Portfolio(broker)
        print("[성공] 포트폴리오 초기화 완료")
        
        # 2. 주문 관리자 초기화 테스트
        order_manager = OrderManager(broker, portfolio)
        print("[성공] 주문 관리자 초기화 완료")

        # 3. 매수/매도 실행 테스트 (실제 주문은 발생하지 않도록 주의)
        # 아래 라인은 실제 주문을 유발할 수 있으므로, 개념 테스트로만 남겨둡니다.
        print("\n[정보] 매수/매도 테스트는 실제 주문을 유발할 수 있어 실행되지 않습니다.")
        print("order_manager.execute_buy_order('005930') 형태의 코드를 직접 실행하여 테스트할 수 있습니다.")
        # order_manager.execute_buy_order('005930')
        # order_manager.execute_sell_order('005930')

    except MarketClosedError as e:
        print(f"[정보] {e}")
    except Exception as e:
        print(f"[오류] 테스트 중 예외 발생: {e}")
    print("--- Portfolio & OrderManager 모듈 테스트 종료 ---\n")


if __name__ == '__main__':
    while True:
        print("=== 자동매매 시스템 단위 테스트 ===")
        print("1. KISBroker (API 연동)")
        print("2. Indicators (기술적 지표 계산)")
        print("3. StockSelector (종목 선정)")
        print("4. Strategy (매매 신호 결정)")
        print("5. Portfolio & OrderManager (계좌 관리 및 주문 실행)")
        print("0. 종료")
        
        choice = input("테스트할 기능을 선택하세요: ")
        
        if choice == '1':
            test_kis_broker()
        elif choice == '2':
            test_indicators()
        elif choice == '3':
            test_stock_selector()
        elif choice == '4':
            test_strategy()
        elif choice == '5':
            test_portfolio_and_order_manager()
        elif choice == '0':
            print("테스트를 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택해주세요.")