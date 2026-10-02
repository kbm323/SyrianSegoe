# SyrianSegoe Korean {{VERSION}}

**Windows 11의 한국어 UI를 Pretendard로. 선택 → 빌드·검증 → 적용 → 복원.**

기존 SyrianSegoe GUI와 글꼴 빌더를 재사용한 한국어 사전 릴리즈입니다.

## 다운로드

| 파일 | 이런 경우에 선택하세요 |
| --- | --- |
| **[SyrianSegoe-Korean.exe](https://github.com/{{REPOSITORY}}/releases/download/{{VERSION}}/SyrianSegoe-Korean.exe)** | GUI만 바로 실행할 때 |
| **[SyrianSegoe-Korean-Windows-x64.zip](https://github.com/{{REPOSITORY}}/releases/download/{{VERSION}}/SyrianSegoe-Korean-Windows-x64.zip)** | GUI·CLI·한국어 안내를 한 폴더에 보관할 때 |
| [SHA256SUMS.txt](https://github.com/{{REPOSITORY}}/releases/download/{{VERSION}}/SHA256SUMS.txt) | 내려받은 EXE와 ZIP의 해시를 확인할 때 |

Windows 11 **x64**용입니다. GUI 실행에는 Python·FontForge 설치가 필요하지 않습니다.
GitHub가 아래에 표시하는 **Source code ZIP/TAR.GZ는 소스**이며 실행 파일 묶음이 아닙니다.

## 3단계로 시작하기

1. **선택:** GUI 위쪽 **한국어 Windows 11 · Pretendard**에서 공식 일반판 `PretendardVariable.ttf` 선택.
2. **빌드·검증:** 출력 폴더를 고르고 완료 안내까지 대기. 이 단계에서는 시스템을 바꾸지 않습니다.
3. **적용:** 적용 확인 → 관리자 창에서 버튼을 다시 누르기 → 작업 저장 후 직접 재부팅.

Pretendard는 [공식 1.3.9 릴리즈](https://github.com/orioncactus/pretendard/releases/tag/v1.3.9)에서 별도로 받습니다.
일반판 ZIP의 `public/variable/PretendardVariable.ttf`를 사용하세요.

## 이번 배포의 구성

- GUI 단독 EXE와 GUI·빌드 CLI·설치 CLI를 담은 Windows x64 ZIP.
- 한국어 빠른 시작·복원 안내, 상세 사용법, MIT 라이선스.
- ZIP 내부 파일 해시와 다운로드 EXE/ZIP 해시를 각각 제공.
- `VERSION.json`에 버전·정확한 소스 커밋·GUI 해시를 기록.
- Windows 원본·Pretendard·생성 글꼴 파일은 배포하지 않음.

앱은 Segoe UI 6종·맑은 고딕 3종·실제 weight 가변 Segoe UI Variable 1종을 빌드합니다.
현대 한글 11,172자와 원본 UI 문자·명칭·줄높이를 검사하며, 아이콘·이모지 글꼴은 제외합니다.

## 원본 복원

**원본 복원 / Restore** → 관리자 창에서 다시 복원 → 재부팅.
잠긴 파일 오류가 발생하면 재부팅 후 복원을 다시 실행하세요.
백업과 변경 기록은 `%USERPROFILE%\Documents\SyrianSegoe\Original_Segoe_Backups`에 남습니다.

## 검증 범위와 제한

배포 워크플로는 고정한 소스의 테스트, Windows EXE 패키징, GUI 메인 창 열기,
두 CLI의 도움말 실행, ZIP 구성과 해시를 검사합니다.
**실제 Windows 전체 UI와 재부팅 후 적용·복원은 미검증**입니다.
일부 UI는 원본 경로를 직접 읽어 바뀌지 않을 수 있고, Variable opsz 디자인·굵기별 조판에는 제한이 있습니다.

EXE는 서명되지 않았습니다. 앱 제어가 차단하면 정책을 해제하지 말고 상세 안내의 소스 실행 방법을 사용하세요.
소스의 MIT 라이선스는 Windows 글꼴이나 생성 TTF의 배포 권한을 부여하지 않습니다.

[상세 사용법](https://github.com/{{REPOSITORY}}/blob/{{SOURCE_COMMIT}}/README.ko.md) ·
[기존 검증 기록](https://github.com/{{REPOSITORY}}/blob/{{SOURCE_COMMIT}}/docs/validation/README.ko.md) ·
[문제 보고](https://github.com/{{REPOSITORY}}/issues)

빌드 소스: [`{{SOURCE_COMMIT}}`](https://github.com/{{REPOSITORY}}/commit/{{SOURCE_COMMIT}})
