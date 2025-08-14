import datetime
import time
import configparser
import requests
import json

class MarketClosedError(Exception):
    """
    장이 열리지 않았을 때 발생하는 예외
    """
    pass

class KISBroker:
    """
    한국투자증권 API를 이용한 주식 거래 중개 클래스 (공식 REST API 기반)
    """
    def __init__(self, mock=True, force_open=False):
        """
        KISBroker 클래스 초기화
        :param mock: True: 모의투자, False: 실전투자
        :param force_open: True: 시장 개장 시간을 무시하고 항상 실행
        """
        self.mock = mock
        self.force_open = force_open
        
        # 모의투자 모드에서는 시장 시간 체크를 하지 않음
        if not mock and not self._is_market_open():
            raise MarketClosedError("장이 열리지 않은 시간에 KISBroker 객체를 생성할 수 없습니다.")

        config = configparser.ConfigParser()
        config.read('config.cfg')
        
        self.app_key = config['kis']['APP_KEY']
        self.app_secret = config['kis']['APP_SECRET']
        
        if mock:
            self.account_no = config['kis'].get('MOCK_ACCOUNT_NO')
            self.base_url = "https://openapivts.koreainvestment.com:29443"  # 모의투자 URL
        else:
            self.account_no = config['kis']['ACCOUNT_NO']
            self.base_url = "https://openapi.koreainvestment.com:9443"  # 실전투자 URL
        
        # 계좌번호 분리 (앞8자리-뒤2자리)
        account_parts = self.account_no.split('-')
        self.account_number = account_parts[0]
        self.account_product_cd = account_parts[1]
        
        # 접근토큰 초기화
        self.access_token = None
        self.token_expired = True
        self.token_file = "access_token.txt"
        
        # 토큰 발급 (캐시된 토큰이 있으면 재사용)
        self._load_cached_token()
        if self.token_expired or not self.access_token:
            self._get_access_token()
        
        print(f"KISBroker 초기화 완료. (모의투자: {mock})")
        if mock:
            print("📝 모의투자 모드: 24시간 테스트 가능합니다.")

    def _load_cached_token(self):
        """
        캐시된 토큰을 로드합니다.
        """
        try:
            import os
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    
                # 토큰 만료 시간 확인 (24시간)
                import time
                if time.time() - token_data.get('timestamp', 0) < 86400:  # 24시간
                    self.access_token = token_data.get('access_token')
                    self.token_expired = False
                    print("✅ 캐시된 토큰 사용")
                    return
                    
            self.token_expired = True
        except Exception as e:
            print(f"캐시된 토큰 로드 실패: {e}")
            self.token_expired = True

    def _save_token_cache(self):
        """
        토큰을 캐시 파일에 저장합니다.
        """
        try:
            import time
            token_data = {
                'access_token': self.access_token,
                'timestamp': time.time()
            }
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f)
        except Exception as e:
            print(f"토큰 캐시 저장 실패: {e}")

    def _get_access_token(self):
        """
        한국투자증권 API 접근토큰을 발급받습니다.
        """
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {
            "content-type": "application/json"
        }
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                result = response.json()
                self.access_token = result["access_token"]
                self.token_expired = False
                self._save_token_cache()
                print("✅ 접근토큰 발급 성공")
            else:
                print(f"❌ 접근토큰 발급 실패: {response.status_code}, {response.text}")
                raise Exception(f"토큰 발급 실패: {response.text}")
        except Exception as e:
            print(f"❌ 토큰 발급 중 오류: {e}")
            raise

    def _get_headers(self, tr_id, custtype="P"):
        """
        API 호출용 헤더를 생성합니다.
        """
        if self.token_expired or not self.access_token:
            self._get_access_token()
            
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": custtype
        }

    def _is_market_open(self):
        """
        현재 시간이 주식 시장 운영 시간인지 확인합니다.
        (월-금, 9:00 - 15:30)
        모의투자 모드에서는 항상 True를 반환합니다.
        """
        # 모의투자 모드에서는 24시간 테스트 가능
        if hasattr(self, 'mock') and self.mock:
            return True
            
        # force_open 옵션이 설정된 경우
        if hasattr(self, 'force_open') and self.force_open:
            return True
            
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
        if not self.mock and not self._is_market_open():
            raise MarketClosedError("장이 열리지 않아 현재가를 조회할 수 없습니다.")
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self._get_headers("FHKST01010100")
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                result = response.json()
                if result["rt_cd"] == "0":  # 성공
                    current_price = int(result["output"]["stck_prpr"])
                    return current_price
                else:
                    print(f"현재가 조회 실패: {result['msg1']}")
                    return None
            else:
                print(f"현재가 조회 HTTP 오류: {response.status_code}")
                return None
        except Exception as e:
            print(f"현재가 조회 실패: {e}")
            return None

    def get_balance(self):
        """
        계좌의 잔고 정보를 조회합니다. (주식 잔고 및 현금 잔고)
        :return: 잔고 정보 딕셔너리 또는 조회 실패 시 None
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        headers = self._get_headers("TTTC8434R")
        params = {
            "CANO": self.account_number,
            "ACNT_PRDT_CD": self.account_product_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                result = response.json()
                if result["rt_cd"] == "0":  # 성공
                    return {
                        "output1": result["output1"],  # 보유종목 리스트
                        "output2": result["output2"]   # 계좌 요약정보
                    }
                else:
                    print(f"잔고 조회 실패: {result['msg1']}")
                    return None
            else:
                print(f"잔고 조회 HTTP 오류: {response.status_code}")
                return None
        except Exception as e:
            print(f"잔고 조회 실패: {e}")
            return None

    def get_daily_price(self, stock_code, start_date, end_date):
        """
        지정한 종목의 일별 시세를 조회합니다.
        :param stock_code: 종목코드
        :param start_date: 조회 시작일 (YYYYMMDD)
        :param end_date: 조회 종료일 (YYYYMMDD)
        :return: 일별 시세 DataFrame 또는 조회 실패 시 None
        """
        import pandas as pd
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        headers = self._get_headers("FHKST03010100")
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
            "fid_input_date_1": start_date,
            "fid_input_date_2": end_date,
            "fid_period_div_code": "D",
            "fid_org_adj_prc": "1"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                result = response.json()
                if result["rt_cd"] == "0":  # 성공
                    data = result["output2"]
                    if data:
                        df = pd.DataFrame(data)
                        # 날짜 순서를 오름차순으로 정렬 (과거 -> 현재)
                        df = df.sort_values('stck_bsop_date').reset_index(drop=True)
                        return df
                    else:
                        print("일봉 데이터가 없습니다.")
                        return None
                else:
                    print(f"일봉 데이터 조회 실패: {result['msg1']}")
                    return None
            else:
                print(f"일봉 데이터 조회 HTTP 오류: {response.status_code}")
                return None
        except Exception as e:
            print(f"일별 시세 조회 실패: {e}")
            return None

    def get_all_listed_stocks(self):
        """
        우량주 위주의 매매 대상 종목을 조회합니다.
        KOSPI 200, 시가총액 상위, 거래량 상위 종목들을 포함합니다.
        :return: 종목 정보 리스트
        """
        # 우량주 위주 확장 리스트 (약 100개 종목)
        blue_chip_stocks = [
            # 대형주 (시가총액 10조 이상)
            {'code': '005930', 'name': '삼성전자', 'sector': 'IT'},
            {'code': '000660', 'name': 'SK하이닉스', 'sector': 'IT'},
            {'code': '207940', 'name': '삼성바이오로직스', 'sector': '바이오'},
            {'code': '005380', 'name': '현대차', 'sector': '자동차'},
            {'code': '006400', 'name': '삼성SDI', 'sector': '배터리'},
            {'code': '051910', 'name': 'LG화학', 'sector': '화학'},
            {'code': '035420', 'name': 'NAVER', 'sector': 'IT'},
            {'code': '068270', 'name': '셀트리온', 'sector': '바이오'},
            {'code': '035720', 'name': '카카오', 'sector': 'IT'},
            {'code': '003670', 'name': '포스코홀딩스', 'sector': '철강'},
            
            # 금융주
            {'code': '105560', 'name': 'KB금융', 'sector': '금융'},
            {'code': '055550', 'name': '신한지주', 'sector': '금융'},
            {'code': '086790', 'name': '하나금융지주', 'sector': '금융'},
            {'code': '316140', 'name': '우리금융지주', 'sector': '금융'},
            {'code': '138040', 'name': '메리츠금융지주', 'sector': '금융'},
            {'code': '024110', 'name': '기업은행', 'sector': '금융'},
            
            # 통신주
            {'code': '017670', 'name': 'SK텔레콤', 'sector': '통신'},
            {'code': '030200', 'name': 'KT', 'sector': '통신'},
            {'code': '032640', 'name': 'LG유플러스', 'sector': '통신'},
            
            # 에너지/화학
            {'code': '096770', 'name': 'SK이노베이션', 'sector': '에너지'},
            {'code': '009150', 'name': '삼성전기', 'sector': '전자부품'},
            {'code': '010950', 'name': 'S-Oil', 'sector': '에너지'},
            {'code': '011170', 'name': '롯데케미칼', 'sector': '화학'},
            {'code': '001570', 'name': '금양', 'sector': '화학'},
            
            # 소비재/유통
            {'code': '051900', 'name': 'LG생활건강', 'sector': '생활용품'},
            {'code': '097950', 'name': 'CJ제일제당', 'sector': '식품'},
            {'code': '271560', 'name': '오리온', 'sector': '식품'},
            {'code': '004170', 'name': '신세계', 'sector': '유통'},
            {'code': '023530', 'name': '롯데쇼핑', 'sector': '유통'},
            {'code': '139480', 'name': '이마트', 'sector': '유통'},
            
            # 건설/부동산
            {'code': '000720', 'name': '현대건설', 'sector': '건설'},
            {'code': '028050', 'name': '삼성물산', 'sector': '건설'},
            {'code': '047040', 'name': '대우건설', 'sector': '건설'},
            {'code': '001040', 'name': 'CJ', 'sector': '지주회사'},
            
            # 제약/바이오
            {'code': '326030', 'name': 'SK바이오팜', 'sector': '제약'},
            {'code': '196170', 'name': '알테오젠', 'sector': '바이오'},
            {'code': '302440', 'name': 'SK바이오사이언스', 'sector': '바이오'},
            {'code': '000100', 'name': '유한양행', 'sector': '제약'},
            {'code': '009420', 'name': '한올바이오파마', 'sector': '제약'},
            
            # 전자/반도체
            {'code': '066570', 'name': 'LG전자', 'sector': '전자'},
            {'code': '000270', 'name': '기아', 'sector': '자동차'},
            {'code': '012330', 'name': '현대모비스', 'sector': '자동차부품'},
            {'code': '034730', 'name': 'SK', 'sector': '지주회사'},
            {'code': '018260', 'name': '삼성에스디에스', 'sector': 'IT서비스'},
            
            # 중견 우량주
            {'code': '033780', 'name': 'KT&G', 'sector': '담배'},
            {'code': '015760', 'name': '한국전력', 'sector': '전력'},
            {'code': '090430', 'name': '아모레퍼시픽', 'sector': '화장품'},
            {'code': '161390', 'name': '한국타이어앤테크놀로지', 'sector': '타이어'},
            {'code': '036570', 'name': '엔씨소프트', 'sector': '게임'},
            {'code': '251270', 'name': '넷마블', 'sector': '게임'},
            {'code': '112040', 'name': '위메이드', 'sector': '게임'},
            
            # 항공/운송
            {'code': '003490', 'name': '대한항공', 'sector': '항공'},
            {'code': '020560', 'name': '아시아나항공', 'sector': '항공'},
            {'code': '180640', 'name': '한진칼', 'sector': '지주회사'},
            
            # 엔터테인먼트
            {'code': '041510', 'name': 'SM', 'sector': '엔터테인먼트'},
            {'code': '122870', 'name': 'YG엔터테인먼트', 'sector': '엔터테인먼트'},
            {'code': '035900', 'name': 'JYP Ent.', 'sector': '엔터테인먼트'},
            
            # 2차전지/신재생에너지
            {'code': '373220', 'name': 'LG에너지솔루션', 'sector': '배터리'},
            {'code': '247540', 'name': '에코프로비엠', 'sector': '배터리소재'},
            {'code': '086520', 'name': '에코프로', 'sector': '배터리소재'},
            {'code': '003550', 'name': 'LG', 'sector': '지주회사'},
            
            # 반도체 장비/소재
            {'code': '042700', 'name': '한미반도체', 'sector': '반도체장비'},
            {'code': '000990', 'name': '동부하이텍', 'sector': '반도체'},
            {'code': '058470', 'name': '리노공업', 'sector': '반도체장비'},
            
            # 디스플레이
            {'code': '034220', 'name': 'LG디스플레이', 'sector': '디스플레이'},
            {'code': '009540', 'name': 'HD한국조선해양', 'sector': '조선'},
            {'code': '010140', 'name': '삼성중공업', 'sector': '조선'},
            
            # 물류/유통
            {'code': '000120', 'name': 'CJ대한통운', 'sector': '물류'},
            {'code': '028670', 'name': '팬오션', 'sector': '해운'},
            
            # 바이오/헬스케어
            {'code': '214150', 'name': '클래시스', 'sector': '바이오'},
            {'code': '145020', 'name': '휴젤', 'sector': '바이오'},
            {'code': '185750', 'name': '종근당', 'sector': '제약'},
            
            # 식품/음료
            {'code': '004000', 'name': '롯데지주', 'sector': '지주회사'},
            {'code': '001680', 'name': '대상', 'sector': '식품'},
            {'code': '280360', 'name': '롯데웰푸드', 'sector': '식품'},
            
            # 미디어/콘텐츠
            {'code': '130960', 'name': '씨젠', 'sector': '진단키트'},
            {'code': '064350', 'name': '현대로템', 'sector': '철도차량'},
            {'code': '267250', 'name': '현대중공업', 'sector': '조선'},
            
            # 기타 우량 중소형주
            {'code': '192820', 'name': '코스맥스', 'sector': '화장품'},
            {'code': '018880', 'name': '한온시스템', 'sector': '자동차부품'},
            {'code': '204320', 'name': '만도', 'sector': '자동차부품'},
            {'code': '307950', 'name': '현대오토에버', 'sector': 'IT서비스'},
            {'code': '005490', 'name': 'POSCO홀딩스', 'sector': '철강'},
            {'code': '003230', 'name': '삼양식품', 'sector': '식품'},
            {'code': '006800', 'name': '미래에셋증권', 'sector': '증권'},
            {'code': '039490', 'name': '키움증권', 'sector': '증권'},
            {'code': '016360', 'name': 'LS', 'sector': '지주회사'},
            {'code': '010120', 'name': 'LS ELECTRIC', 'sector': '전기장비'}
        ]
        
        # 설정 파일에서 필터링 옵션 읽기
        try:
            config = configparser.ConfigParser()
            config.read('config.cfg')
            
            if 'stock_filter' in config:
                filter_config = config['stock_filter']
                max_stocks = filter_config.getint('max_stocks_to_analyze', 50)
                enable_sector_filter = filter_config.getboolean('enable_sector_filter', True)
                
                if enable_sector_filter:
                    preferred_sectors = [s.strip() for s in filter_config.get('preferred_sectors', '').split(',') if s.strip()]
                    exclude_sectors = [s.strip() for s in filter_config.get('exclude_sectors', '').split(',') if s.strip()]
                    
                    # 섹터 필터링 적용
                    if preferred_sectors:
                        blue_chip_stocks = [stock for stock in blue_chip_stocks if stock.get('sector', '') in preferred_sectors]
                        print(f"선호 섹터 필터링 적용: {preferred_sectors}")
                    
                    if exclude_sectors:
                        blue_chip_stocks = [stock for stock in blue_chip_stocks if stock.get('sector', '') not in exclude_sectors]
                        print(f"제외 섹터 필터링 적용: {exclude_sectors}")
                
                # 최대 종목 수 제한
                if len(blue_chip_stocks) > max_stocks:
                    blue_chip_stocks = blue_chip_stocks[:max_stocks]
                    print(f"최대 종목 수 제한 적용: {max_stocks}개")
                    
        except Exception as e:
            print(f"종목 필터링 설정 읽기 실패: {e}")
        
        print(f"최종 매매 대상 종목 {len(blue_chip_stocks)}개를 반환합니다.")
        return blue_chip_stocks

    # 간단한 매수/매도 함수들 (기본 구현)
    def buy(self, stock_code, quantity, price=0):
        print(f"매수 주문: {stock_code} / {quantity}주 (모의투자 모드)")
        return {"odno": "12345", "ord_tmd": "153000"}

    def sell(self, stock_code, quantity, price=0):
        print(f"매도 주문: {stock_code} / {quantity}주 (모의투자 모드)")
        return {"odno": "12346", "ord_tmd": "153000"}

    def get_order_status(self, order_id):
        return "체결"

    def cancel_order(self, order_id):
        print(f"주문 취소: {order_id}")
        return None