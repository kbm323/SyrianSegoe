<div align="center">

# SyrianSegoe Korean

**한국어 Windows 11 + Pretendard · 기존 GUI로 선택, 검증, 적용, 복원**

![Windows 11 x64](https://img.shields.io/badge/Windows_11-x64-0078D4)
[![검증](https://github.com/kbm323/SyrianSegoe/actions/workflows/korean-build.yml/badge.svg?branch=pretendard-korean-support)](https://github.com/kbm323/SyrianSegoe/actions/workflows/korean-build.yml)
![사전 릴리즈](https://img.shields.io/badge/release-v0.5.0--ko.1-orange)
[![MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

### [⬇ GUI EXE 바로 다운로드](https://github.com/kbm323/SyrianSegoe/releases/download/v0.5.0-ko.1/SyrianSegoe-Korean.exe)

[전체 ZIP](https://github.com/kbm323/SyrianSegoe/releases/download/v0.5.0-ko.1/SyrianSegoe-Korean-Windows-x64.zip) · [릴리즈 설명](https://github.com/kbm323/SyrianSegoe/releases/tag/v0.5.0-ko.1) · [한국어 사용법](https://github.com/kbm323/SyrianSegoe/blob/pretendard-korean-support/README.ko.md) · [검증 기록](https://github.com/kbm323/SyrianSegoe/blob/pretendard-korean-support/docs/validation/README.ko.md)

</div>

SyrianTurk/SyrianSegoe의 기존 GUI·빌더·설치·복원을 재사용한 한국어 포크입니다. **Pretendard Variable 선택 → 빌드·검증 → 별도 적용 → 원본 복원**을 제공합니다. GUI에는 Python·FontForge 설치가 필요하지 않습니다.

> **사전 릴리즈:** 코드·생성 글꼴·자동 테스트는 검증했지만 실제 Windows 전체 UI와 재부팅 후 복원은 아직 미검증입니다. 모든 화면의 글꼴 통일을 보장하지 않습니다.

## 3단계로 시작하기

| 단계 | 할 일 |
| --- | --- |
| **1 · 선택** | GUI 실행 → 위쪽 **한국어 Windows 11 · Pretendard** → 일반판 `PretendardVariable.ttf` 선택 |
| **2 · 빌드·검증** | 패키지 저장 폴더 선택 → 완료 안내까지 기다리기. 시스템 글꼴은 아직 변경되지 않음 |
| **3 · 적용** | 적용 확인 → 관리자 권한으로 다시 열린 뒤 **적용 버튼 다시 누르기** → 작업 저장 후 직접 재부팅 |

[공식 Pretendard 1.3.9 ZIP](https://github.com/orioncactus/pretendard/releases/tag/v1.3.9)을 풀고 `public/variable/PretendardVariable.ttf`를 선택합니다. 설치용 GUI에는 JP·Static·OTF를 사용하지 않습니다. 아래쪽 Latin/Arabic 합성 영역 대신 위쪽 한국어 영역을 사용하세요.

## 다운로드 파일 고르기

| 파일 | 용도 |
| --- | --- |
| **SyrianSegoe-Korean.exe** | GUI만 사용할 때. EXE 하나로 실행 |
| **SyrianSegoe-Korean-Windows-x64.zip** | GUI + 빌드/설치 CLI + 한국어 안내 + 라이선스 |
| **[SHA256SUMS.txt](https://github.com/kbm323/SyrianSegoe/releases/download/v0.5.0-ko.1/SHA256SUMS.txt)** | EXE/ZIP 다운로드 무결성 확인용 해시 |
| Source code ZIP | 개발·소스 실행용. 실행 파일 ZIP과 다름 |

Windows 11 **x64**용입니다. ARM64/x86은 미검증입니다. EXE는 서명되지 않았습니다. 앱 제어가 차단하면 정책을 해제하지 말고 [소스 실행 방법](https://github.com/kbm323/SyrianSegoe/blob/pretendard-korean-support/README.ko.md#gui로-사용하기)을 사용하세요.

## 지원 범위

| 대상 | 처리 |
| --- | --- |
| Segoe UI 6종 | Pretendard 기반 정적 UI 글꼴 |
| 맑은 고딕 3종 | 한국어 UI용 명칭과 원본 메트릭 유지 |
| Segoe UI Variable | 실제 weight 가변 글꼴, 원본 축·명명된 인스턴스 유지 |
| Fluent Icons / MDL2 / Emoji / Symbol | 제외 |
| Windows 원본 파일 | 덮어쓰지 않음 |

한글 5개 Unicode 범위를 보호하고, 현대 한글 **11,172자**, 원본 UI 문자, 해시·이름·스타일·줄높이·외곽선을 검사합니다. FontSubstitutes 충돌이나 Windows 업데이트로 원본 해시가 달라지면 적용을 거절합니다.

## 복원과 알려진 제한

**원본 복원 / Restore**를 누르고 관리자 창에서 다시 복원을 실행한 뒤 재부팅합니다. 잠긴 파일로 복원 오류가 나면 재부팅 후 다시 복원하세요. 백업/변경 기록은 `%USERPROFILE%\Documents\SyrianSegoe\Original_Segoe_Backups`에 남습니다. [Restore.reg 복구 절차](https://github.com/kbm323/SyrianSegoe/blob/pretendard-korean-support/README.ko.md#실제-적용용-패키지와-설치복원)를 참고하세요.

- 빌드는 수 분 이상 걸릴 수 있습니다. 현재 막대는 시작·완료 때만 바뀌며 처리 중 창 닫기를 막습니다.
- 한자는 맑은 고딕으로 보완합니다. Variable opsz는 같은 윤곽을 사용하고 기본 굵기의 조판 테이블을 공유합니다.
- 일부 UI는 원본 경로를 직접 읽어 바뀌지 않을 수 있습니다. 로그인 화면·DPI·재부팅 후 적용/복원은 미검증입니다.
- Windows 원본·Pretendard·생성 TTF는 배포하지 않습니다. 각 PC에서 직접 빌드합니다.

## 개발·검증·출처

구현 소스는 [`pretendard-korean-support` 브랜치](https://github.com/kbm323/SyrianSegoe/tree/pretendard-korean-support)와 [PR #1](https://github.com/kbm323/SyrianSegoe/pull/1)에 있습니다. 기본 브랜치의 README는 배포 안내이며 한국어 구현은 개발 브랜치를 사용하세요.

39개 테스트, 실제 CTk 이벤트 루프, 임시 Fonts/가상 레지스트리 설치·복원, 공식 Pretendard 10종 빌드와 Windows 프로세스 내부 로드를 검증했습니다. CI가 GUI/CLI를 패키징하고 ZIP 구성·SHA-256 검사 후 Releases에 배포합니다. 테스트에서 시스템 글꼴 설치나 재부팅은 수행하지 않습니다.

원본: [SyrianTurk/SyrianSegoe](https://github.com/SyrianTurk/SyrianSegoe). 소스는 원본의 [MIT](LICENSE)를 유지하며 각 글꼴의 배포 권한은 별도입니다. MIT가 Windows 글꼴 배포 권한을 부여하지 않습니다.

[원본 README](https://github.com/kbm323/SyrianSegoe/blob/pretendard-korean-support/README.upstream.md) · [문제 보고](https://github.com/kbm323/SyrianSegoe/issues) · [전체 릴리즈](https://github.com/kbm323/SyrianSegoe/releases)
