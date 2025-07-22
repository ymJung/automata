## 프로젝트 작업 목록 상세화

---

### 1. 환경 설정 및 초기화

이 단계는 프로젝트를 시작하기 위한 기본적인 환경을 세팅하고 필수 파일들을 준비하는 과정입니다.

* **`config.cfg.sample` 파일을 `config.cfg`로 복사합니다.**
    * **입력값**: `config.cfg.sample` 파일 (템플릿)
    * **반환값**: `config.cfg` 파일 (사용자 설정값을 입력할 빈 파일)
* **`config.cfg` 파일에 실제 API 키와 계좌번호를 설정합니다.**
    * **입력값**: 한국투자증권 개발자 센터에서 발급받은 실제 API Key, API Secret, 그리고 연동할 계좌번호. (사용자가 직접 입력)
    * **반환값**: API 인증 정보와 계좌 정보가 포함된 `config.cfg` 파일.
* **`.gitignore` 파일에 `config.cfg`가 포함되어 있는지 확인하여 민감한 정보가 유출되지 않도록 합니다.**
    * **입력값**: 프로젝트의 `.gitignore` 파일.
    * **반환값**: `config.cfg`가 버전 관리에서 제외되었는지 확인. (실제 파일 반환은 없음, 상태 확인)
* **`pykoreainvestment` 라이브러리를 설치합니다.**
    * **입력값**: Python 환경.
    * **반환값**: `pykoreainvestment` 라이브러리 설치 완료. (실제 반환은 없음, 라이브러리 사용 가능 상태)

---

### 2. 한국투자증권 API 연동 모듈 개발 (`kis_broker.py`)

이 모듈은 한국투자증권 API와 상호작용하는 모든 기능을 담당합니다.

* **`config.cfg` 파일에서 설정값을 읽어오는 기능을 구현합니다.**
    * **함수**: `load_config()`
    * **입력값**: `config.cfg` 파일 경로.
    * **반환값**: API 키, Secret, 계좌번호 등 설정값이 담긴 **딕셔너리 또는 객체**.
* **API 인증 및 접속을 처리하는 기능을 구현합니다.**
    * **함수**: `authenticate_api(app_key, app_secret, account_no)`
    * **입력값**: `load_config()`에서 반환된 `app_key`, `app_secret`, `account_no`.
    * **반환값**: API 세션 객체 또는 접속 성공/실패 여부를 나타내는 **불리언 값과 메시지**. (예: `True`, `False`, `error_message`)
* **주식 현재가, 호가, 계좌 잔고 등 필요한 정보를 조회하는 함수를 구현합니다.**
    * **함수**: `get_current_price(stock_code)`, `get_order_book(stock_code)`, `get_account_balance(account_no)`
    * **입력값**:
        * `get_current_price`: `stock_code` (종목 코드, 예: '005930')
        * `get_order_book`: `stock_code`
        * `get_account_balance`: `account_no`
    * **반환값**:
        * `get_current_price`: **현재가, 전일 대비, 등락률 등 종목 현재 정보 딕셔너리**.
        * `get_order_book`: **매도/매수 10호가 정보 딕셔너리**.
        * `get_account_balance`: **예수금, 평가 금액, 보유 종목 리스트 등 계좌 잔고 정보 딕셔너리**.
* **주식 주문(매수/매도)을 실행하는 함수를 구현합니다.**
    * **함수**: `place_order(order_type, stock_code, quantity, price, order_division, account_no)`
    * **입력값**:
        * `order_type`: 'buy' (매수) 또는 'sell' (매도).
        * `stock_code`: 종목 코드.
        * `quantity`: 주문 수량.
        * `price`: 주문 가격 (시장가 주문 시 0).
        * `order_division`: '00' (지정가), '01' (시장가) 등.
        * `account_no`: 계좌번호.
    * **반환값**: 주문 성공/실패 여부, 주문 번호, 체결 메시지 등이 담긴 **딕셔너리**.
* **분봉/일봉 등 시세 데이터를 가져오는 함수를 구현합니다.**
    * **함수**: `get_ohlcv_data(stock_code, interval, count)`
    * **입력값**:
        * `stock_code`: 종목 코드.
        * `interval`: 'D' (일봉), 'M' (분봉, 예: '5분봉'이면 '5') 등.
        * `count`: 가져올 데이터 개수.
    * **반환값**: **날짜/시간, 시가, 고가, 저가, 종가, 거래량 등의 시계열 데이터 프레임(Pandas DataFrame) 또는 리스트**.
* **전체 상장 종목 코드 및 기본 정보 (시가총액, 거래량 등)를 조회하는 함수를 구현합니다.**
    * **함수**: `get_all_listed_stocks()`
    * **입력값**: 없음 (API 인증 정보는 내부적으로 활용).
    * **반환값**: **종목 코드, 종목명, 시가총액, 상장 주식 수 등 전체 상장 종목의 기본 정보가 담긴 리스트 또는 데이터 프레임**.

---

### 3. 기술적 지표 계산 로직 구현 (`indicators.py`)

이 모듈은 주어진 시세 데이터를 바탕으로 다양한 기술적 지표를 계산합니다.

* **주어진 시세 데이터를 바탕으로 다음 지표를 계산하는 함수들을 별도의 파일(`indicators.py`)로 만듭니다.**
    * **함수**: `calculate_ema(data, period)`, `calculate_rsi(data, period)`, `calculate_ewo(data, short_period, long_period)`, `calculate_macd(data, fast_period, slow_period, signal_period)`, `calculate_bollinger_bands(data, period, num_std_dev)`
    * **입력값**:
        * `data`: 시가, 고가, 저가, 종가, 거래량 등을 포함하는 Pandas DataFrame (컬럼명 명확화 필요).
        * `period`, `short_period`, `long_period`, `fast_period`, `slow_period`, `signal_period`, `num_std_dev` 등 각 지표에 필요한 계산 주기 및 파라미터.
    * **반환값**: 입력된 데이터프레임에 **계산된 지표(EMA, RSI, EWO, MACD, Bollinger Bands) 컬럼이 추가된 DataFrame**.
* **데이터 누락 여부 확인 로직**
    * **함수**: `check_missing_data(data_frame)`
    * **입력값**: 시세 데이터 프레임.
    * **반환값**: **데이터 누락 여부 (불리언) 및 누락된 부분에 대한 정보 (리스트 또는 메시지)**.

---

### 4. 종목 선정 로직 구현 (`stock_selector.py` 또는 `strategy.py` 내)

이 모듈은 기술적 지표를 활용하여 공격적인 투자에 적합한 종목을 동적으로 발굴합니다.

* **공격적인 투자를 위한 기술적 지표 기반 종목 스크리닝 로직을 구현합니다.**
    * **함수**: `screen_aggressive_stocks(all_stocks_data, config_params)`
    * **입력값**:
        * `all_stocks_data`: `kis_broker.py`에서 가져온 **전체 상장 종목의 기본 정보와 기술적 지표가 추가된 데이터프레임**.
        * `config_params`: `config.cfg`에서 읽어온 스크리닝 관련 설정값 (예: `RSI_LOWER_THRESHOLD`, `VOLUME_INCREASE_FACTOR`, `GOLDEN_CROSS_SHORT_PERIOD`, `GOLDEN_CROSS_LONG_PERIOD` 등).
    * **반환값**: **스크리닝 조건을 만족하는 종목 코드 리스트**.
* **`kis_broker.py`를 통해 가져온 전체 종목 데이터를 활용합니다.**
    * (위 `screen_aggressive_stocks` 함수의 `all_stocks_data` 입력값에 포함됨)
* **`indicators.py`에서 계산된 기술적 지표를 바탕으로 다음 조건들을 만족하는 종목을 필터링합니다.**
    * **단기 이동평균선(예: 5일)이 장기 이동평균선(예: 20일)을 상향 돌파하는 골든 크로스 발생 종목.**
    * **RSI가 과매도 구간(예: 30 이하)에서 상승 전환하는 종목.**
    * **평균 거래량 대비 급증한 거래량이 동반된 종목.**
    * **주가가 볼린저 밴드 상단 밴드를 돌파하는 종목.**
    * **MACD 선이 시그널 선을 상향 돌파하는 종목.**
    * (이 조건들은 `screen_aggressive_stocks` 함수 내부 로직에 포함됨)
* **스크리닝된 종목 리스트를 `main.py`의 매매 루프에서 활용할 수 있도록 관리합니다.**
    * (스크리닝 함수의 반환값을 `main.py`에서 사용)
* **`config.cfg`에서 종목 스크리닝을 위한 파라미터 (예: RSI 기준값, 거래량 급증 배율 등)를 설정할 수 있도록 합니다.**
    * (위 `screen_aggressive_stocks` 함수의 `config_params` 입력값에 포함됨)

---

### 5. 매매 전략 구현 (`strategy.py`)

이 모듈은 API 모듈과 지표 계산 모듈, 종목 선정 모듈을 사용하여 실제 매매 시점을 결정합니다.

* **API 모듈과 지표 계산 모듈, 그리고 종목 선정 모듈을 사용하여 매매 시점을 결정하는 로직을 구현합니다.**
* **매수 조건**
    * **함수**: `check_buy_signal(stock_data, current_holdings, config_params)`
    * **입력값**:
        * `stock_data`: **종목 선정 로직에서 필터링된 개별 종목의 최신 시세 데이터 및 기술적 지표**.
        * `current_holdings`: 현재 계좌에 보유 중인 종목 정보 (평균 단가, 수량 등).
        * `config_params`: `config.cfg`에서 읽어온 매수 조건 관련 설정값 (`Low Offset` 등).
    * **반환값**: **매수 신호 발생 여부 (불리언) 및 매수 수량/가격 제안 (딕셔너리)**.
    * `README.md`에 명시된 두 가지 매수 조건을 확인하는 함수를 구현합니다.
    * `Low Offset`과 같은 파라미터를 설정 파일에서 읽어와 유연하게 조정할 수 있도록 합니다.
    * **종목 선정 로직에서 필터링된 종목들을 대상으로 매수 신호를 판단합니다.** (이 로직은 `check_buy_signal` 함수 내부에 포함)
* **매도 조건**
    * **함수**: `check_sell_signal(stock_data, holding_info, config_params)`
    * **입력값**:
        * `stock_data`: **보유 중인 개별 종목의 최신 시세 데이터 및 기술적 지표**.
        * `holding_info`: 해당 종목의 매수 가격, 현재 수량 등 보유 정보.
        * `config_params`: `config.cfg`에서 읽어온 매도 조건 관련 설정값 (`High Offset`, 손절매 비율 등).
    * **반환값**: **매도 신호 발생 여부 (불리언) 및 매도 수량/가격 제안 (딕셔너리)**.
    * `High Offset`을 이용한 이익 실현 매도 조건을 구현합니다.
    * 매수 가격 대비 -35% 하락 시 손절매하는 로직을 구현합니다.

---

### 6. 주문 실행 및 관리 로직 구현

이 모듈은 매매 전략에 따라 결정된 주문을 실제로 실행하고, 보유 종목을 관리합니다.

* **매매 전략에 따라 결정된 주문을 실제로 실행하는 로직을 구현합니다.**
    * **함수**: `execute_trade(order_details, kis_broker_instance)`
    * **입력값**:
        * `order_details`: `strategy.py`에서 반환된 매수/매도 정보 (종목코드, 수량, 가격, 주문 유형 등).
        * `kis_broker_instance`: `kis_broker.py`의 API 연동 객체.
    * **반환값**: **주문 결과 (성공/실패, 주문 번호, 체결 정보 등 딕셔너리)**.
* **DCA(분할 매수) 전략을 구현합니다. (예: 3분할 주문)**
    * **함수**: `manage_dca_buy(stock_code, total_amount_to_invest, num_divisions, current_step)`
    * **입력값**:
        * `stock_code`: 분할 매수할 종목 코드.
        * `total_amount_to_invest`: 총 투자할 금액.
        * `num_divisions`: 분할 횟수.
        * `current_step`: 현재 분할 매수 단계.
    * **반환값**: **현재 단계에서 매수할 수량 및 가격 정보**.
* **현재 보유 종목, 평균 단가, 주문 상태 등을 추적하고 관리하는 기능을 구현합니다.**
    * **함수**: `update_portfolio(trade_result, current_portfolio)`
    * **입력값**:
        * `trade_result`: `execute_trade`에서 반환된 주문 결과.
        * `current_portfolio`: 현재 시스템이 관리하는 보유 종목 및 주문 내역 상태.
    * **반환값**: **업데이트된 포트폴리오 상태 딕셔너리**.

---

### 7. 메인 실행 로직 및 자동화 구현 (`main.py`)

이 모듈은 위에서 만든 모든 모듈들을 조립하고, 전체 자동매매 프로세스를 주기적으로 실행합니다.

* **위에서 만든 모듈들을 모두 가져와 전체 프로세스를 조립합니다.**
* **일정 주기로 (예: 5분마다) 다음 작업을 반복 실행하는 메인 루프를 만듭니다.**
    * **함수**: `main_loop()`
    * **입력값**: 없음 (내부적으로 각 모듈 호출).
    * **반환값**: 없음 (지속적으로 실행).
    * **세부 프로세스**:
        1.  **정기적인 종목 스크리닝 실행 및 매매 대상 종목 리스트 업데이트 (예: 매일 장 시작 전 또는 주기적으로)**
            * **입력값**: `kis_broker` 인스턴스, `config_params`.
            * **반환값**: **업데이트된 매매 대상 종목 코드 리스트 (`trade_candidates`)**.
        2.  **매매 대상 종목의 최신 시세 데이터 가져오기**
            * **입력값**: `trade_candidates` 리스트.
            * **반환값**: **각 종목의 최신 시세 데이터 (`latest_data_per_stock`)**.
        3.  기술적 지표 계산하기
            * **입력값**: `latest_data_per_stock`.
            * **반환값**: **지표가 추가된 시세 데이터 (`data_with_indicators`)**.
        4.  매매 전략에 따라 매수/매도 신호 판단하기
            * **입력값**: `data_with_indicators`, 현재 보유 종목 정보.
            * **반환값**: **발생한 매수/매도 신호 정보 (주문 상세 정보)**.
        5.  신호 발생 시 주문 실행하기
            * **입력값**: 주문 상세 정보.
            * **반환값**: **주문 실행 결과**.
        6.  현재 상태(계좌 잔고, 보유 종목 등) 로깅하기
            * **입력값**: 계좌 잔고 조회 결과, 보유 종목 정보, 주문 실행 결과.
            * **반환값**: 없음 (로그 파일에 기록).

---

### 8. 모니터링 및 로깅 기능 추가

이 모듈은 시스템의 모든 활동과 상태를 기록하고, 사용자에게 중요한 알림을 보냅니다.

* **`check_balance.py` 스크립트를 활용하여 주기적으로 계좌 잔고를 확인하고 기록하는 기능을 완성합니다.**
    * **함수**: `log_daily_balance(kis_broker_instance, account_no)`
    * **입력값**: `kis_broker` 인스턴스, `account_no`.
    * **반환값**: 없음 (잔고 정보를 파일에 기록).
* **모든 매매 활동, 오류, 시스템 상태 등을 파일에 기록(logging)하여 나중에 분석할 수 있도록 합니다.**
    * **함수**: `setup_logging()`, `log_info(message)`, `log_error(message)`
    * **입력값**: 로깅할 메시지.
    * **반환값**: 없음 (로그 파일 생성 및 기록).
* **텔레그램 알림 모듈을 개발하여 다음 정보를 전송합니다.**
    * **함수**: `send_telegram_message(message, chat_id, bot_token)`
    * **입력값**: 전송할 메시지 내용, 텔레그램 봇 채팅 ID, 텔레그램 봇 토큰.
    * **반환값**: **메시지 전송 성공/실패 여부 (불리언)**.
    * **주문 체결/실패 알림**: `place_order` 함수 호출 후 결과에 따라 `send_telegram_message` 호출.
    * **일일/주간 계좌 잔고 및 수익률 리포트**: `log_daily_balance` 함수 실행 후 요약 정보를 `send_telegram_message`로 전송.
    * **시스템 오류 발생 시 즉시 알림**: `try-except` 블록에서 오류 발생 시 `log_error`와 함께 `send_telegram_message` 호출.

---

