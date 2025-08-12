import configparser
import pandas as pd

# 설정 파일 로드
config = configparser.ConfigParser()
config.read('config.cfg')

try:
    strategy_params = config['strategy']
    LOW_OFFSET = strategy_params.getfloat('low_offset', 0.98)  # 기본값 0.98
    HIGH_OFFSET = strategy_params.getfloat('high_offset', 1.05) # 기본값 1.05
    RSI_BUY_THRESHOLD = strategy_params.getint('rsi_buy_threshold', 50)
    EWO_BUY_THRESHOLD = strategy_params.getint('ewo_buy_threshold', 5)
    EWO_SELL_THRESHOLD = strategy_params.getint('ewo_sell_threshold', -5)
    STOP_LOSS_PERCENT = strategy_params.getfloat('stop_loss_percent', -0.35)
except KeyError:
    print("strategy.py: [strategy] 섹션을 찾을 수 없습니다. 기본값을 사용합니다.")
    LOW_OFFSET = 0.98
    HIGH_OFFSET = 1.05
    RSI_BUY_THRESHOLD = 50
    EWO_BUY_THRESHOLD = 5
    EWO_SELL_THRESHOLD = -5
    STOP_LOSS_PERCENT = -0.35

def check_buy_signal(df: pd.DataFrame) -> tuple[bool, str]:
    """
    매수 신호를 확인합니다.
    :param df: 'close', 'short_ma', 'long_ma', 'rsi', 'ewo' 컬럼이 포함된 데이터프레임
    :return: (매수 신호 여부, 신호 종류)
    """
    if not all(k in df.columns for k in ['close', 'short_ma', 'long_ma', 'rsi', 'ewo']):
        return False, "필요한 지표 데이터 부족"

    latest = df.iloc[-1]
    
    # 조건 1: 현재 가격이 단기 EMA 이하 & 과매수 EWO & 낮은 RSI
    condition1 = (latest['close'] <= latest['short_ma']) and \
                 (latest['ewo'] >= EWO_BUY_THRESHOLD) and \
                 (latest['rsi'] <= RSI_BUY_THRESHOLD)

    if condition1:
        return True, "과매수 EWO & 낮은 RSI"

    # 조건 2: 현재 가격이 (단기 EMA * Low Offset) 보다 낮음 & 과매도 EWO
    condition2 = (latest['close'] < (latest['short_ma'] * LOW_OFFSET)) and \
                 (latest['ewo'] <= EWO_SELL_THRESHOLD)
    
    if condition2:
        return True, "과매도 EWO & 가격 하락"

    return False, "매수 신호 없음"


def check_sell_signal(df: pd.DataFrame, avg_purchase_price: float) -> tuple[bool, str]:
    """
    매도 신호를 확인합니다.
    :param df: 'close', 'short_ma' 컬럼이 포함된 데이터프레임
    :param avg_purchase_price: 해당 종목의 평균 매수 단가
    :return: (매도 신호 여부, 신호 종류)
    """
    if not all(k in df.columns for k in ['close', 'short_ma']):
        return False, "필요한 지표 데이터 부족"

    latest = df.iloc[-1]

    # 이익 실현 조건: 현재가가 (평균 매수가 * High Offset) 보다 높을 때
    profit_taking_condition = latest['close'] >= (avg_purchase_price * HIGH_OFFSET)
    if profit_taking_condition:
        return True, f"이익 실현 (목표가: {avg_purchase_price * HIGH_OFFSET:.2f})"

    # 손절매 조건: 현재가가 평균 매수가 대비 일정 비율 이상 하락했을 때
    stop_loss_price = avg_purchase_price * (1 + STOP_LOSS_PERCENT)
    stop_loss_condition = latest['close'] <= stop_loss_price
    if stop_loss_condition:
        return True, f"손절매 (손절가: {stop_loss_price:.2f})"

    return False, "매도 신호 없음"

if __name__ == '__main__':
    # 테스트용 데이터프레임 생성
    data = {
        'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 110],
        'short_ma': [101, 102, 102, 103, 104, 105, 106, 107, 107, 108],
        'long_ma': [100, 101, 101, 102, 102, 103, 103, 104, 104, 105],
        'rsi': [50, 55, 52, 58, 62, 60, 65, 70, 68, 72],
        'ewo': [1, 1.5, 1.2, 1.8, 2.5, 2.2, 2.8, 3.5, 3.2, 4.0]
    }
    test_df = pd.DataFrame(data)

    # 매수 신호 테스트
    print("--- 매수 신호 테스트 ---")
    
    # 조건 1 테스트
    test_df.loc[9, 'close'] = 107
    test_df.loc[9, 'ewo'] = 6
    test_df.loc[9, 'rsi'] = 45
    buy_signal, reason = check_buy_signal(test_df)
    print(f"상황: 과매수 EWO & 낮은 RSI -> 신호: {buy_signal}, 이유: {reason}")
    
    # 조건 2 테스트
    test_df.loc[9, 'close'] = 105 # 108 * 0.98 = 105.84
    test_df.loc[9, 'ewo'] = -6
    buy_signal, reason = check_buy_signal(test_df)
    print(f"상황: 과매도 EWO & 가격 하락 -> 신호: {buy_signal}, 이유: {reason}")

    # 매도 신호 테스트
    print("\n--- 매도 신호 테스트 ---")
    avg_price = 100
    
    # 이익 실현 테스트
    test_df.loc[9, 'close'] = 106 # 100 * 1.05 = 105
    sell_signal, reason = check_sell_signal(test_df, avg_price)
    print(f"상황: 이익 실현 -> 신호: {sell_signal}, 이유: {reason}")

    # 손절매 테스트
    test_df.loc[9, 'close'] = 64 # 100 * (1 - 0.35) = 65
    sell_signal, reason = check_sell_signal(test_df, avg_price)
    print(f"상황: 손절매 -> 신호: {sell_signal}, 이유: {reason}")
