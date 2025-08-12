#!/usr/bin/env python3
"""
주식 자동매매 시스템 실행 스크립트
"""

import sys
import os
from datetime import datetime

def check_config():
    """config.cfg 파일의 필수 설정값들을 확인합니다."""
    import configparser
    
    config = configparser.ConfigParser()
    if not os.path.exists('config.cfg'):
        print("❌ config.cfg 파일이 없습니다. config.cfg.sample을 참고하여 생성해주세요.")
        return False
    
    config.read('config.cfg')
    
    # 필수 섹션 확인
    required_sections = ['kis', 'telegram', 'strategy', 'order']
    for section in required_sections:
        if section not in config:
            print(f"❌ config.cfg에 [{section}] 섹션이 없습니다.")
            return False
    
    # KIS API 키 확인
    if config['kis']['APP_KEY'] == "여기에_발급받은_APP_KEY를_입력하세요":
        print("❌ config.cfg에 실제 KIS API 키를 입력해주세요.")
        return False
    
    print("✅ config.cfg 설정 확인 완료")
    return True

def main():
    print("=" * 60)
    print("🚀 주식 자동매매 시스템 시작")
    print(f"📅 시작 시간: {datetime.now()}")
    print("=" * 60)
    
    # 설정 파일 확인
    if not check_config():
        print("\n설정을 완료한 후 다시 실행해주세요.")
        sys.exit(1)
    
    # 메인 프로그램 실행
    try:
        from main import run_trading_bot
        run_trading_bot()
    except KeyboardInterrupt:
        print("\n\n🛑 사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 프로그램 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n📅 종료 시간: {datetime.now()}")
        print("=" * 60)

if __name__ == "__main__":
    main()