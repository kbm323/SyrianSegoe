# 릴리즈 만들기

`main`은 배포 안내와 패키징을 관리하고, 한국어 앱은 `pretendard-korean-support`에 있습니다.
`release.json`의 **정확한 소스 커밋**을 체크아웃해 기존 `build.ps1`로 GUI·CLI를 빌드합니다.
브랜치의 새 커밋이 기존 버전의 바이너리를 조용히 바꾸지 않도록 커밋을 고정합니다.

## 먼저 패키지 검토하기

GitHub Actions의 **Windows release → Run workflow**를 `main`에서 실행합니다.
Windows 테스트와 EXE 빌드가 끝나면 버전별 Artifact에 다음 파일이 생깁니다.

```text
SyrianSegoe-Korean.exe
SyrianSegoe-Korean-Windows-x64.zip
SHA256SUMS.txt
RELEASE_NOTES.md
```

수동 실행과 PR 검사는 GitHub Release를 게시하지 않습니다.
Artifact는 14일간 보관되며 실행 파일을 담은 ZIP과 GitHub가 Artifact 다운로드용으로 씌우는 ZIP은 서로 다릅니다.

## 버전 태그와 릴리즈 공개

1. `release.json`의 `version`과 `source_commit`을 검토합니다. 새 버전은 새 태그를 사용합니다.
2. 패키지 구성이나 안내를 바꿀 때 `QUICKSTART.ko.txt`와 `NOTES.md`를 함께 확인합니다.
3. 변경을 `main`에 반영한 뒤 해당 **배포 커밋**에 버전 태그를 만듭니다.

```bash
git tag v0.5.0-ko.1 <검토한-main-커밋>
git push origin v0.5.0-ko.1
```

태그와 `release.json`의 버전이 일치해야 합니다. `v*-ko.*` 태그가 Windows 검증과 패키징을 실행합니다.
성공하면 EXE·ZIP·해시·릴리즈 본문을 담은 초안을 만들고 **사전 릴리즈로 공개**합니다.
같은 이름의 릴리즈가 이미 있으면 실패하며 파일을 덮어쓰지 않습니다.
기존 초안이 남은 재시도에서는 먼저 Artifact를 확인하고 초안을 정리하거나 새 버전을 선택합니다.
워크플로는 패키징된 GUI의 메인 창과 두 CLI의 `--help` 실행을 확인한 뒤 공개합니다.
수동 실행의 Artifact를 먼저 검토하세요. 버전 태그 푸시는 공개 배포를 시작합니다.
공개 전 업로드한 EXE·ZIP·해시를 GitHub에서 다시 내려받아 검사합니다.
실제 시스템 전체 UI와 재부팅 후 복원은 별도의 검증이며 CI 성공으로 대체할 수 없습니다.

릴리즈 본문만 남고 첨부 파일이 0개인 경우 **Recover verified release assets**를 실행해
성공한 Windows release 실행의 `run_id`를 입력합니다. 원본 Artifact의 버전·소스 커밋·해시를
검사하고 빈 릴리즈에만 업로드한 뒤 재다운로드 검증을 수행합니다. 기존 자산이 하나라도 있으면 중단합니다.

## ZIP 안의 파일

```text
SyrianSegoe-Korean.exe           GUI
SyrianSegoe-Korean-Build.exe     빌드 CLI
SyrianSegoe-Korean-Install.exe   설치 계획·적용·복원 CLI
QUICKSTART.ko.txt                빠른 시작·복원 안내
README.ko.md                    고정한 앱 소스의 상세 사용법
LICENSE                         앱 소스의 MIT 라이선스
VERSION.json                    버전·소스 커밋·EXE 해시
SHA256SUMS.txt                   위 파일들의 해시
```

다운로드 옆의 `SHA256SUMS.txt`는 EXE와 ZIP의 해시입니다.
ZIP 내부 해시 목록은 ZIP 안의 모든 다른 파일을 검사합니다. 해시 파일은 자기 자신을 포함하지 않습니다.
Windows 원본·Pretendard·생성 TTF는 패키지에 넣지 않습니다.

## 로컬 패키징

Python 표준 라이브러리만 사용하므로 패키지 조립과 해시 검증은 Linux에서도 가능합니다.
실제 Windows EXE를 새로 빌드하는 단계는 Windows x64에서 수행해야 합니다.

```powershell
# 먼저 고정한 한국어 소스 폴더에서 build.ps1을 실행합니다.
python scripts/package_release.py build --dist <앱소스>/dist --source <앱소스> --output release --version v0.5.0-ko.1 --source-commit <정확한40자리커밋>
python scripts/package_release.py verify release
python -m unittest discover -s tests -v
```

출력 폴더는 새 경로여야 합니다. 기존 다운로드·사용자 파일은 덮어쓰지 않습니다.
`--gui-only`는 CLI가 없는 참고용 GUI ZIP을 만듭니다. 출처를 확인하지 못한 업로드 파일은
`--version uploaded-preview --source-commit unverified`로 표시하고 공식 릴리즈 자산으로 쓰지 않습니다.
GUI 참고용 패키지는 공식 다운로드 링크 없이 출처·실행 미검증을 표시한 별도 본문을 생성합니다.
