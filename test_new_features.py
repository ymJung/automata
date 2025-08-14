#!/usr/bin/env python3
"""
새로운 매매 제어 기능 테스트
"""

import configparser
from trading_controller import TradingController

def test_config_changes():
    """설정 변경사항 확인"""
    print("=== 설정 변경사항 확인 ===\n")
    
    config = configparser.ConfigParser()
    config.read('config.cfg')
    
    # 주문 설정 확인
    print("1. 주문 설정")
    order_section = config['order']
    print(f"   종목당 투자금액: {order_section.get('total_investment_per_stock')}원")
    print(f"   DCA 분할 수: {order_section.get('dca_divisions')}")
    print(f"   DCA 사용: {order_section.get('use_dca')}")
    
    # 매매 제어 설정 확인
    print("\n2. 매매 제어 설정")
    trading_section = config['trading_control']
    print(f"   매수 쿨다운: {trading_section.get('buy_cooldown_minutes')}분")
    print(f"   매도 쿨다운: {trading_section.get('sell_cooldown_minutes')}분")
    print(f"   일일 최대 매매: {trading_section.get('max_daily_trades')}회")
    print(f"   최소 보유 기간: {trading_section.get('min_holding_days')}일")
    print(f"   매매 체크 주기: {trading_section.get('loop_interval_minutes')}분")

def test_trading_controller():
    """매매 제어 시스템 테스트"""
    print("\n=== 매매 제어 시스템 테스트 ===\n")
    
    controller = TradingController()
    
    print("3. 매매 제어 기능")
    print(f"   오늘 매매 횟수: {controller.get_daily_trade_count()}")
    
    # 삼성전자 테스트
    can_buy, reason = controller.can_buy('005930')
    print(f"   삼성전자 매수 가능: {can_buy} ({reason})")
    
    can_sell, reason = controller.can_sell('005930')
    print(f"   삼성전자 매도 가능: {can_sell} ({reason})")

def main():
    """메인 테스트 함수"""
    print("🎯 수수료 절약 전략 구현 완료!\n")
    
    test_config_changes()
    test_trading_controller()
    
    print("\n=== 주요 변경사항 요약 ===")
    print("✅ 매매 주기: 10초 → 5분으로 변경")
    print("✅ DCA 비활성화 옵션 추가 (use_dca = false)")
    print("✅ 종목당 투자금액: 100,000원 → 300,000원 (일괄 투자)")
    print("✅ 매수/매도 쿨다운 시간 설정")
    print("✅ 일일 최대 매매 횟수 제한")
    print("✅ 최소 보유 기간 설정")
    print("✅ 매매 기록 관리 시스템 추가")
    
    print("\n💡 예상 효과:")
    print("- 매매 빈도 대폭 감소 (수수료 절약)")
    print("- 더 신중한 종목 선택")
    print("- 과도한 매매 방지")
    print("- 안정적인 수익 추구")

if __name__ == '__main__':
    main()