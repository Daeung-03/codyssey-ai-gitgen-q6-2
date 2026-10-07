# AI 기반 Git 커밋 메시지·PR 초안 생성기

Git 변경 사항을 읽어 OpenAI 호환 Chat Completions API로 커밋 메시지 또는 Pull Request 초안을 만드는 Python CLI입니다. 결과는 터미널에만 출력되며, 사용자가 검토한 뒤 직접 적용합니다.

## 준비

- Python 3.10 이상, Git
- 제공받은 virtual key
- 이 프로젝트를 독립적인 Git 리포지토리로 구성하고 **리포지토리 루트**에서 실행

외부 Python 패키지는 필요하지 않습니다. API 키는 환경변수로 설정합니다.

```sh
export AI_API_KEY="YOUR_VIRTUAL_KEY"
```

키를 `.env`나 소스 코드에 기록하지 마세요. `.env` 파일은 `.gitignore`에 포함되어 있습니다.

## 실행

```sh
python3 main.py commit
python3 main.py pr
python3 main.py commit --safe-mode
python3 main.py pr --model gpt-5-mini --temperature 1 --max-tokens 2048
```

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--model` | `gpt-5-mini` | OpenAI 호환 API에 전달할 모델명 |
| `--temperature` | `1.0` | 생성 온도(0~2). GPT-5 계열에서는 기본값일 때 요청에서 생략하며, 다른 값을 지정하면 API 지원 여부에 따라 오류가 날 수 있습니다. |
| `--max-tokens` | `2048` | 최대 생성 토큰 수(1~16384). GPT-5 계열에는 `max_completion_tokens`, 그 외 모델에는 `max_tokens`로 전달합니다. |
| `--safe-mode` | 끔 | 전송 파일을 최대 10개, diff를 최대 200줄·30,000자로 제한합니다. |

API 요청 형식은 [OpenAI Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)를 따릅니다. 요청은 제공된 주소인 `POST https://copa.codyssey.kr/v1/chat/completions`로 전송하며 `Authorization: Bearer <virtual-key>` 헤더를 사용합니다. `commit`과 `pr`은 실행당 각각 API를 1회 호출합니다.

## 출력 예시

```text
[INFO] Git 변경 파일: 2개
 M main.py
?? README.md
[INFO] Git diff 수집 완료: 42줄
[INFO] 민감정보 패턴 마스킹 적용
[INFO] AI API 요청 중... (호출 횟수: 1)
--- Commit Message ---
feat: Git 변경 사항으로 커밋 초안 생성

- main.py에 Git diff 수집과 OpenAI 호환 API 호출 추가
- README.md에 실행 방법과 안전 모드 설명 추가
```

```text
--- PR Title ---
feat: AI 기반 커밋·PR 초안 생성 기능 추가

--- PR Body ---
## Why
- 변경 사항을 일관된 형식으로 설명하기 위해 초안 생성이 필요합니다.

## What
- Git 상태와 diff를 수집해 OpenAI 호환 API로 전달합니다.

## How to Test
- `python3 main.py commit`과 `python3 main.py pr`의 출력을 확인합니다.
```

예시는 형식 설명용이며 실제 출력은 변경 내용과 모델 응답에 따라 달라집니다. 커밋 제목은 최대 72자, PR 제목은 최대 80자로 다듬습니다. PR 본문에는 `Why`, `What`, `How to Test`와 각 섹션의 불릿이 필수입니다.

## 변경 사항과 안전

- `git status`와 `git diff`로 staged·unstaged·untracked 변경을 읽습니다. 변경 사항이 없으면 API를 호출하지 않습니다.
- `.env`, 개인키 등 알려진 민감 파일명은 전송 대상에서 제외합니다. API 키·토큰·이메일의 알려진 패턴은 기본 실행에서도 마스킹합니다.
- 마스킹은 모든 비밀값을 탐지한다고 보장할 수 없습니다. 실행 전 `git diff`를 확인하고, 민감정보가 있을 수 있거나 변경이 큰 경우 `--safe-mode`를 사용하세요. 바이너리·큰 untracked 파일은 건너뜁니다.
- 실행당 요청 1회이므로 호출 횟수와 비용을 고려해 필요한 때만 실행하세요.
- 초안이 실제 변경 내용과 테스트 방법을 정확히 설명하는지 검토한 뒤 복사해 사용하세요. 이 도구는 `git commit`, `git push`, GitHub PR 생성을 실행하지 않습니다.

## 오류 상황

- **변경 사항 없음:** 안내 메시지를 출력하고 종료합니다.
- **키 누락:** `AI_API_KEY` 설정 방법을 안내합니다.
- **Git 루트 아님:** 현재 Git 루트를 보여주고 실행 위치를 수정하도록 안내합니다.
- **API 실패:** HTTP 상태 또는 연결 오류 원인을 출력합니다. 모델이 지정한 파라미터를 지원하지 않으면 다른 값이나 모델을 선택하세요.
- **응답 형식 오류:** 요구한 JSON·제목·PR 섹션을 만들지 못한 경우 오류를 알립니다. 다시 실행할 수 있지만 요청이 1회 추가됩니다.

## 개발 검증

```sh
python3 -m unittest discover -s tests -v
```

단위 테스트는 임시 Git 리포지토리와 가짜 API 응답을 사용합니다. 실제 API 호출 확인에는 본인의 virtual key가 필요합니다.
