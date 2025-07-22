import configparser
import pandas as pd
import indicators  # 새로 만든 indicators 모듈을 임포트

# from kis_broker import KisBroker  # 실제 연동 시 주석 해제

# 설정 파일 로드 (stock_selector에만 필요한 파라미터)
config = configparser.ConfigParser()
config.read('config.cfg')

try:
    strategy_params = config['strategy']
    RSI_THRESHOLD = strategy_params.getint('rsi_threshold', 30)
    VOLUME_WINDOW = strategy_params.getint('volume_window', 20)
    VOLUME_SURGE_MULTIPLIER = strategy_params.getfloat('volume_surge_multiplier', 2.0)
except KeyError:
    print("stock_selector.py: [strategy] 섹션을 찾을 수 없습니다. 기본값을 사용합니다.")
    RSI_THRESHOLD = 30
    VOLUME_WINDOW = 20
    VOLUME_SURGE_MULTIPLIER = 2.0

# KIS API 브로커 인스턴스 생성
# broker = KisBroker()

def check_golden_cross(df: pd.DataFrame) -> bool:
    """
    데이터프레임에 이미 계산된 이동평균선을 바탕으로 골든크로스 발생 여부를 확인합니다.
    :param df: 'short_ma', 'long_ma' 컬럼이 포함된 데이터프레임
    :return: 골든크로스 발생 시 True, 아닐 시 False
    """
    # 지표 계산은 indicators.py에서 수행했으므로, 필요한 컬럼이 있는지 확인
    if 'short_ma' not in df.columns or 'long_ma' not in df.columns:
        return False
    
    # NaN 값이 있는 최근 행들을 제외하고 유효한 데이터만으로 확인
    df_valid = df[['short_ma', 'long_ma']].dropna()
    if len(df_valid) < 2:
        return False

    yesterday = df_valid.iloc[-2]
    today = df_valid.iloc[-1]

    if yesterday['short_ma'] < yesterday['long_ma'] and today['short_ma'] > today['long_ma']:
        print(f"[{df.iloc[-1].get('code', 'N/A')}] 골든크로스 발생!")
        return True
    return False

def check_rsi_oversold_exit(df: pd.DataFrame) -> bool:
    """
    RSI 지표가 과매도 구간을 탈출하는지 확인합니다.
    :param df: 'rsi' 컬럼이 포함된 데이터프레임
    :return: 과매도 구간 탈출 시 True, 아닐 시 False
    """
    if 'rsi' not in df.columns:
        return False
        
    df_valid = df[['rsi']].dropna()
    if len(df_valid) < 2:
        return False

    yesterday_rsi = df_valid['rsi'].iloc[-2]
    today_rsi = df_valid['rsi'].iloc[-1]

    if yesterday_rsi < RSI_THRESHOLD and today_rsi > RSI_THRESHOLD:
        print(f"[{df.iloc[-1].get('code', 'N/A')}] RSI 과매도 탈출!")
        return True
    return False

def check_volume_surge(df: pd.DataFrame) -> bool:
    """
    거래량이 평소 대비 급증했는지 확인합니다.
    :param df: 'volume' 컬럼이 포함된 데이터프레임
    :return: 거래량 급증 시 True, 아닐 시 False
    """
    if 'volume' not in df.columns or len(df) < VOLUME_WINDOW:
        return False

    # 평균 거래량 계산 (최근일 제외)
    avg_volume = df['volume'].iloc[-VOLUME_WINDOW:-1].mean()
    latest_volume = df['volume'].iloc[-1]

    if latest_volume > avg_volume * VOLUME_SURGE_MULTIPLIER:
        print(f"[{df.iloc[-1].get('code', 'N/A')}] 거래량 급증!")
        return True
    return False

def check_bollinger_breakout(df: pd.DataFrame) -> bool:
    """
    주가가 볼린저 밴드 상단을 돌파했는지 확인합니다.
    :param df: 'close', 'bollinger_upper' 컬럼이 포함된 데이터프레임
    :return: 상단 돌파 시 True, 아닐 시 False
    """
    if 'bollinger_upper' not in df.columns or 'close' not in df.columns:
        return False
        
    df_valid = df[['close', 'bollinger_upper']].dropna()
    if len(df_valid) < 1:
        return False

    latest = df_valid.iloc[-1]
    if latest['close'] > latest['bollinger_upper']:
        print(f"[{df.iloc[-1].get('code', 'N/A')}] 볼린저 밴드 상단 돌파!")
        return True
    return False

def check_macd_signal_cross(df: pd.DataFrame) -> bool:
    """
    MACD 선이 시그널 선을 상향 돌파했는지 확인합니다.
    :param df: 'macd', 'signal' 컬럼이 포함된 데이터프레임
    :return: MACD 골든크로스 발생 시 True, 아닐 시 False
    """
    if 'macd' not in df.columns or 'signal' not in df.columns:
        return False

    df_valid = df[['macd', 'signal']].dropna()
    if len(df_valid) < 2:
        return False
        
    yesterday = df_valid.iloc[-2]
    today = df_valid.iloc[-1]

    if yesterday['macd'] < yesterday['signal'] and today['macd'] > today['signal']:
        print(f"[{df.iloc[-1].get('code', 'N/A')}] MACD 골든크로스 발생!")
        return True
    return False

def screen_stocks(stock_codes: list[str]) -> list[str]:
    """
    주어진 종목 코드 리스트에 대해 모든 선정 기준을 적용하여 대상 종목을 필터링합니다.
    :param stock_codes: 검사할 전체 종목 코드 리스트
    :return: 모든 조건을 만족하는 선정된 종목 코드 리스트
    """
    selected_stocks = []
    for code in stock_codes:
        try:
            # 1. 데이터 가져오기 (실제로는 KIS Broker 사용)
            # df = broker.get_daily_chart(code)
            df = pd.DataFrame({
                'code': [code] * 40,
                'close': [100 + i + (10 if i > 35 else 0) for i in range(40)],
                'volume': [10000 * (1.5 if i > 38 else 1) for i in range(40)]
            })

            # 데이터가 충분하지 않으면 건너뛰기
            if len(df) < 20: # 최소 기간 (임의 설정)
                continue

            # 2. 기술적 지표 계산 (indicators 모듈 사용)
            df_with_indicators = indicators.add_all_indicators(df.copy())

            # 3. 스크리닝 조건 확인
            is_golden_cross = check_golden_cross(df_with_indicators)
            is_rsi_exit = check_rsi_oversold_exit(df_with_indicators)
            is_volume_surged = check_volume_surge(df_with_indicators)
            is_bollinger_breakout = check_bollinger_breakout(df_with_indicators)
            is_macd_cross = check_macd_signal_cross(df_with_indicators)

            # 모든 조건이 참일 경우에만 최종 선정
            if (is_golden_cross and is_rsi_exit and is_volume_surged and
                is_bollinger_breakout and is_macd_cross):
                print(f"\n>>> 최종 선정 종목: {code}\n")
                selected_stocks.append(code)

        except Exception as e:
            print(f"{code} 종목 처리 중 오류 발생: {e}")
            continue
            
    return selected_stocks

if __name__ == '__main__':
    # config.cfg 파일이 없으면 테스트를 위해 생성
    try:
        with open('config.cfg', 'x') as f:
            f.write("[strategy]\n" \
                    "short_ma_window = 5\n" \
                    "long_ma_window = 20\n" \
                    "rsi_window = 14\n" \
                    "rsi_threshold = 30\n" \
                    "volume_window = 20\n" \
                    "volume_surge_multiplier = 2.0\n" \
                    "bollinger_window = 20\n" \
                    "bollinger_std_dev = 2\n" \
                    "macd_short_window = 12\n" \
                    "macd_long_window = 26\n" \
                    "macd_signal_window = 9\n")
    except FileExistsError:
        pass # 파일이 이미 있으면 넘어감

    sample_stock_codes = ['005930', '000660', '035720']
    print("종목 스크리닝 시작...")
    final_list = screen_stocks(sample_stock_codes)
    print(f"\n최종 선정된 종목 리스트: {final_list}")