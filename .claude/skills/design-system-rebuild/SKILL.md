---
name: design-system-rebuild
description: 기존 화면의 기능을 보존하면서 디자인 시스템 스펙 기반으로 화면을 새로 구성합니다. /design-rebuild 로 실행하세요.
allowed-tools: Read Glob Grep Bash Edit Write
paths:
  - "design-system/**"
  - "src/**"
  - "app/**"
  - "components/**"
  - "styles/**"
  - "lib/**"
---

# Design System Rebuild

기존 AI 생성 UI나 프로토타입을 디자인 시스템 스펙 기반으로 **처음부터 다시 구성**합니다.
Refactor(토큰 교체)와 다릅니다 — 레이아웃, 타이포그래피 위계, 색상 구성, 컴포넌트 구조를 모두 재설계합니다.

## Refactor vs Rebuild 차이

| | Refactor | **Rebuild** |
|---|---|---|
| 목표 | 기존 코드에 토큰 연결 | **화면 전체를 스펙 기반으로 재구성** |
| 레이아웃 | 건드리지 않음 | **스펙에 맞게 재설계** |
| 서체 | 변수명만 교체 | **위계 자체를 재구성** |
| 여백 | 같은 값만 교체 | **리듬과 호흡을 재설계** |
| 임팩트 | 작음 (안전) | **크게 달라 보임 (변환)** |

## 실행 절차

### Phase 1: 스펙 로드

1. `design-system/system_spec.md` — 디자인 원칙, 브랜드 키워드, 안티 키워드
2. `design-system/token_schema.json` — 토큰 체계 (color, typography, spacing, motion)
3. `design-system/components/component_specs.json` — 컴포넌트별 상세 스펙
4. `design-system/component_inventory.json` — 컴포넌트 패밀리

특히 아래 정보를 반드시 추출합니다:
- **color palette**: primary, accent, surface, semantic states (이 색상을 실제로 사용)
- **typography**: heading/body/mono 서체, type scale, line-height (이 서체와 크기를 실제로 적용)
- **design principles**: 예를 들어 "calm" → 절제된 모션, "bold" → 강한 대비
- **component anatomy**: 각 컴포넌트의 필수 파트와 상태

### Phase 2: 기존 화면 분석

대상 파일을 읽고 **기능 목록**만 추출합니다 (시각적 구현은 버림):

```
기능 추출 예시:
- 이 화면은 "리그 순위표"를 보여줌
- 데이터: 순위, 팀명, 경기수, 승/무/패, 골득실, 승점, 최근 5경기
- 인터랙션: 컬럼 정렬, 시즌 필터
- 상태: 로딩, 빈 상태, 에러
- 네비게이션: 상단 탭, 팀 클릭 시 상세 이동
```

기존 코드의 시각적 결정(색상, 여백, 서체 크기, 레이아웃)은 참고하지 않습니다.
오직 **"이 화면이 무엇을 하는가"**만 파악합니다.

### Phase 3: 디자인 시스템 기반 재구성

추출한 기능을 디자인 시스템 스펙으로 다시 만듭니다.

#### 3-1. 색상 적용

system_spec.md의 Color Reference에서 가져온 palette를 실제로 사용합니다:
- **배경**: canvas/surface/surface_tint 토큰 — dark mode first면 어두운 surface
- **텍스트**: ink/ink_muted 토큰 — 위계에 따라 primary/secondary 구분
- **강조**: primary/accent 컬러 — CTA, 활성 상태, 하이라이트에만 사용
- **상태**: success/warning/danger/info — semantic state에만 사용
- **보더**: border/border_subtle — 구조를 드러내되 과하지 않게

절대로 Tailwind 기본 색상(blue-500, gray-100 등)을 쓰지 않습니다.
CSS 변수 또는 프로젝트의 토큰 시스템으로 적용합니다.

#### 3-2. 타이포그래피 위계

system_spec.md의 Typography System에서:
- **heading 서체**: 페이지 제목, 섹션 헤더에 적용
- **body 서체**: 본문, UI 라벨에 적용
- **mono 서체**: 데이터, 코드, 숫자에 적용
- **type scale**: 각 위치의 font-size를 scale에서 선택
- **line-height**: preset에 따라 적용

위계 구성 원칙:
```
페이지 제목: heading font, 2xl-3xl, weight 800
섹션 제목:   heading font, xl, weight 700
카드 제목:   body font, lg, weight 600
본문:        body font, md, weight 400
캡션/라벨:   body font, sm, weight 500, uppercase + letter-spacing (optional)
데이터 숫자: mono 또는 tabular figures, lg-2xl, weight 700-800
```

#### 3-3. 여백과 리듬

spacing scale을 활용해 시각적 리듬을 만듭니다:
```
페이지 패딩:    spacing-24 ~ spacing-32
섹션 간 간격:   spacing-24 ~ spacing-32
카드 내부 패딩:  spacing-16 ~ spacing-24
요소 간 간격:   spacing-8 ~ spacing-16
인라인 간격:    spacing-4 ~ spacing-8
```

리듬 원칙:
- 큰 단위는 작은 단위의 배수 (8→16→32)
- 관련 요소는 가깝게, 다른 그룹은 멀게 (근접성 원칙)
- 빈 공간을 두려워하지 않기 — 여백이 위계를 만듬

#### 3-4. 레이아웃 구성

화면 유형별 레이아웃 패턴:
```
대시보드:    상단 히어로/요약 → 통계 카드 그리드 → 데이터 테이블
목록/피드:   상단 필터/검색 → 반복 카드/행 → 페이지네이션
상세 페이지:  헤더(제목+메타) → 메인 콘텐츠 → 사이드 정보 → 관련 항목
설정:       좌측 메뉴 → 우측 폼 섹션
```

#### 3-5. 컴포넌트 구성

component_specs.json의 각 컴포넌트를:
- anatomy에 정의된 파트를 모두 포함
- states에 정의된 상태를 모두 처리
- accessibility에 정의된 속성을 모두 적용
- 브랜드 적용 규칙을 반영

#### 3-6. 인터랙션과 모션

```
hover:      opacity 변화 또는 background shift (brand keyword에 따라)
transition: 120-200ms ease-out (calm이면 느리게, energetic이면 빠르게)
loading:    skeleton 또는 spinner (컴포넌트 스펙에 따라)
focus:      focus-ring 토큰 (접근성 필수)
```

### Phase 4: 코드 작성

재구성한 화면을 실제 코드로 작성합니다.

작성 규칙:
- 프로젝트의 기존 프레임워크/라이브러리를 사용 (React, Vue, Svelte 등)
- CSS 변수 또는 프로젝트의 토큰 시스템을 통해 스펙 값 적용
- 컴포넌트 분리: 재사용 가능한 단위로 분리 (하나의 거대한 파일 금지)
- TypeScript를 사용 중이면 props 타입 정의
- 접근성 속성 반드시 포함 (role, aria, label, scope 등)

### Phase 5: 검증 및 리포트

```
## Rebuild 결과

### 재구성된 화면
- [화면명]: [주요 변경 사항]

### 적용된 디자인 시스템 요소
- Color: [사용한 palette roles]
- Typography: [heading/body/mono 서체 + scale]
- Components: [스펙 기반으로 구성한 컴포넌트 목록]
- Accessibility: [적용한 접근성 속성]

### 보존된 기능
- [기존 기능이 그대로 동작하는지 확인 목록]

### 수동 확인 필요
- [실제 데이터로 테스트 필요한 항목]
- [반응형 확인 필요한 breakpoint]
```

## 금지 사항

- 기존 기능을 제거하거나 빠뜨리지 않음 — 모든 데이터와 인터랙션을 보존
- 라우팅이나 API 호출 로직을 변경하지 않음
- 스펙에 없는 장식적 요소를 추가하지 않음 (그라데이션, 글로우 등 — 스펙에 있으면 OK)
- 안티 키워드에 해당하는 시각적 패턴을 사용하지 않음
- 접근성을 빠뜨리지 않음 — rebuild는 접근성이 더 좋아져야 함
