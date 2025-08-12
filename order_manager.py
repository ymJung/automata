import time
import configparser
from kis_broker import KISBroker, MarketClosedError
from telegram_bot import TelegramBot
from portfolio import Portfolio

# 설정 파일 로드
config = configparser.ConfigParser()
config.read('config.cfg')

try:
    # 주문 관리자 설정
    order_params = config['order']
    TOTAL_INVESTMENT_PER_STOCK = order_params.getfloat('total_investment_per_stock', 100000) # 종목당 총 투자금액
    DCA_DIVISIONS = order_params.getint('dca_divisions', 3) # 분할매수 횟수
    
    # 텔레그램 설정
    telegram_params = config['telegram']
    TELEGRAM_TOKEN = telegram_params.get('token')
    TELEGRAM_CHAT_ID = telegram_params.get('chat_id')

except KeyError as e:
    print(f"order_manager.py: config.cfg 파일에서 [{e.args[0]}] 섹션을 찾을 수 없습니다. 기본값을 사용합니다.")
    TOTAL_INVESTMENT_PER_STOCK = 100000
    DCA_DIVISIONS = 3
    TELEGRAM_TOKEN = None
    TELEGRAM_CHAT_ID = None

class OrderManager:
    """
    전략에 따라 주문을 실행하고 관리하며, 결과를 텔레그램으로 알립니다.
    """
    def __init__(self, broker: KISBroker, portfolio: Portfolio):
        self.broker = broker
        self.portfolio = portfolio
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            self.telegram_bot = TelegramBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        else:
            self.telegram_bot = None

    def _send_telegram_message(self, message: str):
        """ 텔레그램 메시지를 전송합니다. """
        print(f"[텔레그램] {message}")
        if self.telegram_bot:
            try:
                self.telegram_bot.send_message(message)
            except Exception as e:
                print(f"텔레그램 메시지 전송 실패: {e}")

    def execute_buy_order(self, stock_code: str):
        """
        DCA 전략에 따라 매수 주문을 실행합니다.
        :param stock_code: 매수할 종목 코드
        """
        try:
            # 1. 현재 가격 조회
            current_price = self.broker.get_current_price(stock_code)
            if not current_price:
                print(f"[{stock_code}] 현재가 조회에 실패하여 매수를 진행할 수 없습니다.")
                return

            # 2. DCA를 위한 투자 금액 및 수량 계산
            investment_amount_per_buy = TOTAL_INVESTMENT_PER_STOCK / DCA_DIVISIONS
            quantity_to_buy = int(investment_amount_per_buy // current_price)

            if quantity_to_buy == 0:
                print(f"[{stock_code}] 주문 가능 수량이 0이므로 매수를 진행하지 않습니다.")
                return

            # 3. 현금 잔고 확인
            if self.portfolio.cash < investment_amount_per_buy:
                self._send_telegram_message(f"[매수 실패] {stock_code} - 현금 부족\n- 필요 금액: {investment_amount_per_buy:,.0f}원\n- 현재 잔고: {self.portfolio.cash:,.0f}원")
                return

            # 4. 매수 주문 실행 (시장가)
            order_result = self.broker.buy(stock_code, quantity_to_buy)
            if not order_result or 'odno' not in order_result:
                self._send_telegram_message(f"[매수 주문 실패] {stock_code} - API 오류")
                return

            # 5. 주문 체결 확인 및 포트폴리오 업데이트
            time.sleep(5) # 체결 대기
            order_id = order_result['odno']
            order_status = self.broker.get_order_status(order_id)

            if order_status == '체결':
                # 정확한 체결가는 API 응답에서 확인해야 하지만, pykis 예제에서는 현재가로 근사
                self.portfolio.update_on_buy(stock_code, quantity_to_buy, current_price)
                self._send_telegram_message(f"[매수 체결] {stock_code}\n- 수량: {quantity_to_buy}주\n- 가격: {current_price:,.0f}원")
            else:
                self.broker.cancel_order(order_id) # 미체결 주문은 취소
                self._send_telegram_message(f"[매수 미체결] {stock_code} - 주문이 체결되지 않아 취소되었습니다.")

        except MarketClosedError:
            print("장이 종료되어 매수 주문을 실행할 수 없습니다.")
        except Exception as e:
            self._send_telegram_message(f"[매수 오류] {stock_code} - {e}")

    def execute_sell_order(self, stock_code: str):
        """
        보유 주식 전량을 매도합니다.
        :param stock_code: 매도할 종목 코드
        """
        holding = self.portfolio.get_holding(stock_code)
        if not holding or holding['quantity'] == 0:
            print(f"[{stock_code}] 보유 수량이 없어 매도를 진행할 수 없습니다.")
            return

        quantity_to_sell = holding['quantity']

        try:
            # 1. 현재 가격 조회
            current_price = self.broker.get_current_price(stock_code)
            if not current_price:
                print(f"[{stock_code}] 현재가 조회에 실패하여 매도를 진행할 수 없습니다.")
                return

            # 2. 매도 주문 실행 (시장가)
            order_result = self.broker.sell(stock_code, quantity_to_sell)
            if not order_result or 'odno' not in order_result:
                self._send_telegram_message(f"[매도 주문 실패] {stock_code} - API 오류")
                return

            # 3. 주문 체결 확인 및 포트폴리오 업데이트
            time.sleep(5) # 체결 대기
            order_id = order_result['odno']
            order_status = self.broker.get_order_status(order_id)

            if order_status == '체결':
                self.portfolio.update_on_sell(stock_code, quantity_to_sell, current_price)
                self._send_telegram_message(f"[매도 체결] {stock_code}\n- 수량: {quantity_to_sell}주\n- 가격: {current_price:,.0f}원")
            else:
                self.broker.cancel_order(order_id)
                self._send_telegram_message(f"[매도 미체결] {stock_code} - 주문이 체결되지 않아 취소되었습니다.")

        except MarketClosedError:
            print("장이 종료되어 매도 주문을 실행할 수 없습니다.")
        except Exception as e:
            self._send_telegram_message(f"[매도 오류] {stock_code} - {e}")
