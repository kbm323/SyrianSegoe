<div align="center">

# SyrianSegoe Korean

### Windows 11 × Pretendard

한국어 Windows UI를 위한 글꼴 빌더.<br>
**선택하고, 검증하고, 적용하고, 원본으로 복원하세요.**

![Windows 11 x64](https://img.shields.io/badge/Windows_11-x64-0078D4?logo=windows11&logoColor=white)
![Pretendard](https://img.shields.io/badge/Pretendard-1.3.9-4F46E5)
![사전 릴리즈](https://img.shields.io/badge/status-prerelease-F59E0B)
[![Windows release](https://github.com/kbm323/SyrianSegoe/actions/workflows/release.yml/badge.svg)](https://github.com/kbm323/SyrianSegoe/actions/workflows/release.yml)
[![MIT](https://img.shields.io/badge/license-MIT-16A34A)](LICENSE)

**[GUI EXE 다운로드](https://github.com/kbm323/SyrianSegoe/releases/download/v0.5.0-ko.1/SyrianSegoe-Korean.exe)** ·
[전체 Windows x64 ZIP](https://github.com/kbm323/SyrianSegoe/releases/download/v0.5.0-ko.1/SyrianSegoe-Korean-Windows-x64.zip) ·
[릴리즈 안내](https://github.com/kbm323/SyrianSegoe/releases/tag/v0.5.0-ko.1) ·
[한국어 사용법](https://github.com/kbm323/SyrianSegoe/blob/pretendard-korean-support/README.ko.md) ·
[문제 보고](https://github.com/kbm323/SyrianSegoe/issues)

</div>

---

SyrianTurk/SyrianSegoe의 기존 GUI·빌드·설치·복원을 재사용한 한국어 포크입니다.
일반판 **Pretendard Variable**로 Segoe UI와 맑은 고딕용 글꼴을 만들고, 검사한 뒤 별도로 적용합니다.
GUI 실행에는 Python·FontForge 설치가 필요하지 않습니다.

> **v0.5.0-ko.1 사전 릴리즈:** Windows CI에서 앱 테스트, GUI·CLI 빌드, GUI 창 열기, CLI 도움말 실행과 공개 다운로드 해시를 검증했습니다. 실제 Windows 전체 UI와 재부팅 후 적용·복원은 아직 미검증이며 모든 화면의 글꼴 통일을 보장하지 않습니다.

## 다운로드 선택

| 원하는 사용 방식 | 선택할 파일 | 포함 내용 |
| --- | --- | --- |
| **GUI로 시작하기** | [SyrianSegoe-Korean.exe](https://github.com/kbm323/SyrianSegoe/releases/download/v0.5.0-ko.1/SyrianSegoe-Korean.exe) | 바로 실행하는 GUI |
| **도구와 안내를 함께 보관하기** | [SyrianSegoe-Korean-Windows-x64.zip](https://github.com/kbm323/SyrianSegoe/releases/download/v0.5.0-ko.1/SyrianSegoe-Korean-Windows-x64.zip) | GUI + 빌드·설치 CLI + 한국어 안내 + 라이선스 |
| **다운로드 확인하기** | [SHA256SUMS.txt](https://github.com/kbm323/SyrianSegoe/releases/download/v0.5.0-ko.1/SHA256SUMS.txt) | EXE·ZIP의 SHA-256 해시 |
| **소스 수정하기** | GitHub의 Source code ZIP / TAR.GZ | 소스 코드. 실행 파일 묶음과 다릅니다 |

Windows 11 **x64**용입니다. ARM64/x86은 미검증입니다.
ZIP에는 `QUICKSTART.ko.txt`, 상세 사용법, 파일별 해시와 버전·소스 커밋을 기록한 `VERSION.json`이 함께 들어갑니다.

## 3단계로 시작하기

| ① 선택 | ② 빌드·검증 | ③ 적용 |
| --- | --- | --- |
| 앱 위쪽 **한국어 Windows 11 · Pretendard**에서 글꼴 선택 | 저장 폴더를 고르고 완료 안내까지 대기 | 적용 확인 후 관리자 창에서 버튼을 다시 누르고 직접 재부팅 |
| 일반판 `PretendardVariable.ttf` 사용 | 이 단계에서는 시스템을 변경하지 않음 | 작업을 저장한 뒤 진행 |

[공식 Pretendard 1.3.9 ZIP](https://github.com/orioncactus/pretendard/releases/tag/v1.3.9)을 별도로 풀고
`public/variable/PretendardVariable.ttf`를 선택합니다. GUI 설치용 입력에는 **JP·Static·OTF를 사용하지 않습니다.**
아래쪽 Latin/Arabic 합성 영역 대신 위쪽 한국어 영역을 사용하세요.

## 지원하는 글꼴

| 대상 | 생성 방식 |
| --- | --- |
| **Segoe UI 6종** | Pretendard 기반 정적 UI 글꼴 |
| **맑은 고딕 3종** | 한국어 UI용 이름과 원본 줄높이 메트릭 유지 |
| **Segoe UI Variable** | 실제 weight 가변 글꼴, 원본 축·명명된 인스턴스 유지 |

한글 5개 Unicode 범위를 보호하고, 현대 한글 **11,172자**와 원본 UI 문자·해시·이름·스타일·줄높이·외곽선을 검사합니다.
Fluent Icons·MDL2·Emoji·Symbol은 대상에서 제외하며 Windows 원본 파일은 덮어쓰지 않습니다.
기존 FontSubstitutes 설정이 충돌하거나 Windows 업데이트로 원본 해시가 바뀌면 적용을 거절합니다.

## 원본으로 복원

**원본 복원 / Restore** → 관리자 창에서 다시 복원 → 재부팅.
잠긴 파일로 오류가 나면 재부팅 후 복원을 다시 실행하세요.
백업·변경 기록·`Restore.reg`는 아래 폴더에 남습니다.

```text
%USERPROFILE%\Documents\SyrianSegoe\Original_Segoe_Backups
```

[자세한 복원·Restore.reg 복구 안내](https://github.com/kbm323/SyrianSegoe/blob/pretendard-korean-support/README.ko.md#실제-적용용-패키지와-설치복원)

<details>
<summary><strong>알려진 제한과 실행 파일 안내</strong></summary>

- 빌드는 수 분 이상 걸릴 수 있습니다. 진행 막대는 시작·완료 때만 바뀌며 처리 중 창 닫기를 막습니다.
- 한자는 맑은 고딕으로 보완합니다. 모든 한자가 Pretendard 디자인이 되는 것은 아닙니다.
- Variable opsz는 같은 윤곽을 사용하고 기본 굵기의 조판 테이블을 공유합니다.
- 일부 Windows UI는 원본 경로를 직접 읽어 변경되지 않을 수 있습니다. 로그인 화면·DPI·재부팅 후 적용·복원은 미검증입니다.
- EXE는 서명되지 않았습니다. 앱 제어가 차단하면 정책을 해제하지 말고 한국어 안내의 Python 소스 실행 방법을 사용하세요.
- Windows 원본·Pretendard·생성 TTF는 배포 ZIP에 포함하지 않습니다. 각 PC에서 직접 빌드합니다.

</details>

## 개발과 배포

한국어 구현은 [`pretendard-korean-support`](https://github.com/kbm323/SyrianSegoe/tree/pretendard-korean-support)에 있습니다.
`main`은 배포 홈과 릴리즈 구성을 관리합니다. 앱 소스를 찾는 경우 한국어 개발 브랜치를 사용하세요.

배포는 `release.json`의 **고정한 소스 커밋**에서 기존 빌더를 실행합니다.
Windows 테스트 → GUI·CLI 패키징과 실행 확인 → ZIP·해시 검사 → 버전 태그의 사전 릴리즈를 공개합니다.
수동 Actions 실행은 검토용 파일만 만들며 공개 게시하지 않습니다.

[릴리즈 만들기](docs/release/README.md) · [릴리즈 본문 템플릿](docs/release/NOTES.md) ·
[기존 앱 검증 기록](https://github.com/kbm323/SyrianSegoe/blob/pretendard-korean-support/docs/validation/README.ko.md)

## 출처와 라이선스

원본: [SyrianTurk/SyrianSegoe](https://github.com/SyrianTurk/SyrianSegoe).
프로그램 소스는 원본의 [MIT](LICENSE)를 유지합니다. 각 글꼴의 배포 권한은 별도이며,
소스의 MIT 라이선스가 Windows 글꼴이나 생성 TTF의 배포 권한을 부여하지 않습니다.

[원본 README](https://github.com/kbm323/SyrianSegoe/blob/pretendard-korean-support/README.upstream.md) ·
[Pretendard](https://github.com/orioncactus/pretendard) ·
[변경 PR #1](https://github.com/kbm323/SyrianSegoe/pull/1)
