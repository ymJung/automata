import configparser
import pandas as pd

# 설정 파일 로드
config = configparser.ConfigParser()
# config.cfg 파일이 프로젝트 루트에 있다고 가정합니다.
config.read('config.cfg')

# --- 설정 파일에서 전략 파라미터 불러오기 ---
try:
    strategy_params = config['strategy']
    SHORT_MA_WINDOW = strategy_params.getint('short_ma_window', 5)
    LONG_MA_WINDOW = strategy_params.getint('long_ma_window', 20)
    RSI_WINDOW = strategy_params.getint('rsi_window', 14)
    BOLLINGER_WINDOW = strategy_params.getint('bollinger_window', 20)
    BOLLINGER_STD_DEV = strategy_params.getint('bollinger_std_dev', 2)
    MACD_SHORT_WINDOW = strategy_params.getint('macd_short_window', 12)
    MACD_LONG_WINDOW = strategy_params.getint('macd_long_window', 26)
    MACD_SIGNAL_WINDOW = strategy_params.getint('macd_signal_window', 9)
except KeyError:
    print("indicators.py: [strategy] 섹션을 찾을 수 없습니다. 기본값을 사용합니다.")
    SHORT_MA_WINDOW, LONG_MA_WINDOW = 5, 20
    RSI_WINDOW = 14
    BOLLINGER_WINDOW, BOLLINGER_STD_DEV = 20, 2
    MACD_SHORT_WINDOW, MACD_LONG_WINDOW, MACD_SIGNAL_WINDOW = 12, 26, 9

def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터프레임에 단기 및 장기 이동평균선 컬럼을 추가합니다.
    :param df: 주가 데이터프레임 ('close' 종가 필요)
    :return: 'short_ma', 'long_ma' 컬럼이 추가된 데이터프레임
    """
    if len(df) >= SHORT_MA_WINDOW:
        df['short_ma'] = df['close'].rolling(window=SHORT_MA_WINDOW).mean()
    if len(df) >= LONG_MA_WINDOW:
        df['long_ma'] = df['close'].rolling(window=LONG_MA_WINDOW).mean()
    return df

def add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터프레임에 RSI 지표 컬럼을 추가합니다.
    :param df: 주가 데이터프레임 ('close' 종가 필요)
    :return: 'rsi' 컬럼이 추가된 데이터프레임
    """
    if len(df) >= RSI_WINDOW:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=RSI_WINDOW).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_WINDOW).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
    return df

def add_bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터프레임에 볼린저 밴드 관련 컬럼(중심선, 상단밴드)을 추가합니다.
    :param df: 주가 데이터프레임 ('close' 종가 필요)
    :return: 'ma_bollinger', 'bollinger_upper' 컬럼이 추가된 데이터프레임
    """
    if len(df) >= BOLLINGER_WINDOW:
        df['ma_bollinger'] = df['close'].rolling(window=BOLLINGER_WINDOW).mean()
        std_dev = df['close'].rolling(window=BOLLINGER_WINDOW).std()
        df['bollinger_upper'] = df['ma_bollinger'] + (std_dev * BOLLINGER_STD_DEV)
    return df

def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터프레임에 MACD 및 시그널 라인 컬럼을 추가합니다.
    :param df: 주가 데이터프레임 ('close' 종가 필요)
    :return: 'macd', 'signal' 컬럼이 추가된 데이터프레임
    """
    if len(df) >= MACD_LONG_WINDOW:
        df['ema_short'] = df['close'].ewm(span=MACD_SHORT_WINDOW, adjust=False).mean()
        df['ema_long'] = df['close'].ewm(span=MACD_LONG_WINDOW, adjust=False).mean()
        df['macd'] = df['ema_short'] - df['ema_long']
        df['signal'] = df['macd'].ewm(span=MACD_SIGNAL_WINDOW, adjust=False).mean()
    return df

def add_ewo(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터프레임에 EWO (Elder's Wave Oscillator) 지표를 추가합니다.
    EWO = ((단기 EMA - 장기 EMA) / 장기 EMA) * 100
    :param df: 주가 데이터프레임 ('close' 종가 필요)
    :return: 'ewo' 컬럼이 추가된 데이터프레임
    """
    if len(df) >= LONG_MA_WINDOW:
        short_ema = df['close'].ewm(span=SHORT_MA_WINDOW, adjust=False).mean()
        long_ema = df['close'].ewm(span=LONG_MA_WINDOW, adjust=False).mean()
        df['ewo'] = ((short_ema - long_ema) / long_ema) * 100
    return df

def check_missing_data(df: pd.DataFrame) -> tuple[bool, str]:
    """
    데이터프레임에서 누락된 데이터가 있는지 확인합니다.
    :param df: 확인할 데이터프레임
    :return: (누락 데이터 존재 여부, 누락 정보 메시지)
    """
    if df.empty:
        return True, "데이터프레임이 비어있습니다."
    
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        missing_info = df.isnull().sum()
        missing_columns = missing_info[missing_info > 0].to_dict()
        return True, f"누락된 데이터: {missing_columns}"
    
    return False, "누락된 데이터가 없습니다."

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    주어진 데이터프레임에 정의된 모든 기술적 지표를 추가합니다.
    :param df: 원본 주가 데이터프레임
    :return: 모든 지표가 추가된 데이터프레임
    """
    df = add_moving_averages(df)
    df = add_rsi(df)
    df = add_bollinger_bands(df)
    df = add_macd(df)
    df = add_ewo(df)
    return df
