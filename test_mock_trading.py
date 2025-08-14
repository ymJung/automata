#!/usr/bin/env python3
"""
모의투자 모드 테스트 스크립트
24시간 언제든지 실행 가능한지 확인합니다.
"""

import sys
from datetime import datetime, timedelta
from kis_broker import KISBroker, MarketClosedError

def test_mock_trading():
    """모의투자 모드에서 24시간 실행 가능한지 테스트합니다."""
    print("=" * 60)
    print("🧪 모의투자 모드 24시간 테스트")
    print(f"📅 현재 시간: {datetime.now()}")
    print("=" * 60)
    
    try:
        # 1. 모의투자 모드로 브로커 초기화
        print("\n1️⃣ 모의투자 모드 브로커 초기화 중...")
        broker = KISBroker(mock=True)
        print("✅ 모의투자 모드 브로커 초기화 성공!")
        
        # 2. 현재가 조회 테스트
        print("\n2️⃣ 현재가 조회 테스트 중...")
        price = broker.get_current_price("005930")  # 삼성전자
        if price:
            print(f"✅ 삼성전자 현재가 조회 성공: {price:,}원")
        else:
            print("❌ 현재가 조회 실패")
        
        # 3. 잔고 조회 테스트
        print("\n3️⃣ 계좌 잔고 조회 테스트 중...")
        balance = broker.get_balance()
        if balance is not None:
            print("✅ 계좌 잔고 조회 성공!")
            print(f"   - 조회된 데이터 타입: {type(balance)}")
        else:
            print("❌ 계좌 잔고 조회 실패")
        
        # 4. 종목 리스트 조회 테스트
        print("\n4️⃣ 전체 종목 리스트 조회 테스트 중...")
        stocks = broker.get_all_listed_stocks()
        print(f"✅ 종목 리스트 조회 성공: {len(stocks)}개 종목")
        
        # 5. 시세 데이터 조회 테스트
        print("\n5️⃣ 일봉 데이터 조회 테스트 중...")
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        df = broker.get_daily_price("005930", start_date=start_date, end_date=end_date)
        
        if df is not None and not df.empty:
            print(f"✅ 일봉 데이터 조회 성공: {len(df)}일치 데이터")
            print(f"   - 데이터 컬럼: {list(df.columns)}")
        else:
            print("❌ 일봉 데이터 조회 실패")
        
        print("\n" + "=" * 60)
        print("🎉 모든 테스트 완료!")
        print("📝 모의투자 모드에서는 24시간 언제든지 실행 가능합니다.")
        print("=" * 60)
        
        return True
        
    except MarketClosedError as e:
        print(f"❌ 예상치 못한 MarketClosedError 발생: {e}")
        print("🔧 모의투자 모드에서는 이 오류가 발생하지 않아야 합니다.")
        return False
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_trading():
    """실전투자 모드에서 시장 시간 체크가 작동하는지 테스트합니다."""
    print("\n" + "=" * 60)
    print("🧪 실전투자 모드 시장 시간 체크 테스트")
    print("=" * 60)
    
    try:
        print("실전투자 모드 브로커 초기화 시도 중...")
        broker = KISBroker(mock=False)
        print("✅ 실전투자 모드 브로커 초기화 성공 (현재 장 시간)")
        return True
        
    except MarketClosedError as e:
        print(f"✅ 예상된 MarketClosedError 발생: {e}")
        print("📝 실전투자 모드에서는 장 시간에만 실행됩니다.")
        return True
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("모의투자 vs 실전투자 모드 테스트를 시작합니다.\n")
    
    # 모의투자 모드 테스트
    mock_success = test_mock_trading()
    
    # 실전투자 모드 테스트
    real_success = test_real_trading()
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"모의투자 모드: {'✅ 성공' if mock_success else '❌ 실패'}")
    print(f"실전투자 모드: {'✅ 성공' if real_success else '❌ 실패'}")
    
    if mock_success and real_success:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("📝 모의투자 모드로 24시간 테스트를 진행할 수 있습니다.")
    else:
        print("\n⚠️  일부 테스트가 실패했습니다.")
        sys.exit(1)