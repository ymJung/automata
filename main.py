import time
from datetime import datetime
import pandas as pd

from kis_broker import KISBroker, MarketClosedError
from indicators import add_all_indicators
from strategy import check_buy_signal, check_sell_signal
from portfolio import Portfolio
from order_manager import OrderManager
from stock_selector import screen_stocks

# --- 설정 ---
# 장이 열려있을 때 매매 로직을 실행하는 주기 (초)
LOOP_INTERVAL_SECONDS = 10  # 5분

# 매수 후보 종목 리스트는 동적으로 조회
CANDIDATE_STOCK_CODES = []

def run_trading_bot():
    """ 자동매매 봇의 메인 로직을 실행합니다. """
    print(f"[{datetime.now()}] 자동매매 시스템을 시작합니다.")

    try:
        # 1. 모든 컴포넌트 초기화 (실전 투자 모드)
        broker = KISBroker(mock=True, force_open=True)
        portfolio = Portfolio(broker)
        order_manager = OrderManager(broker, portfolio)

        order_manager._send_telegram_message("자동매매 시스템이 시작되었습니다.")
        print("초기화 완료. 메인 루프를 시작합니다.")
        
        # 전체 상장 종목 조회 (시스템 시작 시 한 번만)
        all_stocks = broker.get_all_listed_stocks()
        global CANDIDATE_STOCK_CODES
        CANDIDATE_STOCK_CODES = [stock['code'] for stock in all_stocks]
        print(f"매수 후보 종목 {len(CANDIDATE_STOCK_CODES)}개 로드 완료")

        # --- 메인 루프 ---
        while True:
            # 실전투자 모드에서만 장 시간 확인
            if not broker.mock and not broker._is_market_open():
                print(f"[{datetime.now()}] 장이 열리지 않았습니다. 다음 개장까지 대기합니다.")
                # 실제 운영 시에는 다음 날 개장 시간까지 대기하는 로직이 필요합니다.
                # 여기서는 테스트를 위해 1시간 대기 후 재시도합니다.
                time.sleep(3600)
                continue

            print(f"\n[{datetime.now()}] 새로운 매매 주기를 시작합니다.")
            
            # 2. 포트폴리오 최신화 (실시간 계좌 잔고 반영)
            portfolio.update_from_broker()

            # 3. 보유 종목 매도 신호 확인
            print("\n--- 보유 종목 매도 신호 확인 ---")
            holdings_to_check = list(portfolio.holdings.keys())
            for stock_code in holdings_to_check:
                holding_details = portfolio.get_holding(stock_code)
                if not holding_details or holding_details['quantity'] == 0:
                    continue
                
                print(f"[{stock_code} ({holding_details['name']})] 확인 중...")
                
                # 일봉 데이터 가져오기 (최근 60일치로 지표 계산)
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - pd.Timedelta(days=60)).strftime('%Y%m%d')
                df = broker.get_daily_price(stock_code, start_date=start_date, end_date=end_date)

                if df is None or df.empty:
                    print(f"[{stock_code}] 시세 데이터 조회에 실패했습니다.")
                    continue
                
                # 데이터 전처리 (컬럼명 변경 및 타입 변환)
                df.rename(columns={'stck_clpr': 'close', 'acml_vol': 'volume'}, inplace=True)
                df['close'] = pd.to_numeric(df['close'])
                df['volume'] = pd.to_numeric(df['volume'])
                
                df_with_indicators = add_all_indicators(df.copy())
                
                sell_signal, reason = check_sell_signal(df_with_indicators, holding_details['avg_price'])
                if sell_signal:
                    order_manager._send_telegram_message(f"[매도 신호] {stock_code}\n- 사유: {reason}")
                    order_manager.execute_sell_order(stock_code)
                else:
                    print(f"[{stock_code}] 매도 신호 없음.")

            # 4. 종목 스크리닝 (매 주기마다 실행하면 부하가 클 수 있으므로 필요시 주기 조정)
            print("\n--- 종목 스크리닝 실행 ---")
            screened_stocks = screen_stocks(CANDIDATE_STOCK_CODES[:10], broker)  # 처음 10개 종목만 스크리닝
            print(f"스크리닝 결과: {len(screened_stocks)}개 종목 선정")
            
            # 5. 신규 종목 매수 신호 확인
            print("\n--- 신규 매수 대상 종목 확인 ---")
            # 스크리닝된 종목 + 기존 후보 종목 중 일부를 확인
            stocks_to_check = list(set(screened_stocks + CANDIDATE_STOCK_CODES[:5]))
            
            for stock_code in stocks_to_check:
                if stock_code in portfolio.holdings:
                    print(f"[{stock_code}] 이미 보유 중인 종목이므로 건너뜁니다.")
                    continue

                print(f"[{stock_code}] 확인 중...")
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - pd.Timedelta(days=60)).strftime('%Y%m%d')
                df = broker.get_daily_price(stock_code, start_date=start_date, end_date=end_date)

                if df is None or df.empty:
                    print(f"[{stock_code}] 시세 데이터 조회에 실패했습니다.")
                    continue
                
                df.rename(columns={'stck_clpr': 'close', 'acml_vol': 'volume'}, inplace=True)
                df['close'] = pd.to_numeric(df['close'])
                df['volume'] = pd.to_numeric(df['volume'])

                df_with_indicators = add_all_indicators(df.copy())
                
                buy_signal, reason = check_buy_signal(df_with_indicators)
                if buy_signal:
                    order_manager._send_telegram_message(f"[매수 신호] {stock_code}\n- 사유: {reason}")
                    order_manager.execute_buy_order(stock_code)
                else:
                    print(f"[{stock_code}] 매수 신호 없음.")

            # 6. 다음 주기까지 대기
            print(f"\n[{datetime.now()}] 모든 작업 완료. {LOOP_INTERVAL_SECONDS}초 후 다음 주기를 시작합니다.")
            time.sleep(LOOP_INTERVAL_SECONDS)

    except MarketClosedError:
        msg = "장이 종료되어 자동매매 시스템을 중지합니다."
        print(f"[{datetime.now()}] {msg}")
        if 'order_manager' in locals() and order_manager.telegram_bot:
            order_manager._send_telegram_message(msg)
    except KeyboardInterrupt:
        msg = "사용자에 의해 자동매매 시스템이 중지되었습니다."
        print(f"[{datetime.now()}] {msg}")
        if 'order_manager' in locals() and order_manager.telegram_bot:
            order_manager._send_telegram_message(msg)
    except Exception as e:
        msg = f"자동매매 시스템에 심각한 오류가 발생하여 중지되었습니다.\n오류: {e}"
        print(f"[{datetime.now()}] {msg}")
        if 'order_manager' in locals() and order_manager.telegram_bot:
            order_manager._send_telegram_message(msg)

if __name__ == "__main__":
    run_trading_bot()