---
name: design-system-refactor
description: AI가 만든 UI 코드를 디자인 시스템 스펙에 맞게 자동 리팩토링합니다. /design-refactor 로 실행하세요.
allowed-tools: Read Glob Grep Bash Edit Write
paths:
  - "design-system/**"
  - "src/**"
  - "app/**"
  - "components/**"
  - "styles/**"
  - "lib/**"
---

# Design System Refactor

AI가 생성한 UI 코드나 급하게 만든 프로토타입을, 디자인 시스템 스펙 기준으로 체계적으로 리팩토링합니다.

## 실행 절차

### Phase 1: 스펙 로드

1. `design-system/component_specs.json` 또는 `design-system/components/component_specs.json`을 읽습니다.
   - 없으면 `design-system/component_inventory.json`을 읽습니다.
2. `design-system/token_schema.json`을 읽습니다.
3. `design-system/system_spec.md`를 읽어 브랜드 키워드, 안티 키워드, 디자인 원칙을 파악합니다.

이 세 파일이 리팩토링의 기준입니다. 파일이 없으면 어떤 파일이 빠졌는지 알리고 멈춥니다.

### Phase 2: 코드베이스 스캔

1. `src/`, `app/`, `components/` 에서 UI 컴포넌트 파일을 찾습니다.
   - React: `*.tsx`, `*.jsx`
   - Vue: `*.vue`
   - Svelte: `*.svelte`
2. 각 파일에서 아래 문제를 탐지합니다:

**토큰 위반**
- 하드코딩된 색상값 (`#fff`, `rgb(...)`, `bg-blue-500` 등)
- 하드코딩된 spacing (`margin: 12px`, `p-3` 등 — 토큰 scale에 없는 값)
- 하드코딩된 font-size, border-radius
- 인라인 스타일에 직접 값 사용

**컴포넌트 구조 위반**
- 스펙에 정의된 상태(states)가 빠져 있는 컴포넌트
- anatomy에 정의된 필수 파트가 없는 컴포넌트
- variant 없이 조건부로 스타일 하드코딩

**접근성 위반**
- button에 role/aria 속성 누락
- input에 label 연결 누락
- modal에 focus trap 누락
- 이미지에 alt 누락
- 터치 영역 44px 미만

**브랜드 위반**
- 안티 키워드에 해당하는 시각적 패턴 (예: "noisy" 안티키워드인데 과한 그림자/애니메이션)
- 브랜드 키워드와 충돌하는 인터랙션 (예: "calm"인데 bounce 애니메이션)

### Phase 3: 리팩토링 실행

탐지된 문제를 **우선순위 순서**로 수정합니다:

1. **접근성 위반** (가장 먼저 — 법적/윤리적 요구사항)
2. **토큰 하드코딩** (시스템의 기반)
3. **컴포넌트 구조** (누락된 상태/파트 추가)
4. **브랜드 정합성** (시각적 미세 조정)

각 수정은:
- 한 파일씩 순차적으로 처리
- 수정 전후를 설명
- 기존 기능을 깨뜨리지 않는 범위에서만 변경
- 확신이 없는 변경은 TODO 주석으로 남김

### Phase 4: 리포트

리팩토링 완료 후 요약을 출력합니다:

```
## 리팩토링 결과

### 수정 완료
- [파일명]: 토큰 위반 3건, 접근성 위반 1건 수정
- [파일명]: 컴포넌트 구조 보완 (disabled 상태 추가)

### 수동 확인 필요
- [파일명]: 색상 팔레트 적용 확인 필요
- [파일명]: 반응형 레이아웃 테스트 필요

### 스펙 미커버
- [컴포넌트명]: 스펙에 없는 컴포넌트 — component_specs에 추가 필요
```

## 수정 규칙

### 토큰 교체 예시

```tsx
// Before (하드코딩)
<div className="bg-white text-gray-900 p-4 rounded-lg shadow-md">

// After (토큰 기반)
<div className="bg-surface-default text-text-primary p-spacing-16 rounded-radius-md shadow-elevation-raised">
```

### 상태 추가 예시

```tsx
// Before (상태 누락)
function Button({ children }) {
  return <button>{children}</button>
}

// After (스펙 기반 상태)
function Button({ children, variant = "primary", size = "md", disabled, loading }) {
  return (
    <button
      disabled={disabled || loading}
      aria-busy={loading}
      aria-disabled={disabled}
      className={buttonStyles({ variant, size, disabled, loading })}
    >
      {loading ? <Spinner /> : children}
    </button>
  )
}
```

### 접근성 추가 예시

```tsx
// Before
<input placeholder="이름" />

// After
<label htmlFor="name">이름</label>
<input id="name" aria-required="true" />
```

## 레이아웃 보호 규칙 (최우선)

리팩토링은 **기존 화면의 레이아웃과 텍스트 흐름을 절대 깨뜨리지 않는 범위**에서만 진행합니다.

### 절대 건드리지 않는 것

- `display`, `flex-direction`, `grid-template-columns`, `position`, `float` 등 **레이아웃 속성**
- `width`, `height`, `max-width`, `min-height` 등 **박스 크기**
- `overflow`, `text-overflow`, `white-space`, `word-break` 등 **텍스트 줄바꿈 제어**
- `line-clamp`, `-webkit-line-clamp` 등 **말줄임 처리**
- `gap`, `margin`, `padding` 중 **레이아웃 간격에 영향을 주는 값** (단, 토큰으로 1:1 교체는 허용)

### 안전한 교체만 허용

```
허용: color: #334155 → color: var(--text-primary)
허용: background: #fff → background: var(--surface-default)
허용: border: 1px solid #e5e7eb → border: 1px solid var(--border-default)
허용: border-radius: 8px → border-radius: var(--radius-md)
허용: font-weight: 600 → font-weight: var(--font-weight-semibold)
허용: box-shadow: 0 1px 3px ... → box-shadow: var(--elevation-raised)

금지: padding: 12px 16px → padding: 16px 24px (크기가 바뀌면 레이아웃 깨짐)
금지: display: flex → display: grid (레이아웃 변경)
금지: width: 100% → width: auto (크기 변경)
금지: font-size: 14px → font-size: 16px (줄바꿈 위치가 바뀜)
금지: line-height: 1.4 → line-height: 1.75 (텍스트 높이가 바뀜)
```

### font-size / line-height: 원칙적으로 바꾸지 않음

**기존 코드의 font-size는 이미 화면에 맞게 조정된 값입니다.**
토큰 스케일(xs=12, sm=13, md=15, lg=21...)에 기계적으로 맞추려고
기존 14px → 15px, 16px → 21px 같은 변경을 하면 안 됩니다.

이런 일이 실제로 발생합니다:
- 카드 제목 16px → 18px(lg)로 올림 → 한 줄이 두 줄로 넘침 → 카드 높이 깨짐
- 배지 텍스트 11px → 12px(xs)로 올림 → 배지 폭 증가 → 줄 끝에서 밀려남
- 리스트 아이템 13px → 14px → padding 그대로인데 글자가 커져서 뭉쳐 보임
- 가격 텍스트 15px → 16px → 옆 요소와 정렬 어긋남

**리팩토링에서 font-size를 바꾸는 것은 디자인 변경이지 리팩토링이 아닙니다.**

허용되는 경우:
```
font-size: 14px → var(--text-sm)   (단, --text-sm이 정확히 14px일 때만)
font-size: 16px → var(--text-md)   (단, --text-md가 정확히 16px일 때만)
```

금지되는 경우:
```
font-size: 14px → var(--text-md)   (md가 15px이면 × — 1px 차이라도 안 됨)
font-size: 16px → var(--text-lg)   (lg가 21px이면 × — "스케일에 맞추려고" 키우면 안 됨)
font-size: 11px → var(--text-xs)   (xs가 12px이면 × — 배지/뱃지 크기가 바뀜)
```

토큰 스케일에 정확히 맞는 값이 없으면:
```
// 토큰 스케일에 14px가 없음 — 원본 유지
font-size: 14px; /* TODO: token scale에 없는 값, 커스텀 토큰 추가 검토 */
```

line-height도 동일하게 적용합니다.
**토큰이 코드에 맞춰야지, 코드가 토큰에 맞추면 안 됩니다.**

### spacing 교체 시 주의

- `padding`/`margin` 교체는 spacing scale에서 **정확히 같은 값**이 있을 때만 1:1 교체
- spacing scale에 없는 값(14px, 18px, 22px 등)은 교체하지 않고 TODO로 남김
- 절대로 "가장 가까운 값"으로 반올림하지 않음 — 1px 차이로도 레이아웃이 깨질 수 있음
- 특히 **보더나 구분선이 없는 반복 요소**(리스트, 카드 나열)는 spacing이 유일한 시각적 구분 — 더 신중하게
- 배지/뱃지의 padding을 키우면 배지 자체 크기가 바뀌고 주변 정렬에 영향 — 원본 유지

### 리팩토링 후 자가 검증

매 파일 수정 후 아래를 확인합니다:

1. **줄바꿈 불변**: 텍스트의 줄바꿈 위치가 바뀌지 않았는가?
2. **박스 크기 불변**: 수정 전후로 요소의 width/height가 동일한가?
3. **간격 불변**: 요소 사이 간격이 달라지지 않았는가?
4. **넘침 없음**: 텍스트나 요소가 컨테이너를 벗어나지 않는가?
5. **뭉침 없음**: 보더 없는 목록에서 아이템 간 시각적 구분이 유지되는가?
6. **정렬 유지**: 인접 요소 간 baseline/vertical 정렬이 바뀌지 않았는가?

확신이 없으면 **수정하지 않고** 리포트에 "수동 확인 필요" 항목으로 남깁니다.

## 금지 사항

- 기존 기능이나 라우팅을 변경하지 않음
- 스펙에 없는 새 컴포넌트를 발명하지 않음
- 전체 파일을 리라이트하지 않음 — 문제가 있는 부분만 수정
- 테마/다크모드 지원이 있으면 깨뜨리지 않음
- 동작하는 로직을 건드리지 않음 — 시각적/구조적 레이어만 수정
- **레이아웃 속성을 변경하지 않음** — 색상/보더/그림자/radius만 토큰으로 교체
- **font-size/line-height를 함부로 바꾸지 않음** — 줄바꿈이 바뀔 수 있음
- **spacing을 반올림하지 않음** — 정확히 같은 값의 토큰이 없으면 교체하지 않음
