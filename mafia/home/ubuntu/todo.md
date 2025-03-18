# 텔레그램 마피아 게임 봇 개발 계획

## 프로젝트 구조 설정
- [x] 프로젝트 디렉토리 구조 생성
- [x] 필요한 패키지 설치 (python-telegram-bot 등)

## 역할 관련 모듈 구현
- [x] 기본 역할 클래스 구현 (base_role.py)
- [x] 마피아 역할 클래스 구현 (mafia_roles.py)
- [x] 시민 역할 클래스 구현 (citizen_roles.py)
- [x] 중립 역할 클래스 구현 (neutral_roles.py)

## 게임 관련 모듈 구현
- [x] 게임 초기화 모듈 구현 (game/__init__.py)
- [x] 플레이어 클래스 구현 (game/player.py)
- [x] 역할 관리자 구현 (game/role_manager.py)
- [x] 게임 단계 관리자 구현 (game/phase_manager.py)
- [x] 게임 관리자 구현 (game/game_manager.py)

## 핸들러 모듈 구현
- [x] 핸들러 초기화 모듈 구현 (handlers/__init__.py)
- [x] 명령어 핸들러 구현 (handlers/command_handlers.py)
- [x] 콜백 쿼리 핸들러 구현 (handlers/callback_handlers.py)
- [x] 게임 진행 핸들러 구현 (handlers/game_handlers.py)

## 유틸리티 모듈 구현
- [x] 설정 관리 모듈 구현 (utils/settings.py)
- [x] 메시지 유틸리티 구현 (utils/message_utils.py)
- [x] 게임 상태 관리 모듈 구현 (utils/state_utils.py)

## 메인 애플리케이션 구현
- [x] 메인 애플리케이션 파일 구현 (main.py)
- [x] 봇 초기화 및 설정
- [x] 핸들러 등록
- [x] 봇 실행 코드 구현

## 테스트 및 디버깅
- [x] 기본 명령어 테스트
- [x] 게임 진행 테스트
- [x] 오류 처리 및 디버깅

## 문서화
- [x] 코드 주석 추가
- [x] README.md 작성
- [x] 사용 방법 문서화
