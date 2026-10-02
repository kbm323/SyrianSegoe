# 한국어 Windows 11 + Pretendard 실험 브랜치

이 브랜치는 SyrianTurk/SyrianSegoe의 한글 삭제 경로를 수정하고, **기존 설치·복원을 재사용하는 한국어 경로**를 추가한다. 기준 저장소는 GitHub의 `kbm323/SyrianSegoe`, 브랜치는 `pretendard-korean-support`다. 로컬 체크아웃·생성 글꼴은 임시 검증 자료다.

**설치 가능한 패키지 생성과 apply/restore 명령을 제공합니다.** 이 작업에서는 실제 PC에 적용하지 않았으므로 시작 메뉴·설정·로그인 화면·DPI별 렌더링·재부팅 후 Restore는 아직 검증하지 않았습니다. 기존 GUI의 일반 합성 경로로 한국어를 보내지 않고 아래 한국어 설치 명령을 사용합니다. 기존의 기본 빌드 전용 모드도 유지합니다.

## 원본 분석과 변경점

| 파일 | 확인한 문제와 변경 |
| --- | --- |
| `engine.py`, `grid_sync_engine.py`, 두 italic 엔진 | 한글·CJK 보존 범위 확장, 실제 `unicode`와 `altuni` 보호 우선 처리, 한글이 있는 글꼴의 GSUB/GPOS 유지. TTF 생성 실패 시 SFD를 `.ttf`로 저장하던 fallback 제거. weight 실패를 프로세스 실패로 반환 |
| `variable_slicer.py` | Segoe UI cmap만 기준으로 subset하면서 한글을 삭제하던 경로 수정. 한글·한국어 문자 범위 추가. 기존 Variable placeholder에 시스템 이름 적용. 이 placeholder가 실제 Segoe UI Variable 축/동작을 재현한다고 보장하지 않음 |
| `glyph_policy.py` | 네 엔진과 slicer가 공유하는 한국어 문자 보존 정책 |
| `font_targets.py`, `korean_builder.py` | 기본 빌드 9종 및 설치용 10종(Variable 포함)을 FontTools로 생성·검사. Static 및 Variable 입력 지원, Malgun Gothic 지원, 시스템 원본은 읽기 전용 |
| `app.py`, `font_backup.py` | 한글 입력의 기존 적용 차단. Segoe/Malgun 원본 백업 추가 및 재실행 시 덮어쓰기 방지. 해시 검증 |
| `font_transaction.py` | 기존 GUI 적용 경로를 journal 방식으로 보강. 전체 생성물 사전검사, 원래 레지스트리 값 기록, 중간 실패 보상 복구, 영구 journal 기반 Restore. 이번 작업에서는 실제 설치 호출을 실행하지 않음 |
| `segoe_cloner.py` | Segoe UI Clone 별도 설치 기능임을 확인. 한국어 builder가 호출하지 않으며 Malgun/아이콘 복제 기능을 추가하지 않음 |
| `font_resizer.py` | NONCLIENTMETRICS와 아이콘 제목 텍스트 크기를 바꾸는 별도 기능임을 확인. 한국어 builder가 호출하지 않음 |
| `grid_sync_engine_italic.py` | 원본 파일명의 보이지 않는 RTL 문자를 제거하여 app 및 패키징에서 요청하는 파일명과 일치시킴 |

새 한국어 builder는 FontForge의 시각적 H 높이 확대 후 EM 변경 경로를 사용하지 않는다. FontTools로 EM을 한 번 맞추고 원본 대상의 수평·OS/2 세로 metrics를 복사한다. Pretendard의 GSUB/GPOS와 존재하는 문자들을 유지하며, 그 밖의 전체 Unicode 글리프를 새로 만들거나 임의로 추가하지 않는다.

## 보존하는 문자

- Hangul Jamo U+1100–11FF
- Hangul Compatibility Jamo U+3130–318F (`U+3164` 포함)
- Hangul Jamo Extended-A U+A960–A97F
- Hangul Syllables U+AC00–D7AF
- Hangul Jamo Extended-B U+D7B0–D7FF

범위 보존은 입력에 있는 글리프를 지우지 않는다는 뜻이다. 입력에 없는 옛한글 글리프나 예약 코드포인트를 생성한다는 뜻은 아니다. 현대 한글 완성형의 실제 배정 범위 U+AC00–D7A3, **11,172자**는 입력과 생성물 양쪽에서 필수 검사한다.

CJK 문장부호, 한자 Extension A/기본 통합 한자/호환 한자, enclosed CJK, 통화·화살표·수학기호, 동그라미 숫자, 전각·반각 문자도 보존한다. 원본의 `U+4E00–4FFE`만 남기던 한자 정책을 확장했다. 한글이 다른 Unicode alias로 연결된 경우에도 삭제 목록보다 보호를 먼저 적용한다.

Pretendard 일반판에는 `漢字`가 없었다. Segoe UI 역시 한자 공급원으로 충분하지 않다. 따라서 원본 대상에만 있는 UI 문자는 그 대상 글꼴에서, Segoe 대상과 Malgun Semilight에 필요한 한자는 **설치된 Malgun Regular/Bold**에서 보완한다. Pretendard에 존재하는 문자의 우선권은 유지한다. 보완된 한자는 맑은 고딕의 디자인이며, Light 대상의 한자가 Regular 굵기로 보일 수 있다.

## 글꼴과 굵기 매핑

일반 `Pretendard` 1.3.9를 검증에 사용했다. Pretendard JP, Apple SF Pro, Apple SD Gothic Neo는 사용하거나 배포하지 않는다. Static을 우선 선택한다.

| Windows 대상 | 원본 파일 | Static 입력 | Variable wght |
| --- | --- | --- | --- |
| Segoe UI Light | segoeuil.ttf | Pretendard-Light.ttf | 300 |
| Segoe UI Semilight | segoeuisl.ttf | Pretendard-Light.ttf | 350 |
| Segoe UI Regular | segoeui.ttf | Pretendard-Regular.ttf | 400 |
| Segoe UI Semibold | seguisb.ttf | Pretendard-SemiBold.ttf | 600 |
| Segoe UI Bold | segoeuib.ttf | Pretendard-Bold.ttf | 700 |
| Segoe UI Black | seguibl.ttf | Pretendard-Black.ttf | 900 |
| Malgun Gothic Semilight | malgunsl.ttf | Pretendard-Light.ttf | 300 |
| Malgun Gothic Regular | malgun.ttf | Pretendard-Regular.ttf | 400 |
| Malgun Gothic Bold | malgunbd.ttf | Pretendard-Bold.ttf | 700 |

Static에는 350 굵기가 없으므로 Segoe Semilight는 300 윤곽을 사용하고 Windows 대상의 weight metadata는 보존한다. Variable은 350을 실제 instantiate한다. 기본 빌드의 9개 출력은 **정적 TTF**다. `--installable`은 추가로 실제 weight 가변 `SegUIVar_system_mod.ttf`를 생성한다. Windows 원본의 축 범위, 명명된 Small/Text/Display 인스턴스와 이름을 유지한다. Pretendard에는 opsz 디자인이 없으므로 opsz 좌표는 받되 같은 윤곽을 사용하며 Segoe의 광학 크기 디자인을 재현하지 않는다. 현대 Windows UI 일부가 원래 글꼴을 계속 사용하므로 전체 OS의 완전한 통일을 보장하지 않는다. 별도 italic 생성은 이번 한국어 builder의 지원 대상이 아니다.

Microsoft는 Malgun Gothic을 한국어 UI 글꼴로 설명하고 Windows 11에 세 원본 파일을 포함한다. 따라서 Segoe UI만 생성하는 것보다 Malgun 이름·metadata를 가진 결과물까지 준비하는 것이 필요하다고 판단했다. 단, 특정 시작 메뉴/설정 화면의 실제 fallback 선택은 이번 작업에서 추적하지 않았다.

- [Microsoft: UI typography](https://github.com/MicrosoftDocs/windows-dev-docs/blob/docs/hub/apps/design/signature-experiences/typography.md)
- [Microsoft: Malgun Gothic](https://learn.microsoft.com/en-us/typography/font-list/malgun-gothic)
- [Microsoft: Windows 11 font list](https://learn.microsoft.com/en-us/typography/fonts/windows_11_font_list)
- [Pretendard 공식 릴리스](https://github.com/orioncactus/pretendard/releases/tag/v1.3.9)

## 빌드 전용 사용 방법

관리자 권한·MacType·FontForge·추가 복원 지점 생성이 필요하지 않다. 이미 만든 시스템 복원 지점은 유지한다. 저장소를 임시 작업 폴더에 체크아웃하고 Python 3.12 환경에서 실행한다.

```powershell
git clone --branch pretendard-korean-support https://github.com/kbm323/SyrianSegoe.git
cd SyrianSegoe
python -m venv .venv
.venv\Scripts\python -m pip install -r src/requirements-korean.txt
```

공식 Pretendard 1.3.9 ZIP을 별도 임시 폴더에 풀고 **`public/static/alternative`의 TTF**를 사용한다. `public/static`의 기본 OTF/CFF 파일은 이 builder에서 지원하지 않는다. 명시적으로 오류를 반환한다. 정확한 upstream 지원 환경과 동일한 Python/FontTools 버전은 requirements에 기록했다.

```powershell
.venv\Scripts\python src/korean_builder.py `
  --source "C:\temp\Pretendard\public\static\alternative" `
  --references "C:\Windows\Fonts" `
  --output "C:\temp\SyrianSegoe-build-static"
```

Variable 입력:

```powershell
.venv\Scripts\python src/korean_builder.py `
  --source "C:\temp\Pretendard\public\variable\PretendardVariable.ttf" `
  --references "C:\Windows\Fonts" `
  --output "C:\temp\SyrianSegoe-build-variable"
```

출력 디렉터리는 **새 경로**여야 한다. 기존 출력·원본 파일은 덮어쓰지 않는다. 시스템 Fonts 폴더나 원본 참조 디렉터리 내부로 출력할 수 없다. 모든 결과가 검사에 통과해야 최종 출력 폴더를 만든다. 실패하면 임시 staging만 정리하며 설치하지 않는다. `--segoe-only`는 Malgun 대상 파일 생성을 생략한다. 한자 보완을 위해 원본 Malgun Regular/Bold가 여전히 필요할 수 있다.

출력에는 9개의 `*_system_mod.ttf`와 `validation.json`이 생긴다. **TTF를 더블클릭하여 설치하거나 Windows Fonts로 복사하지 않는다. 기존 GUI의 Build & Apply도 이번 한국어 작업의 사용 방법이 아니다.** 향후 적용 기능과 UI 검증은 별도 작업이다.

## 검증과 metrics

자동 검사는 cmap, glyph order, name, OS/2, head, hhea 및 모든 테이블의 decompile/recompile 가능 여부를 검사한다. 소스 cmap 전체와 원본 대상 cmap이 생성물에 남아 있는지도 검사한다. U+AC00 `가`, U+B098 `나`, U+D55C `한`, U+AE00 `글`을 포함한 현대 한글 전체와 아래 문자열을 필수 검사한다.

```text
가나다라마바사아자차카타파하
한글 Windows 시스템 글꼴 테스트
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
0123456789
₩ $ € ¥
→ ← ↑ ↓
㈜ ① ② ③
漢字
```

보고서는 EM, hhea ascent/descent/lineGap, OS/2 typo ascent/descent/lineGap, WinAscent/WinDescent, glyph/cmap 수, family/weight, 실제 한글 범위별 cmap 수, 소스/참조/출력 SHA256을 기록한다. H/a/0/가/한/글/漢 윤곽 bounds와 테스트 문자의 bounds도 기록한다. 이는 baseline·크기·위아래 잘림을 평가하기 위한 수치 자료이며 실제 화면 렌더링 증거가 아니다.

**일부 전체 글리프 bounds가 Windows 원본 metrics를 초과하는 문제가 남아 있다.** 줄 높이를 임의 확대하거나 모든 글리프를 과도하게 축소하여 문제를 숨기지 않았다. `outline_exceeds_windows_bounds`, `outline_exceeds_hhea_bounds`, `test_text_exceeds_windows_bounds`를 검토하고, 어느 하나의 수치 검사 성공만으로 적용을 승인하지 않는다. FontTools 병합 과정에서 TrueType hint 프로그램이 제거될 수 있어 작은 크기의 ClearType 표시도 별도 확인해야 한다.

2026-10-02 검증 환경은 Windows 11 25H2 build 26200.9457, Python 3.12, FontTools 4.66.1이다. **빌드/파일 검사만 검증**했으며 OS 적용을 검증한 버전은 없다. 원본 README의 Windows 10 21H2 / Windows 11 24H2·25H2 검증 주장은 이 한국어 브랜치의 적용 검증으로 승계하지 않는다. 상세 결과는 `docs/validation`에 기록한다.

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python -m compileall -q src tests
```

Windows 실행 파일 패키징:

```powershell
.venv\Scripts\python -m pip install -r src/requirements-build.txt
# 활성화된 가상 환경의 python을 사용
.venv\Scripts\Activate.ps1
.\build.ps1
```

GUI와 빌드 전용 CLI를 각각 패키징한다. GUI를 실행하거나 적용·크기 변경·원본 Clone 설치를 검증용으로 호출하지 않는다. CI도 synthetic 글꼴 테스트와 패키징만 실행하며 글꼴을 설치하지 않는다. FontForge 원본 엔진은 코드·회귀 테스트를 검증했지만 실제 FontForge 런타임 생성은 이번 환경에 FontForge가 없어 검증하지 않았다.

## 아이콘·이모지 보호

Segoe Fluent Icons의 `SegoeIcons.ttf`, Segoe MDL2 Assets의 `segmdl2.ttf`, Segoe UI Emoji의 `seguiemj.ttf`, Segoe UI Symbol 및 Windows 아이콘 리소스는 대상에서 제외한다. builder는 이 파일들을 글리프 공급원으로도 사용하지 않는다. Segoe UI 텍스트 글꼴 자체에 포함된 UI symbol은 원본 대상에서 보존한다. Windows 기본 아이콘 디자인은 변경하지 않는다.

## 원본 백업과 Restore

빌드 전용 경로는 원본을 읽기만 하므로 시스템 복구할 변경이 없다. 실패한 빌드는 새 출력 경로로 다시 수행한다. 생성 파일을 보관할 필요가 없으면 그 임시 출력 폴더만 정리한다. 시스템 Fonts나 레지스트리를 수정할 필요가 없다.

기존 GUI의 원본 백업 위치는 `%USERPROFILE%\Documents\SyrianSegoe\Original_Segoe_Backups`다. Segoe UI 원본 13개와 Malgun 3개를 허용 목록으로 백업하며 최초 파일을 덮어쓰지 않는다. `backup_manifest.json`의 해시와 실제 백업이 다르면 재사용을 차단한다. 이미 존재하던 upstream 백업은 현재 내용의 해시를 등록할 뿐, 그 파일이 역사적으로 올바른 원본이었다고 증명하지 못한다.

기존 비한국어 GUI 적용 경로는 전체 생성물을 먼저 검사하고 `font_transaction.json`에 변경 전 레지스트리 값과 새 파일 해시를 기록한다. 원본 Windows 파일을 덮어쓰지 않고 새 이름으로 설치한다. 중간 실패 시 기록된 값을 복원하고 해당 새 파일만 제거한다. 다음 GUI 실행에서 journal이 남아 있으면 새 적용을 막는다. Restore는 journal을 먼저 사용하여 변경 전 값을 복원한다.

복구 절차(이전 GUI 적용이 있었던 경우):

1. 백업 폴더와 `font_transaction.json`을 보존한다.
2. GUI의 Restore Original Fonts를 실행한다. 기록된 레지스트리 연결을 되돌린다.
3. 파일 잠금으로 cleanup에 실패하면 journal이 유지된다. 재부팅 후 Restore를 다시 수행한다.
4. journal이 없는 과거 upstream 적용은 기존 Segoe UI 기본 파일명 연결 복구를 사용한다. 과거 사용자 지정 레지스트리 값까지 복구했다고 보장할 수 없다.
5. Windows 업데이트 후 원본 파일이 달라지면 백업 보고서 `changed_sources`를 확인한다. 오래된 백업을 현재 시스템 원본 위에 강제로 복사하지 않는다. 현재 OS의 원본과 journal을 다시 검토한다.

가짜 레지스트리와 임시 디렉터리에서 중간 실패/재시작 후 journal Restore/누락 weight/아이콘 차단을 테스트했다. 실제 관리자 권한·파일 잠금·갑작스러운 종료·재부팅·Windows 업데이트 후 복구는 미검증이다. rollback 역시 절대적인 원복 보장이 아니다. 한국어 설치 명령은 아래에 추가되어 있으나 Malgun의 실환경 설치 후 Restore는 미검증이다.

## 실제 적용 전 확인 사항

- 한글·원본 UI 문자 누락이 없고 모든 출력 테이블 검사가 통과해야 한다.
- 글자 bounds 초과 원인을 해결하거나 영향을 평가하고, 작은 크기/DPI별 한글·영문·숫자 baseline과 잘림을 실제로 확인해야 한다.
- Variable의 실제 UI 선택·로그인 화면과 italic 지원은 추가 검증 대상이다.
- VM 또는 복구 가능한 테스트 환경에서 설치·중간 실패·재부팅·Restore를 검증해야 한다.
- system filename 충돌이 없어야 하고 Fluent Icons·MDL2·Emoji·아이콘 리소스 해시가 유지돼야 한다.
- 원본 백업과 현재 OS 버전의 일치, journal 보존, 시스템 복원 경로를 확인해야 한다.
- 사용자에게 결과와 남은 위험을 보고하고 **명시적인 실제 적용 지시**를 받아야 한다.

이 조건을 충족하기 전에는 한글 glyph 누락, Restore 불완전, metrics 초과, 파일 충돌, 아이콘/Emoji 영향, 미검증 강제 파일 교체를 동반하는 적용을 진행하지 않는다.

## 배포 범위

GitHub에는 소스·테스트·문서·검증 숫자와 해시만 저장한다. 설치된 Windows 원본, 파생 TTF, Pretendard 다운로드 ZIP, EXE는 이번 PR에 커밋하지 않는다. Pretendard의 OFL과 Microsoft 원본/파생 글꼴의 배포 조건을 별도로 검토해야 한다. 이 소스의 MIT 라이선스가 포함 글꼴의 배포 권한을 부여하지 않는다.

### 백업 위치와 복사 실패 복원

기존 GUI의 백업과 변경 기록은 `%USERPROFILE%\Documents\SyrianSegoe\Original_Segoe_Backups`에 보관합니다. 단일 실행 파일의 임시 압축 해제 폴더가 삭제되어도 유지됩니다. 이전 버전의 코드 폴더에 있는 백업은 자동 이동하지 않으며, 이전 적용 상태라면 해당 버전에서 먼저 복원하세요. 복사 중 실패한 파일은 생성 시 기록한 파일 식별자가 일치하는 경우에만 삭제합니다. 외부에서 바뀐 파일이나 잠긴 파일은 변경 기록을 유지하고 수동 확인 또는 재시작 후 복원을 요구합니다.

검증 결과와 각 출력의 메트릭/해시는 [검증 기록](docs/validation/README.ko.md)을 참고하세요.


## 실제 적용용 패키지와 설치·복원

일반판도 빌드 전용 모드에서는 지원합니다. 아래 전체 설치 패키지는 **공식 Pretendard Variable TTF**를 사용합니다. 기존 빌더와 기존 journal 설치·복원 함수를 그대로 재사용하며 새 런타임 의존성은 없습니다.

일반 PowerShell에서 빌드와 설치 계획 검사를 실행합니다. 이 두 명령은 시스템을 변경하지 않습니다.

```powershell
.venv\Scripts\python.exe src/korean_builder.py --installable `
  --source "C:\temp\Pretendard\public\variable\PretendardVariable.ttf" `
  --output "C:\temp\SyrianSegoe-Korean-installable"
.venv\Scripts\python.exe src/font_transaction.py plan --build "C:\temp\SyrianSegoe-Korean-installable"
```

설치용 모드는 Segoe 6종, 맑은 고딕 3종, Segoe UI Variable 1종을 묶습니다. Windows 원본의 줄높이 메트릭을 유지하고, 세로 조정 과정에서는 Pretendard의 가로 advance width를 변경하지 않습니다. 세로 범위를 초과한 예외 글리프만 baseline 기준으로 높이를 조정합니다. 영향을 받은 글리프 수는 보고서의 `fitted_glyphs`에 기록합니다. 일반 한글을 일괄 축소하지 않습니다. 조정된 글리프는 원래 디자인과 높이가 달라질 수 있으며 기존 hint 명령은 제거합니다. Variable의 모든 master는 같은 glyph topology와 조정 비율을 사용합니다. FontTools가 이 PC의 Windows 25H2 원본 SegUIVar GPOS variation 인덱스를 처리하지 못하는 문제를 피하려고 참조 보조 글리프는 기본 인스턴스의 GSUB와 윤곽을 사용합니다. Pretendard의 기본 굵기 GSUB/GPOS를 모든 Variable master에 동일하게 유지합니다. 가중치에 따라 달라지는 feature 선택과 kerning 보간은 재현하지 않습니다. 이는 master별 lookup 구조가 달라 합성이 실패하는 경우를 피하기 위한 제한입니다.

적용을 결정한 뒤 **같은 Windows 사용자 계정의 관리자 PowerShell**에서 다음 명령을 실행합니다. apply만 시스템을 변경합니다. 기존 원본 파일을 덮어쓰지 않고 별도 생성 파일을 설치한 후 Fonts 레지스트리 연결을 바꿉니다. 실제 적용에는 재부팅이 필요합니다. 기존 FontSubstitutes에 해당 글꼴 대체 설정이 있으면 충돌을 피하도록 설치를 거절합니다. FontCache 삭제, 서비스 종료, 보호 해제, MacType 설치 및 자동 재부팅은 하지 않습니다.

```powershell
.venv\Scripts\python.exe src/font_transaction.py apply --build "C:\temp\SyrianSegoe-Korean-installable"
```

백업/변경 기록/`Restore.reg`는 `%USERPROFILE%\Documents\SyrianSegoe\Original_Segoe_Backups`에 남습니다. 잠겨 삭제할 수 없는 생성 파일은 journal을 유지하며 재시작 후 다시 restore해야 합니다.

```powershell
.venv\Scripts\python.exe src/font_transaction.py restore
```

GUI/Python을 실행하기 어려울 때는 관리자 PowerShell에서 아래 **레지스트리 연결만 먼저 복원**한 뒤 재부팅합니다. 이후 정상 restore로 생성 파일을 정리합니다. REG 파일만으로 생성 파일이 삭제되지는 않습니다.

```powershell
reg import "$env:USERPROFILE\Documents\SyrianSegoe\Original_Segoe_Backups\Restore.reg"
```

`build.ps1`은 기존 GUI, 빌드 CLI, 설치·복원 CLI를 패키징합니다. 실행 파일을 사용하는 경우 `SyrianSegoe-Korean-Build.exe`와 `SyrianSegoe-Korean-Install.exe`에 각각 같은 인수를 전달하면 됩니다. 이 PC에서는 Windows 앱 제어가 자체 생성 EXE 실행을 차단했으므로 정책을 끄지 말고 Python 소스 명령으로 실행하세요.

Windows 업데이트로 원본 해시가 바뀌거나 출력 파일이 수정되면 plan/apply는 거절합니다. 다시 빌드해야 하며 이전 적용이 있다면 먼저 복원해야 합니다. 시작 메뉴 등 일부 UI가 레지스트리 대신 원본 경로를 직접 읽으면 변경이 반영되지 않을 수 있습니다. 보호된 원본을 강제로 덮어쓰는 기능은 포함하지 않습니다.

이 변경은 [Ponytail](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md)의 재사용 우선 지침에 따라 기존 builder/FontTools와 install_font_set/restore_font_set을 연결했습니다. 새 폰트 엔진이나 별도 설치 프레임워크를 추가하지 않았습니다.
