import configparser
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
import os

class TradingController:
    """매매 빈도와 쿨다운을 관리하는 클래스"""
    
    def __init__(self):
        # 설정 로드
        config = configparser.ConfigParser()
        config.read('config.cfg')
        
        try:
            trading_control = config['trading_control']
            self.buy_cooldown_minutes = trading_control.getint('buy_cooldown_minutes', 30)
            self.sell_cooldown_minutes = trading_control.getint('sell_cooldown_minutes', 15)
            self.max_daily_trades = trading_control.getint('max_daily_trades', 10)
            self.min_holding_days = trading_control.getint('min_holding_days', 3)
        except KeyError:
            # 기본값 설정
            self.buy_cooldown_minutes = 30
            self.sell_cooldown_minutes = 15
            self.max_daily_trades = 10
            self.min_holding_days = 3
        
        # 매매 기록 파일
        self.trade_log_file = 'trade_log.json'
        self.trade_history = self._load_trade_history()
    
    def _load_trade_history(self) -> Dict:
        """매매 기록을 파일에서 로드"""
        if os.path.exists(self.trade_log_file):
            try:
                with open(self.trade_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            'last_buy_times': {},      # 종목별 마지막 매수 시간
            'last_sell_times': {},     # 종목별 마지막 매도 시간
            'daily_trade_count': {},   # 날짜별 매매 횟수
            'purchase_dates': {}       # 종목별 매수 날짜
        }
    
    def _save_trade_history(self):
        """매매 기록을 파일에 저장"""
        try:
            with open(self.trade_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.trade_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"매매 기록 저장 실패: {e}")
    
    def can_buy(self, stock_code: str) -> tuple[bool, str]:
        """매수 가능 여부 확인"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        # 1. 일일 매매 한도 확인
        daily_count = self.trade_history['daily_trade_count'].get(today, 0)
        if daily_count >= self.max_daily_trades:
            return False, f"일일 매매 한도 초과 ({daily_count}/{self.max_daily_trades})"
        
        # 2. 매수 쿨다운 확인
        last_buy_time_str = self.trade_history['last_buy_times'].get(stock_code)
        if last_buy_time_str:
            last_buy_time = datetime.fromisoformat(last_buy_time_str)
            cooldown_end = last_buy_time + timedelta(minutes=self.buy_cooldown_minutes)
            if now < cooldown_end:
                remaining = int((cooldown_end - now).total_seconds() / 60)
                return False, f"매수 쿨다운 중 (남은 시간: {remaining}분)"
        
        return True, "매수 가능"
    
    def can_sell(self, stock_code: str, purchase_date: Optional[str] = None) -> tuple[bool, str]:
        """매도 가능 여부 확인"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        # 1. 일일 매매 한도 확인
        daily_count = self.trade_history['daily_trade_count'].get(today, 0)
        if daily_count >= self.max_daily_trades:
            return False, f"일일 매매 한도 초과 ({daily_count}/{self.max_daily_trades})"
        
        # 2. 매도 쿨다운 확인
        last_sell_time_str = self.trade_history['last_sell_times'].get(stock_code)
        if last_sell_time_str:
            last_sell_time = datetime.fromisoformat(last_sell_time_str)
            cooldown_end = last_sell_time + timedelta(minutes=self.sell_cooldown_minutes)
            if now < cooldown_end:
                remaining = int((cooldown_end - now).total_seconds() / 60)
                return False, f"매도 쿨다운 중 (남은 시간: {remaining}분)"
        
        # 3. 최소 보유 기간 확인
        if purchase_date:
            purchase_dt = datetime.fromisoformat(purchase_date)
        else:
            # 기록에서 매수 날짜 찾기
            purchase_date_str = self.trade_history['purchase_dates'].get(stock_code)
            if purchase_date_str:
                purchase_dt = datetime.fromisoformat(purchase_date_str)
            else:
                # 매수 날짜를 찾을 수 없으면 매도 허용
                return True, "매도 가능"
        
        days_held = (now - purchase_dt).days
        if days_held < self.min_holding_days:
            remaining_days = self.min_holding_days - days_held
            return False, f"최소 보유 기간 미달 (남은 기간: {remaining_days}일)"
        
        return True, "매도 가능"
    
    def record_buy(self, stock_code: str):
        """매수 기록"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        # 매수 시간 기록
        self.trade_history['last_buy_times'][stock_code] = now.isoformat()
        
        # 매수 날짜 기록
        self.trade_history['purchase_dates'][stock_code] = now.isoformat()
        
        # 일일 매매 횟수 증가
        self.trade_history['daily_trade_count'][today] = \
            self.trade_history['daily_trade_count'].get(today, 0) + 1
        
        self._save_trade_history()
        print(f"[매수 기록] {stock_code} - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def record_sell(self, stock_code: str):
        """매도 기록"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        # 매도 시간 기록
        self.trade_history['last_sell_times'][stock_code] = now.isoformat()
        
        # 매수 날짜 기록 삭제 (더 이상 보유하지 않음)
        if stock_code in self.trade_history['purchase_dates']:
            del self.trade_history['purchase_dates'][stock_code]
        
        # 일일 매매 횟수 증가
        self.trade_history['daily_trade_count'][today] = \
            self.trade_history['daily_trade_count'].get(today, 0) + 1
        
        self._save_trade_history()
        print(f"[매도 기록] {stock_code} - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def get_daily_trade_count(self) -> int:
        """오늘의 매매 횟수 반환"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.trade_history['daily_trade_count'].get(today, 0)
    
    def cleanup_old_records(self, days_to_keep: int = 30):
        """오래된 기록 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # 오래된 일일 매매 기록 삭제
        dates_to_remove = [date for date in self.trade_history['daily_trade_count'].keys() 
                          if date < cutoff_str]
        for date in dates_to_remove:
            del self.trade_history['daily_trade_count'][date]
        
        self._save_trade_history()
        if dates_to_remove:
            print(f"오래된 매매 기록 {len(dates_to_remove)}개 정리 완료")

if __name__ == '__main__':
    # 테스트
    controller = TradingController()
    
    # 매수 테스트
    can_buy, reason = controller.can_buy('005930')
    print(f"삼성전자 매수 가능: {can_buy}, 사유: {reason}")
    
    if can_buy:
        controller.record_buy('005930')
        print(f"오늘 매매 횟수: {controller.get_daily_trade_count()}")
    
    # 매도 테스트
    can_sell, reason = controller.can_sell('005930')
    print(f"삼성전자 매도 가능: {can_sell}, 사유: {reason}")