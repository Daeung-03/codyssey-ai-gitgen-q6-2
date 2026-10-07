# AI 기반 커밋 메시지·PR 초안 생성기 구현 계획

## 목표와 범위

- Python 3.10+ 터미널 CLI에서 Git 변경 사항을 읽고 제공된 OpenAI 호환 Chat Completions API 주소로 커밋 메시지 또는 PR 초안을 생성한다.
- `commit`, `pr` 명령의 결과를 사용자가 검토·복사할 수 있게 출력한다. 실제 커밋, push, GitHub PR 생성은 CLI 기능에 포함하지 않는다.
- `docs/PROBLEM.md`의 필수 요구사항과 GitHub 리포지토리·README 제출물을 완성한다. 보너스 과제는 제외한다.

## 현재 상태와 선행 조건

- 계획 작성 전 `Q6_2`에는 `docs/PROBLEM.md`만 있었으며, CLI 소스와 README는 아직 없다.
- 현재 Git 루트는 `Q6_2`의 상위 디렉터리다. 구현·검증 전에 이 프로젝트를 독립적인 Git 리포지토리로 구성하고, CLI는 Git 루트에서 실행하도록 확인해 다른 과제의 변경 사항이 입력에 섞이지 않게 한다.
- 실제 API 호출 검증에는 유효한 virtual key가 필요하다. 키는 `AI_API_KEY` 환경변수로만 읽고 저장소에 기록하지 않는다.

## CLI와 API 설계

| 항목 | 계획 |
| --- | --- |
| 실행 | `python main.py commit` 또는 `python main.py pr` |
| 공통 옵션 | `--model`, `--temperature`, `--max-tokens`, `--safe-mode` |
| 기본 모델 | 제공된 호출 예시의 `gpt-5-mini` |
| 요청 | `POST https://copa.codyssey.kr/v1/chat/completions` |
| 인증·본문 | `Authorization: Bearer <AI_API_KEY>`, JSON `model`·`messages` 및 지정한 생성 파라미터 |
| 응답 | Chat Completions의 생성 텍스트를 추출하고 명령별 형식으로 검증·출력 |

각 명령은 API를 1회 호출하고 호출 횟수를 로그에 표시한다. 모델별 파라미터 허용 범위는 실제 호출에서 확인하며, 거부되면 HTTP 상태와 오류 내용을 사용자에게 설명한다.

## 구현 순서

1. **Git 입력 수집:** `git status`로 변경 파일을 확인하고 `git diff`로 staged·unstaged 변경을 모은다. untracked 파일도 누락되지 않도록 diff 입력을 구성한다. 변경이 없으면 안내 후 API 호출 없이 종료한다.
2. **안전한 입력 구성:** `--safe-mode`에서 API 키·토큰 형태와 이메일 등 알려진 패턴을 마스킹하고, 전송할 diff 크기를 제한한다. 바이너리·과도하게 큰 파일은 제외하거나 축약하며 적용 내용을 출력한다.
3. **OpenAI 호환 API 연결:** 표준 Python HTTP/JSON 기능으로 요청·응답을 처리한다. 키 누락, 네트워크 오류, 인증 실패, 비정상 응답을 구분해 알린다.
4. **프롬프트와 결과 검증:** 변경 요약과 출력 양식을 명령별 프롬프트에 담는다. 커밋 제목은 1줄·최대 72자(50자 이내 권장), PR 제목은 1줄·최대 80자로 제한한다. PR 본문은 `Why`, `What`, `How to Test` 헤더와 각 섹션의 불릿 1개 이상을 요구한다. 형식이 어긋나면 로컬 후처리·검증으로 다듬고, 충족하지 못하면 명확히 오류를 알린다.
5. **사용 문서와 제출:** README에 설치, `AI_API_KEY` 설정, 두 명령과 옵션, 출력 예시, 민감정보·비용 주의사항을 작성한다. 소스와 README를 GitHub 리포지토리에 push해 파일 구조와 커밋 기록을 확인한다.

## 완료 확인

- 변경 사항 유무, staged·unstaged·untracked 입력에 따라 CLI가 의도대로 동작한다.
- 유효한 키로 `commit`과 `pr`을 각각 실행해 OpenAI 호환 API 호출 및 형식에 맞는 출력을 확인한다.
- 키 누락·인증 실패·네트워크 오류와 잘못된 AI 출력에서 원인을 알 수 있는 메시지가 나온다.
- `--safe-mode` 입력에 알려진 민감정보 패턴이 남지 않으며, README만으로 실행을 재현할 수 있다.
- GitHub 저장소에 필수 파일이 올라가 있다.
