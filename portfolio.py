import pandas as pd
from kis_broker import KISBroker

class Portfolio:
    """
    포트폴리오 상태를 관리하는 클래스. (보유 현금, 주식, 평균 단가 등)
    """
    def __init__(self, broker: KISBroker):
        """
        포트폴리오 초기화.
        :param broker: KISBroker 인스턴스
        """
        self.broker = broker
        self.cash = 0
        self.holdings = {}  # { '종목코드': {'name': '종목명', 'quantity': 수량, 'avg_price': 평단, 'current_price': 현재가, 'eval_amount': 평가금액}, ... }
        self.update_from_broker()

    def update_from_broker(self):
        """
        브로커 API를 통해 실제 계좌 잔고를 가져와 포트폴리오를 최신 상태로 업데이트합니다.
        """
        balance = self.broker.get_balance()
        if balance is None or 'output1' not in balance or 'output2' not in balance:
            print("계좌 잔고를 가져오는 데 실패했습니다.")
            return

        # 주식 잔고 업데이트
        stock_balance = balance['output1']
        self.holdings = {}
        for stock in stock_balance:
            code = stock['pdno']
            self.holdings[code] = {
                'name': stock['prdt_name'],
                'quantity': int(stock['hldg_qty']),
                'avg_price': float(stock['pchs_avg_pric']),
                'current_price': float(stock['prpr']),
                'eval_amount': int(stock['evlu_amt'])
            }
        
        # 현금 잔고 업데이트
        cash_balance = balance['output2']
        self.cash = int(cash_balance['dnca_tot_amt'])
        
        print("포트폴리오가 계좌 실시간 잔고로 업데이트되었습니다.")
        print(self)

    def update_on_buy(self, stock_code: str, quantity: int, price: float):
        """
        매수 체결 후 포트폴리오 상태를 업데이트합니다.
        :param stock_code: 매수한 종목 코드
        :param quantity: 매수한 수량
        :param price: 매수 체결 가격
        """
        if stock_code in self.holdings:
            # 기존 보유 종목 추가 매수
            existing_holding = self.holdings[stock_code]
            total_quantity = existing_holding['quantity'] + quantity
            total_value = (existing_holding['quantity'] * existing_holding['avg_price']) + (quantity * price)
            new_avg_price = total_value / total_quantity
            
            existing_holding['quantity'] = total_quantity
            existing_holding['avg_price'] = new_avg_price
        else:
            # 신규 종목 매수
            self.holdings[stock_code] = {
                'name': 'Unknown', # 종목명은 추후 업데이트 필요
                'quantity': quantity,
                'avg_price': price,
            }
        
        # 현금 차감
        self.cash -= quantity * price
        print(f"[매수] {stock_code} {quantity}주 @ {price}원. 포트폴리오 업데이트 완료.")
        print(self)

    def update_on_sell(self, stock_code: str, quantity: int, price: float):
        """
        매도 체결 후 포트폴리오 상태를 업데이트합니다.
        :param stock_code: 매도한 종목 코드
        :param quantity: 매도한 수량
        :param price: 매도 체결 가격
        """
        if stock_code not in self.holdings or self.holdings[stock_code]['quantity'] < quantity:
            print(f"[오류] 매도 수량({quantity})이 보유 수량보다 많습니다.")
            return

        # 보유 수량 차감
        self.holdings[stock_code]['quantity'] -= quantity
        
        # 전량 매도 시 holdings에서 제거
        if self.holdings[stock_code]['quantity'] == 0:
            del self.holdings[stock_code]
            
        # 현금 증가
        self.cash += quantity * price
        print(f"[매도] {stock_code} {quantity}주 @ {price}원. 포트폴리오 업데이트 완료.")
        print(self)

    def get_holding(self, stock_code: str) -> dict | None:
        """ 특정 종목의 보유 정보를 반환합니다. """
        return self.holdings.get(stock_code)

    def __str__(self):
        holdings_str = "\n".join([f"  - {code} ({details['name']}): {details['quantity']}주 @ 평단 {details['avg_price']:.0f}원" for code, details in self.holdings.items()])
        return f"--- 포트폴리오 현황 ---\n현금: {self.cash:,}원\n보유 주식:\n{holdings_str}\n----------------------"