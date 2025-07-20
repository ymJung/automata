import time
from pykoreainvestment import KoreaInvestment
import configparser

class KISBroker:
    """
    한국투자증권 API를 이용한 주식 거래 중개 클래스
    """
    def __init__(self, mock=True):
        """
        KISBroker 클래스 초기화
        :param mock: True: 모의투자, False: 실전투자
        """
        config = configparser.ConfigParser()
        config.read('config.cfg')
        self.api = KoreaInvestment(
            app_key=config['kis']['APP_KEY'],
            app_secret=config['kis']['APP_SECRET'],
            account_no=config['kis']['ACCOUNT_NO'],
            mock=mock
        )
        print(f"KISBroker 초기화 완료. (모의투자: {mock})")

    def get_current_price(self, stock_code):
        """
        지정한 종목의 현재가를 조회합니다.
        :param stock_code: 종목코드 (예: "005930")
        :return: 현재가 (정수) 또는 조회 실패 시 None
        """
        try:
            response = self.api.get_current_price(stock_code)
            return int(response['output']['stck_prpr'])
        except Exception as e:
            print(f"현재가 조회 실패: {e}")
            return None

    def get_balance(self):
        """
        계좌의 잔고 정보를 조회합니다. (주식 잔고 및 현금 잔고)
        :return: 잔고 정보 딕셔너리 또는 조회 실패 시 None
        """
        try:
            response = self.api.get_balance()
            return response
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
        order_type = "지정가" if price > 0 else "시장가"
        print(f"매수 주문: {stock_code} / {quantity}주 / {order_type}")
        try:
            # 시장가 주문의 경우 price를 0으로 설정
            response = self.api.buy(stock_code=stock_code, quantity=quantity, price=price)
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
        order_type = "지정가" if price > 0 else "시장가"
        print(f"매도 주문: {stock_code} / {quantity}주 / {order_type}")
        try:
            response = self.api.sell(stock_code=stock_code, quantity=quantity, price=price)
            return response
        except Exception as e:
            print(f"매도 주문 실패: {e}")
            return None

    def get_order_status(self, order_id, is_buy=True):
        """
        주문의 체결 상태를 확인합니다.
        :param order_id: 주문 ID (매수/매도 시 반환되는 KRX_FWDG_ORD_ORGNO)
        :param is_buy: True: 매수 주문, False: 매도 주문
        :return: '체결', '미체결', '확인불가'
        """
        try:
            # KIS API는 주문 리스트 조회를 통해 체결 여부를 확인해야 합니다.
            # 여기서는 단순화를 위해 특정 주문 번호가 체결 리스트에 있는지 확인합니다.
            # 실제 구현 시에는 더 정교한 로직이 필요할 수 있습니다.
            time.sleep(1) # 주문 후 체결까지 시간이 걸릴 수 있으므로 잠시 대기
            orders = self.api.get_order_list()
            
            for order in orders['output']:
                if order['odno'] == order_id:
                    return "체결" if "체결" in order['ord_tmd_result_nm'] else "미체결"
            return "미체결" # 주문 목록에 없으면 미체결로 간주
        except Exception as e:
            print(f"주문 상태 확인 실패: {e}")
            return "확인불가"


if __name__ == '__main__':
    # 아래 코드는 KISBroker 클래스의 사용 예시입니다.
    # 이 파일을 직접 실행하면 아래 로직이 동작합니다.
    
    # 1. 브로커 객체 생성 (모의투자)
    broker = KISBroker(mock=True)

    # 2. 잔고 확인
    balance = broker.get_balance()
    if balance:
        print("\n--- 초기 잔고 ---")
        print(balance)

    # 3. 삼성전자(005930) 현재가 조회
    samsung_price = broker.get_current_price("005930")
    if samsung_price:
        print(f"\n--- 삼성전자 현재가: {samsung_price}원 ---")

        # 4. 삼성전자 1주 시장가 매수
        buy_result = broker.buy("005930", 1)
        if buy_result:
            print("\n--- 매수 주문 결과 ---")
            print(buy_result)
            
            # 5. 주문 체결 여부 확인
            order_id = buy_result['output']['KRX_FWDG_ORD_ORGNO']
            status = broker.get_order_status(order_id, is_buy=True)
            print(f"\n--- 주문({order_id}) 체결 상태: {status} ---")

    # 6. 변경된 잔고 확인
    balance_after_buy = broker.get_balance()
    if balance_after_buy:
        print("\n--- 매수 후 잔고 ---")
        print(balance_after_buy)
