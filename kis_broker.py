import datetime
import time
import configparser
from pykis.public_api import Api, DomainInfo

class MarketClosedError(Exception):
    """
    장이 열리지 않았을 때 발생하는 예외
    """
    pass

class KISBroker:
    """
    한국투자증권 API를 이용한 주식 거래 중개 클래스 (pykis 기반)
    """
    def __init__(self, mock=True):
        """
        KISBroker 클래스 초기화
        :param mock: True: 모의투자, False: 실전투자
        """
        if not self._is_market_open():
            raise MarketClosedError("장이 열리지 않은 시간에 KISBroker 객체를 생성할 수 없습니다.")

        config = configparser.ConfigParser()
        config.read('config.cfg')
        
        app_key = config['kis']['APP_KEY']
        app_secret = config['kis']['APP_SECRET']
        
        if mock:
            account_no = config['kis'].get('MOCK_ACCOUNT_NO')
        else:
            account_no = config['kis']['ACCOUNT_NO']

        domain_kind = "virtual" if mock else "real"
        domain_info = DomainInfo(kind=domain_kind)

        key_info = {
            "appkey": app_key,
            "appsecret": app_secret
        }

        account_info = {
            "account_code": account_no,
            "product_code": "01"
        }

        self.api = Api(key_info=key_info, domain_info=domain_info, account_info=account_info)
        print(f"KISBroker 초기화 완료. (모의투자: {mock})")

    def _is_market_open(self):
        """
        현재 시간이 주식 시장 운영 시간인지 확인합니다.
        (월-금, 9:00 - 15:30)
        """
        now = datetime.datetime.now()
        start_time = datetime.time(9, 0, 0)
        end_time = datetime.time(15, 30, 0)
        # Monday is 0 and Sunday is 6
        is_weekday = now.weekday() < 5 
        return is_weekday and start_time <= now.time() <= end_time

    def get_current_price(self, stock_code):
        """
        지정한 종목의 현재가를 조회합니다.
        :param stock_code: 종목코드 (예: "005930")
        :return: 현재가 (정수) 또는 조회 실패 시 None
        """
        if not self._is_market_open():
            raise MarketClosedError("장이 열리지 않아 현재가를 조회할 수 없습니다.")
        try:
            price = self.api.get_kr_current_price(stock_code)
            return price
        except Exception as e:
            print(f"현재가 조회 실패: {e}")
            return None

    def get_balance(self):
        """
        계좌의 잔고 정보를 조회합니다. (주식 잔고 및 현금 잔고)
        :return: 잔고 정보 DataFrame 또는 조회 실패 시 None
        """
        try:
            df = self.api.get_kr_stock_balance()
            return df
        except Exception as e:
            print(f"잔고 조회 실패: {e}")
            return None

    def buy(self, stock_code, quantity, price=0):
        """
        지정한 종목을 매수합니다.
        :param stock_code: 종목코드
        :param quantity: 주문 수량
        :param price: 주문 가격 (0으로 설정 시 시장가 주문)
        :return: 주문 결과 딕셔너리 또는 실패 시 None
        """
        if not self._is_market_open():
            raise MarketClosedError("장이 열리지 않아 매수할 수 없습니다.")
        order_type = "지정가" if price > 0 else "시장가"
        print(f"매수 주문: {stock_code} / {quantity}주 / {order_type}")
        try:
            response = self.api.buy_kr_stock(ticker=stock_code, order_amount=quantity, price=price)
            return response
        except Exception as e:
            print(f"매수 주문 실패: {e}")
            return None

    def sell(self, stock_code, quantity, price=0):
        """
        지정한 종목을 매도합니다.
        :param stock_code: 종목코드
        :param quantity: 주문 수량
        :param price: 주문 가격 (0으로 설정 시 시장가 주문)
        :return: 주문 결과 딕셔너리 또는 실패 시 None
        """
        if not self._is_market_open():
            raise MarketClosedError("장이 열리지 않아 매도할 수 없습니다.")
        order_type = "지정가" if price > 0 else "시장가"
        print(f"매도 주문: {stock_code} / {quantity}주 / {order_type}")
        try:
            response = self.api.sell_kr_stock(ticker=stock_code, order_amount=quantity, price=price)
            return response
        except Exception as e:
            print(f"매도 주문 실패: {e}")
            return None

    def get_order_status(self, order_id):
        """
        주문의 체결 상태를 확인합니다.
        :param order_id: 주문 ID (매수/매도 시 반환되는 odno)
        :return: '체결', '미체결', '확인불가'
        """
        if not self._is_market_open():
            raise MarketClosedError("장이 열리지 않아 주문 상태를 확인할 수 없습니다.")
        try:
            time.sleep(1)
            orders = self.api.get_kr_orders()
            
            if orders is None or orders.empty:
                return "체결"

            order_id = str(order_id)
            
            if order_id in orders.index:
                return "미체결"
            else:
                return "체결"

        except Exception as e:
            print(f"주문 상태 확인 실패: {e}")
            return "확인불가"

    def get_order_list(self):
        """
        미체결 주문 목록을 조회합니다.
        :return: 미체결 주문 목록 DataFrame 또는 조회 실패 시 None
        """
        if not self._is_market_open():
            raise MarketClosedError("장이 열리지 않아 미체결 주문 목록을 조회할 수 없습니다.")
        try:
            orders = self.api.get_orders()
            return orders
        except Exception as e:
            print(f"미체결 주문 조회 실패: {e}")
            return None

    def get_order_detail(self, order_id):
        """
        특정 주문의 상세 정보를 조회합니다.
        :param order_id: 주문 ID
        :return: 주문 상세 정보 딕셔너리 또는 조회 실패 시 None
        """
        if not self._is_market_open():
            raise MarketClosedError("장이 열리지 않아 주문 상세 정보를 조회할 수 없습니다.")
        try:
            order = self.api.get_order(order_id)
            return order
        except Exception as e:
            print(f"주문 상세 조회 실패: {e}")
            return None

    def cancel_order(self, order_id):
        """
        주문을 취소합니다.
        :param order_id: 주문 ID
        :return: 주문 취소 결과 딕셔너리 또는 실패 시 None
        """
        if not self._is_market_open():
            raise MarketClosedError("장이 열리지 않아 주문을 취소할 수 없습니다.")
        try:
            response = self.api.cancel_order(order_id)
            return response
        except Exception as e:
            print(f"주문 취소 실패: {e}")
            return None

    def get_account_info(self):
        """
        계좌 정보를 조회합니다.
        :return: 계좌 정보 딕셔너리 또는 조회 실패 시 None
        """
        try:
            account_info = self.api.get_account_info()
            return account_info
        except Exception as e:
            print(f"계좌 정보 조회 실패: {e}")
            return None

    def get_stock_info(self, stock_code):
        """
        지정한 종목의 정보를 조회합니다.
        :param stock_code: 종목코드
        :return: 종목 정보 딕셔너리 또는 조회 실패 시 None
        """
        try:
            stock_info = self.api.get_stock_info(stock_code)
            return stock_info
        except Exception as e:
            print(f"종목 정보 조회 실패: {e}")
            return None

    def get_daily_price(self, stock_code, start_date, end_date):
        """
        지정한 종목의 일별 시세를 조회합니다.
        :param stock_code: 종목코드
        :param start_date: 조회 시작일 (YYYYMMDD)
        :param end_date: 조회 종료일 (YYYYMMDD)
        :return: 일별 시세 DataFrame 또는 조회 실패 시 None
        """
        try:
            df = self.api.get_daily_price(stock_code, start_date, end_date)
            return df
        except Exception as e:
            print(f"일별 시세 조회 실패: {e}")
            return None

    def get_minute_price(self, stock_code, start_time, end_time):
        """
        지정한 종목의 분봉 데이터를 조회합니다.
        :param stock_code: 종목코드
        :param start_time: 조회 시작 시간 (HHMMSS)
        :param end_time: 조회 종료 시간 (HHMMSS)
        :return: 분봉 데이터 DataFrame 또는 조회 실패 시 None
        """
        try:
            df = self.api.get_minute_price(stock_code, start_time, end_time)
            return df
        except Exception as e:
            print(f"분봉 데이터 조회 실패: {e}")
            return None

    def get_orderbook(self, stock_code):
        """
        지정한 종목의 호가 정보를 조회합니다.
        :param stock_code: 종목코드
        :return: 호가 정보 딕셔너리 또는 조회 실패 시 None
        """
        try:
            orderbook = self.api.get_orderbook(stock_code)
            return orderbook
        except Exception as e:
            print(f"호가 정보 조회 실패: {e}")
            return None

    def get_market_status(self):
        """
        현재 시장 상태를 조회합니다. (개장, 폐장, 장중 등)
        :return: 시장 상태 문자열 또는 조회 실패 시 None
        """
        try:
            status = self.api.get_market_status()
            return status
        except Exception as e:
            print(f"시장 상태 조회 실패: {e}")
            return None

    def get_account_balance(self):
        """
        계좌 잔고를 조회합니다.
        :return: 계좌 잔고 DataFrame 또는 조회 실패 시 None
        """
        try:
            balance = self.api.get_balance()
            return balance
        except Exception as e:
            print(f"계좌 잔고 조회 실패: {e}")
            return None


if __name__ == '__main__':
    try:
        broker = KISBroker(mock=False)

        balance = broker.get_balance()
        if balance is not None:
            print("\n--- 초기 잔고 ---")
            print(balance.to_string())

        samsung_price = broker.get_current_price("005930")
        if samsung_price:
            print(f"\n--- 삼성전자 현재가: {samsung_price}원 ---")

            buy_result = broker.buy("005930", 1)
            if buy_result:
                print("\n--- 매수 주문 결과 ---")
                print(buy_result)
                
                order_id = buy_result['odno']
                status = broker.get_order_status(order_id)
                print(f"\n--- 주문({order_id}) 체결 상태: {status} ---")

        balance_after_buy = broker.get_balance()
        if balance_after_buy is not None:
            print("\n--- 매수 후 잔고 ---")
            print(balance_after_buy.to_string())

    except MarketClosedError as e:
        print(f"오류 발생: {e}")