# 인계 문서 — 슈퍼로봇대전 EX(SFC) 한글화

작성: 2026-11-24. 새 세션은 이 문서를 먼저 읽을 것. 주소·길이는 기억이 아니라 **파일과 ROM으로 확인**한다.
제3차 한글화(`C:/work/sfc/srw3-ko`)와 같은 방식·표기 기준이다. **3차 폴더는 읽기만 하고 절대 고치지 않는다**(필요한 도구는 이 폴더로 복사해 씀, 참고용 사본은 `ref3/` — git에서 제외, 없으면 3차 저장소에서 다시 복사).

## 1. 대상과 방식
- `Super Robot Taisen EX (J).smc` (LoROM 12Mbit, 헤더 없음, CRC32 `239621A0`). 원본은 수정하지 않는다. 결과는 `out/`.
- 3차와 같은 엔진 계열이지만 **코드 배치·제어 코드 번호가 다르다**(뱅크별 바이트 일치 1~11%). 주소는 모두 새로 찾았다.
- 2MB 확장(뱅크 $B0~$BF), 한글 글꼴 MonaS12(3차 v0.9.1 이후와 같음).
- **한글 인코딩(3차와 다름)**: 접두 `EC ED EE EF F0 F1 F2 F3` × 256 = 2,048칸. 번역에 **실제로 쓰인 음절만** KS X 1001 순서로 칸에 배정(빌드할 때마다 계산). 3차 전체 번역이 1,012음절이었으므로 충분. 전각 공백 `　`은 12px 빈칸(원본 `$F2FF`) 용도.

## 2. 핵심 기술 사실
| 항목 | 위치 |
|---|---|
| 1바이트 글꼴 | `$20:E1BC` (16바이트/글자, 3차 글꼴과 같은 모양을 2줄 아래로 그림) |
| 한자 글꼴 | `$21:8000` 1,024자 (F0~F3 xx). 포인터 초기화 `$80:8323` ← `$20:8003/8006` |
| 대사 블록 표 | `$0C:8000` 3바이트 × 33 |
| 이름·창 표 목록 | `$03:8090` + 3t (t=0~2 창 레이아웃 뱅크 $05, 4 유닛, 5 풀네임, 6 약칭, 7·8 무기, B 지형, C 곡명, D 속성·설정, E 스테이지 제목) |
| 대사 해석 | `$81:85DE`(읽기 `$81:8B3F`, 포인터 `$CA`), 제어 점프표 `$81:896D` |
| 창 해석기 | `$80:B9A4`(읽기 `$80:BF2C`, 포인터 `$1A`), 점프표 `$80:C3E9`. 글자 모드 = `F5` 인자 bit6(16비트 BIT라 `$2B` bit6) |
| 글리프 | `$80:BA96`. 2바이트: 창 경로 `$80:BADF`→BB94, 대사 경로 `$80:BC75`→BD54 |

대사 제어 코드(3차보다 하나씩 밀림): `F4` 줄바꿈 `F5` 키 대기 `F6 x` 대기 `F7 e t` 호출 `F8 n p..` 무작위 `F9 s x y`(포인터 없음) `FA` 조건/점프 `FB s`(1~6 이름 삽입) `FC ffff` 플래그 `FD` 창 지우기 `FE x` 얼굴 `FF` 끝. **EC~EF도 끝(FF와 같은 처리)**.
창 코드 길이: F0:4 F1:3 F2:4 F3:4 F4:1 F5:2 F6:2 F7:3 F8:2 F9:5 FA:2 FB:1 FC:3 FD:3 FE:2 FF:1. 글자 모드에서는 F0~F3이 한자 접두.

## 3. 패치(`build/build_ko.py`)
- `$81:85E6` 대사: EC~F3을 접두로(코드 상위 = 접두 − $EB).
- `$80:B9BD` 창 글자 모드: 같은 방식. 원래 EC~EF 아이콘 글자([M][HP][B][P])는 빈 1바이트 코드로 옮김(`ICON_MAP`, 빌드가 원문 바이트도 자동 변환). 추출된 텍스트 전체 조사(2026-11-24): EC~EF 아이콘은 텍스트에 한 번도 안 나옴(코드가 직접 그림). ICON_MAP은 안 쓰이는 03·04·0C·61로 둠.
- `$80:BADF`/`$80:BC75` → `$B0:8000~` 훅: 글꼴 포인터를 `$B1:8000 + 칸×32`로 바꿈.
- 1바이트 `。`(E4)·`、`(3A)를 `.` `,`로 다시 그림.
- 대사 블록 22 #27은 포인터가 $8000 미만인 깨진 미사용 항목 → 빈 문자열로 처리(`valid_dlg`).

## 4. 작업 방법
```
cd build
python srwtext.py extract          # 없는 스크립트만 생성 (--force는 번역을 지움!)
python setko.py --file ../tr/x.tsv # 번역 반영
python srwtext.py build            # out/srwex_ko.smc + .ips + _labels.tsv
python srwtext.py build --no-tr    # 재배치만(회귀 검사)
```
- 번역 보조: `tr/AGENT_BRIEF.md`(에이전트 지침), `tr/export_todo.py`, `tr/reflow.py [--battle]`, `tr/check_tsv.py`, `tr/check_prefix.py`.
- 이름 표: `tr/<표>_names.tsv`(라벨·JP·KO) → `python tr/apply_names.py`. 일괄 채우기 `tr/fill_names.py`, 사전 `tr/names_*.txt`, 3차 표기 사전 `tr/srw3_names.json`.
- 창 레이아웃: `python tr/layruns.py export layXX > tr/layXX_runs.txt` → `tr/layXX_ko.txt`(구간마다 한 줄, `=`는 원문) → `python tr/layruns.py build tr/layXX_runs.txt tr/layXX_ko.txt tr/layXX.tsv` → setko.
- 폭 기준: 대사 첫 줄 240px(화면에서 확인함), 이어지는 줄 232px, 3줄. 전투 대사 파일(dlg00, dlg14~1C, 1E, 1F, 20)은 200/192px·2줄(데모 전투에서 $0E34=50단위, $0E35=2줄 실측 2026-11-24).

## 5. 자동 실행 (Mesen2, `tools/mesen`)
- PowerShell: `Start-Process tools\mesen\Mesen.exe -ArgumentList '--testrunner','--timeout=300',<rom>,<lua> -Wait -NoNewWindow`
- 캡처 Lua: `tools/rt/boot.py`(새 게임 진행), `tools/rt/idle.py`(무입력 → 약 4,000프레임부터 데모 전투), `tools/rt/menu.py`(새 게임 → 지도에서 메뉴 열기, 30프레임마다 캡처).
- 대사 전체 렌더러 검사: `python tools/rt/make_chain.py dlgXX game <폴더> <lua>`(전투 파일은 `demo … 3600`) → `out/srwex_verify.smc`로 실행 → `chain.txt`의 `seg/wrap/stall/done`. 원문 비교용 `make_chain_jp.py`(번역 없는 ROM).
- 줄 폭 한도 기록: `tools/rt/wlim.lua`.
- **세이브 충돌 방지**: 자동 실행은 사본(`out/srwex_auto.smc`, `srwex_verify.smc` 등)으로만. Mesen은 ROM 파일 이름으로 세이브를 공유한다. 3차 ROM 이름(`srw3_*`)과 겹치지 않게 `srwex_*`만 쓸 것.
- Lua 표 리터럴 실수 주의: 입력 콜백에서 오류가 나면 조용히 입력이 안 들어간다(2026-11-24 `menu.py` 중괄호 중첩으로 한 번 겪음).

## 6. 현재 상태 (2026-11-24)
- **번역 완료**: 6,487조각(대사 33블록 전부, 이름·용어 표 832항목, 창 레이아웃 lay00·01·02). 남은 한자 조각 12개는 대사가 아닌 창 데이터(원문 유지). 한글 1,094음절 사용(2,048칸 중).
  - 대사는 번역 에이전트 9개가 `tr/dlgXX_*.tsv`로 작성 → setko 반영. 이름·레이아웃은 메인 세션이 직접.
  - 표기 통일: かくれみの `은신 망토`, 隠行の術 `은형의 술`, ソラティス `솔라티스`, グラン・ガラン `그란가란`. 사투리(로드니 등 간사이)는 경상도 말씨.
  - 한자표 판독 오류 수정(에이전트 보고로 발견): 奥 兎 裡 套 簒 字 壟 躍 澪 借 拳/挙 薬 侮 蓮. 수정 후 `python tr/refresh_jp.py`로 JP 줄만 다시 해석(KO 유지).
- **검증**
  - 대사 33개 파일 전체를 실제 렌더러로 출력(`make_chain.py`): 전부 끝까지 출력, 멈춤 0. 줄 넘침은 S06D750(얼굴 전환 `{face}` 연쇄)뿐이며 **원본 일본어도 테스트 장치에서 같은 위치에서 넘침** — 두 창(위·아래)을 쓰는 장면을 장면 설정 없이 불러서 생긴 것으로 판단, 실제 장면 확인 필요.
  - 데모 전투: 유닛·파일럿·무기 이름, 전투 대사, HP 창 정상.
  - 지도: 턴 메뉴, 턴 창, 지형 정보 창 정상. 프롤로그 첫 화면 정상.
  - 이름 표는 창 해석기 `$80:B981/C19D`와 대사 이름 삽입 `$81:8A34~8AC5`에서만 읽으며 모두 ROM에서 바로 그림 → 빌드의 "check RAM buffers" 경고는 이 경로에선 해당 없음.
- **그래픽 글자(2026-11-24 후반 완료)**
  - 스테이지 도입 제목: `build/titles.py`(빌드 자동 호출), 번역표 `tr/titles.tsv`(세트2 번호·블록·JP·KO). 제목 글꼴 = 그래픽 자료 4번(`$20:91A6`, LZ 32KB, 16×16 글자 4KB 블록 8개, 테두리 색8 + 위→아래 6..1 그러데이션). 시작 시 블록0→VRAM `$7800`, 블록1→`$6000`(공통 스크립트 `$80:DD36`), 스테이지 블록→`$6800`. 첫 줄 = 세트0 묶음 `0E`(第)·숫자·`11`(話), 둘째 줄 = **세트2 묶음 번호**(세트 목록 `$03:80C0`, 세트2 표 `$04:CEFE`, 116항목 중 제목 64개). 스테이지별 블록은 코드를 못 찾아 **블록 후보별 렌더링을 눈으로 읽어** 정함(`analysis/titlematch.py`, `img/tsheet_*.png`). 한글은 MonaS12로 획을 그리고 테두리·그러데이션, 글자 간격 14px. 압축 글꼴 `$B0:8800`, 묶음은 원래 제목 묶음 자리 + `$04:FF60` 빈 곳에 다시 씀. 1화 실제 화면 확인.
  - 타이틀 로고: `build/logo.py`. 로고 = BG1(맵 `$7000`) 팔레트3, 그래픽 자료 47번(`$13:8000`, VRAM 0번지 32KB)의 타일 0x201~0x275, 칸 6줄×18열(행5~10, 열7~24). 「슈퍼로봇대전」을 나눔스퀘어EB로 그려 그 타일만 다시 칠함(파란 「EX」는 별도 층이라 그대로). 압축 자료는 **뱅크 `$BF` 전용**(텍스트 배치 뱅크는 `$B3~$BE`). 실제 화면 확인.
- **추가 수정**: 창 문자열 7개를 `FORCE_TEXT`로 추출·번역(트레이닝 설명, 숨겨진 「슈우 편」, 데이터 오류 2, 작전 설명 2, 행동횟수). 한글 글꼴 빈 칸을 0으로 채움(원본의 빈칸 글자 `$F2FF` 등이 흰 네모로 보이던 문제).
- **화면 확인 추가**: 편 선택, 유닛 명령 메뉴, 미니 상태창, 능력 화면(유닛·파일럿 쪽) 정상. 입력 스크립트 `tools/rt/menu_unit.py`. 인터미션은 1화 클리어 세이브가 없어 미확인.
- **배포 파일(v0.9 베타)**: `dist/README.txt`, `dist/OFL.txt`(MonaS12·나눔스퀘어), `dist/srwex_ko.xdelta`·`.ips`(git 제외, Release 첨부용). 결과 ROM CRC32 `FEBC62A7`, SHA-1 `f660331b19b26d65d831ea907411c5efaa698634`. xdelta3·Flips로 원본 사본에 적용해 MD5 일치 확인. **빌드가 바뀌면 xdelta·IPS·CRC·SHA-1을 다시 만들 것**:
  `cp out/srwex_ko.ips dist/` / `tools/patchers/xdelta/xdelta3-3.1.0-x86_64.exe -e -9 -f -s "Super Robot Taisen EX (J).smc" out/srwex_ko.smc dist/srwex_ko.xdelta`

## 7. 다음 세션에서 할 일 (사용자 지시: 남은 것 처리 후 공개 전환)
1. 정식 README.md·README.ja.md: 3차 저장소 README 형식(특징 표, 원문/한국어 비교 스크린샷 `docs/images/`, 패치 방법, 문제 제보, 동작 원리, 직접 빌드, 권리·Claude 사용 고지). 스크린샷 원본: `tools/shots/`(타이틀 `logo_ko/shot.png`·`logo/shot.png`, 편 선택 `menu4/00840.png`, 1화 제목 `title_ko/`, 대화·전투 `menu4/`·`idle/`, 능력 `unit2/10830.png`). 개발 중 문구 제거.
2. 문제 제보 양식 `.github/ISSUE_TEMPLATE/report.yml`(3차 것 복사·수정).
3. **공개 전 필수: 커밋 `8aeb904`에 원본 게임 그래픽을 풀어 낸 `analysis/img/g04.bin`이 들어가 있다**(다음 커밋에서 삭제·`.gitignore` 추가했지만 기록에는 남음). 공개 전에 그 커밋에서 파일을 빼는 기록 정리(`git rebase`/`filter-repo` + 강제 push)가 필요하며, 강제 push는 사용자 승인이 필요함(2026-11-24 자동 승인 분류기가 거절).
4. 커밋·push → `gh release create v0.9 dist/srwex_ko.xdelta dist/srwex_ko.ips dist/README.txt dist/OFL.txt`(베타라 pre-release 권장, 사용자와 확인) → **`gh repo edit game-patch-ko/srwex-ko --visibility public --accept-visibility-change-consequences`**(사용자가 2026-11-24 공개 전환을 지시함).
5. 이후: 사용자·지인 플레이 피드백(인터미션·엔딩), 얼굴 전환 장면 S06D750 실제 확인.
- git: `main`, 원격 `game-patch-ko/srwex-ko` **비공개**(2026-11-24 생성). 작성자 rity73 noreply(저장소 로컬 설정), 커밋 끝 `Generated automatically using Claude (AI model).`
