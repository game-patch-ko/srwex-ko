<div align="center">

**한국어** | [日本語](README.ja.md)

# 🤖 슈퍼로봇대전 EX 한국어 패치 (개발 중)

슈퍼 패미컴 **「スーパーロボット大戦EX」**(1994)를 한국어로 옮기는 비공식 팬 패치

</div>

> **아직 배포 전입니다.** 대사와 메뉴 번역, 기본 화면 검증까지 끝났고, 배포 준비 중입니다.

## 현재 상태

| 항목 | 상태 |
|---|---|
| 번역 | 대사 33블록 전부, 파일럿·유닛·무기 이름, 지형·용어, 메뉴·프롤로그 창 — 6,487조각 |
| 한글 출력 | ROM을 1.5MB → 2MB로 늘리고 12px 도트 글꼴 MonaS12로 한글을 넣음 |
| 검증 | 모든 대사를 실제 게임 렌더러로 출력해 멈춤 0건, 데모 전투·지도 메뉴 화면 확인 |
| 그래픽 글자 | 스테이지 도입 제목 64개, 타이틀 로고 「슈퍼로봇대전」 |
| 남은 일 | 정식 안내 문서, 인터미션 화면 확인(플레이 피드백) |

## 직접 빌드

원본 ROM `Super Robot Taisen EX (J).smc`(헤더 없음, CRC32 `239621A0`)를 저장소 맨 위 폴더에 두고:

```
cd build
python srwtext.py build      # out/srwex_ko.smc, out/srwex_ko.ips
```

- Python 3과 Pillow가 필요합니다.
- 글꼴 `MonaS12.ttf`(Monad ABXY, SIL Open Font License 1.1)를 `tools/fonts/mona/MonaS/01 Main/`에 두거나 환경 변수 `SRW3_MONAS12`로 경로를 알려 주세요.
- 구조와 작업 방법은 [HANDOFF.md](HANDOFF.md)에 있습니다.

같은 방식으로 만든 [제3차 슈퍼로봇대전 한국어 패치](https://github.com/game-patch-ko/srw3-ko)의 도구를 이 게임에 맞게 옮겨 썼습니다.

## 권리와 안내

- 비공식 팬 번역이며 원저작권자(반프레스토, 각 작품 권리자)와 관계가 없습니다.
- 원본 ROM은 포함하지 않으며 배포하지 않습니다. 직접 가진 카트리지에서 추출한 ROM에만 쓰세요.
- 이 프로젝트는 Anthropic의 AI 모델인 Claude와 함께 작업했으며, 책임은 작성자에게 있습니다.
