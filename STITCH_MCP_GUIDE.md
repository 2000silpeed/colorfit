# Google Stitch MCP 연동 가이드

> ColorFit 디자인 리팩토링을 위한 Google Stitch + MCP 서버 셋업 가이드

## 1. Google Stitch란?

Google Labs에서 만든 AI 기반 UI 디자인 도구. Gemini 2.5 Pro가 텍스트 프롬프트, 스케치, 스크린샷을 받아서 반응형 UI 디자인 + HTML/CSS 코드를 생성한다.

### 핵심 기능
- **텍스트 → UI**: 자연어로 화면 설명하면 완성된 UI 생성
- **멀티 변형**: 한 프롬프트로 여러 디자인 후보 생성
- **인터랙티브 프로토타입**: 화면 연결해서 바로 플레이 가능
- **Figma 내보내기**: 디자인을 Figma에 붙여넣기 가능
- **DESIGN.md 지원**: 디자인 시스템을 마크다운으로 내보내기/가져오기
- **음성 입력**: 캔버스에 말로 디자인 지시 가능

### 동작 모드
| 모드 | 모델 | 용도 |
|------|------|------|
| Standard | Gemini 2.5 Flash | 빠른 레이아웃 생성, 테마 편집 |
| Experimental | Gemini 2.5 Pro | 고품질 결과, 이미지 입력 지원 |

---

## 2. stitch-mcp란?

Stitch API를 MCP(Model Context Protocol) 서버로 감싸서, Claude Code 같은 AI 에이전트가 Stitch를 도구로 호출할 수 있게 해주는 CLI.

> 주의: David East 개인 프로젝트이며 Google 공식 도구가 아님 (Apache 2.0 라이선스)

### 제공하는 MCP 도구

| 도구명 | 설명 |
|--------|------|
| `build_site` | 프로젝트 화면들을 라우트로 매핑하여 사이트 빌드, 각 페이지의 HTML 반환 |
| `get_screen_code` | 특정 화면의 HTML 코드 다운로드 |
| `get_screen_image` | 특정 화면의 스크린샷을 base64로 다운로드 |

---

## 3. 사전 준비

### 3-1. Google Cloud 프로젝트 준비
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성 또는 기존 프로젝트 선택
3. 결제 활성화 확인
4. Stitch API 활성화:
   ```bash
   gcloud beta services mcp enable stitch.googleapis.com --project=<PROJECT_ID>
   ```

### 3-2. gcloud CLI 설치 (없는 경우)
```bash
# macOS
brew install google-cloud-sdk

# 또는 공식 설치 스크립트
curl https://sdk.cloud.google.com | bash
```

### 3-3. Node.js 확인
```bash
node --version  # v18+ 필요
```

---

## 4. stitch-mcp 설치 및 초기화

### 방법 A: 자동 설정 (권장)

```bash
npx @_davideast/stitch-mcp init
```

이 명령어가 자동으로 처리하는 것:
- gcloud 설치 여부 확인
- OAuth 인증 (브라우저 열림)
- 자격증명 설정
- Google Cloud 프로젝트 설정

### 방법 B: API 키 사용 (OAuth 스킵)

```bash
export STITCH_API_KEY="your-api-key"
```

### 방법 C: 기존 gcloud 사용

```bash
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
```

### 설정 확인

```bash
npx @_davideast/stitch-mcp doctor
# 문제가 있으면 --verbose 추가
npx @_davideast/stitch-mcp doctor --verbose
```

---

## 5. Claude Code에 MCP 서버 연결

### 5-1. 프로젝트 레벨 설정 (권장)

프로젝트 루트에 `.mcp.json` 파일 생성:

```json
{
  "mcpServers": {
    "stitch": {
      "command": "npx",
      "args": ["@_davideast/stitch-mcp", "proxy"]
    }
  }
}
```

### 5-2. 시스템 gcloud 사용 시

```json
{
  "mcpServers": {
    "stitch": {
      "command": "npx",
      "args": ["@_davideast/stitch-mcp", "proxy"],
      "env": {
        "STITCH_USE_SYSTEM_GCLOUD": "1"
      }
    }
  }
}
```

### 5-3. 연결 확인

Claude Code 재시작 후, MCP 서버가 연결되면 Stitch 도구들이 사용 가능해진다.

---

## 6. 기본 사용법

### 6-1. Stitch에서 디자인 만들기

1. https://stitch.withgoogle.com 접속
2. 프롬프트로 UI 디자인 생성 (예: "패션 앱 온보딩 화면, 따뜻한 톤, Marsala 액센트 컬러")
3. 마음에 드는 디자인 선택
4. 프로젝트 ID와 화면 ID 확인

### 6-2. CLI로 디자인 탐색

```bash
# 모든 프로젝트 보기
npx @_davideast/stitch-mcp view --projects

# 특정 프로젝트의 화면들 보기
npx @_davideast/stitch-mcp screens -p <project-id>

# 화면 상세 정보
npx @_davideast/stitch-mcp view --project <project-id> --screen <screen-id>
```

### 6-3. 로컬 미리보기

```bash
# Vite 개발 서버로 화면 미리보기
npx @_davideast/stitch-mcp serve -p <project-id>
```

### 6-4. 사이트 빌드

```bash
# Astro 프로젝트로 변환
npx @_davideast/stitch-mcp site -p <project-id>
```

### 6-5. MCP 도구 직접 호출

```bash
# 사용 가능한 도구 목록
npx @_davideast/stitch-mcp tool

# 도구 스키마 확인
npx @_davideast/stitch-mcp tool get_screen_code -s

# 화면 코드 가져오기
npx @_davideast/stitch-mcp tool get_screen_code -d '{
  "projectId": "123456",
  "query": "온보딩"
}'

# 사이트 빌드
npx @_davideast/stitch-mcp tool build_site -d '{
  "projectId": "123456",
  "routes": [
    { "screenId": "abc", "route": "/" },
    { "screenId": "def", "route": "/about" }
  ]
}'
```

---

## 7. ColorFit 디자인 리팩토링 워크플로우

### Step 1: Stitch에서 ColorFit 디자인 시스템 적용

Stitch에 ColorFit의 디자인 시스템을 전달하여 화면 생성:

```
프롬프트 예시:
"패션 퍼스널컬러 앱. 
배경: #F8F6F3 (Warm Off-White)
액센트: #964F4C (Marsala)
헤드라인 서체: Nanum Myeongjo
본문 서체: Pretendard Variable
따뜻하고 고급스러운 톤.
온보딩 → 코디 피드 → 상품 추천 상세 화면 생성해줘"
```

### Step 2: MCP로 디자인 코드 추출

Claude Code에서 Stitch MCP 도구를 호출하여 생성된 디자인의 HTML/CSS를 가져온다.

### Step 3: 기존 컴포넌트에 적용

추출한 디자인 코드를 참고하여 기존 Next.js 컴포넌트를 리팩토링한다.

### Step 4: DESIGN.md 동기화

Stitch의 DESIGN.md 내보내기 기능으로 디자인 시스템을 문서화하고, 프로젝트 DESIGN.md와 비교/병합한다.

---

## 8. 환경 변수 레퍼런스

| 변수 | 설명 |
|------|------|
| `STITCH_API_KEY` | API 키 (OAuth 대신 사용) |
| `STITCH_ACCESS_TOKEN` | 기존 액세스 토큰 직접 사용 |
| `STITCH_USE_SYSTEM_GCLOUD` | `1`이면 시스템 gcloud 사용 |
| `STITCH_PROJECT_ID` | Google Cloud 프로젝트 ID 오버라이드 |
| `GOOGLE_CLOUD_PROJECT` | 대체 프로젝트 ID 변수 |
| `STITCH_HOST` | 커스텀 Stitch API 엔드포인트 |

---

## 9. 문제 해결

### 인증 오류
```bash
# 자격증명 초기화
npx @_davideast/stitch-mcp logout --force --clear-config

# 다시 설정
npx @_davideast/stitch-mcp init
```

### 권한 오류
- Google Cloud 프로젝트에서 소유자/편집자 역할 확인
- 결제 활성화 확인
- Stitch API 활성화 확인

### 인증 URL이 안 보일 때
- `https://accounts.google.com`으로 시작하는 URL이 터미널에 출력됨 (5초 타임아웃)
- 프록시 디버그: `--debug` 플래그 추가 후 `/tmp/stitch-proxy-debug.log` 확인

### WSL/SSH/Docker 환경
- 브라우저 자동 열기 안 됨 → 터미널에 출력된 OAuth URL을 수동으로 브라우저에서 열기

---

## 10. 참고 링크

- [Stitch 공식 사이트](https://stitch.withgoogle.com)
- [stitch-mcp GitHub](https://github.com/davideast/stitch-mcp)
- [Google Stitch 블로그 소개](https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-ai-ui-design/)
- [Google Developers Blog - Stitch](https://developers.googleblog.com/stitch-a-new-way-to-design-uis/)
- [Design-to-Code with Antigravity and Stitch MCP (Codelab)](https://codelabs.developers.google.com/design-to-code-with-antigravity-stitch)
