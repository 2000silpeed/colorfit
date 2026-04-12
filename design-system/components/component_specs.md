# ColorFit Component Specs

총 61개 컴포넌트 | 패밀리: button, data-display, feedback, input, navigation, overlay

## 브랜드 적용 규칙

- **hover**: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- **motion**: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- **color**: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음
- **density**: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- **feedback**: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

---

## button / primary-button

**역할**: 주요 행동을 유도하는 CTA 버튼

**탐지 출처**: baseline

### 구조 (Anatomy)

- container
- label
- leading-icon(optional)
- trailing-icon(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `disabled` | 비활성 (상호작용 불가) |
| `loading` | 로딩 중 (스피너 표시) |

### 토큰 바인딩

```
surface: primary-button.surface.{state}
text: primary-button.text.{state}
border: primary-button.border.{state}
radius: radius.md
padding: spacing.12 spacing.24
font: typography.text.md.semibold
```

### 접근성

- role="button"
- aria-disabled="true" when disabled
- aria-busy="true" when loading
- 최소 44x44 터치 영역
- 텍스트 대비 4.5:1 이상

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: These components can toggle between the AI variant and the default variant depending on the user’s interaction. If the user manually overrides the ...
- **Primer**: I get so much joy from writing HTML and CSS, and design systems are one level up - systematically making UIs accessible and consistent. I love conc...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- size prop: sm / md / lg (터치 영역은 항상 최소 44px 보장)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## button / secondary-button

**역할**: 보조 행동 버튼

**탐지 출처**: baseline

### 구조 (Anatomy)

- container
- label
- leading-icon(optional)
- trailing-icon(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `disabled` | 비활성 (상호작용 불가) |
| `loading` | 로딩 중 (스피너 표시) |

### 토큰 바인딩

```
surface: secondary-button.surface.{state}
text: secondary-button.text.{state}
border: secondary-button.border.{state}
radius: radius.md
padding: spacing.12 spacing.24
font: typography.text.md.semibold
```

### 접근성

- role="button"
- aria-disabled="true" when disabled
- aria-busy="true" when loading
- 최소 44x44 터치 영역
- 텍스트 대비 4.5:1 이상

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: These components can toggle between the AI variant and the default variant depending on the user’s interaction. If the user manually overrides the ...
- **Primer**: I get so much joy from writing HTML and CSS, and design systems are one level up - systematically making UIs accessible and consistent. I love conc...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- size prop: sm / md / lg (터치 영역은 항상 최소 44px 보장)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## button / ghost-button

**역할**: 최소한의 시각적 무게를 가진 버튼

**탐지 출처**: baseline

### 구조 (Anatomy)

- container
- label
- leading-icon(optional)
- trailing-icon(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `disabled` | 비활성 (상호작용 불가) |
| `loading` | 로딩 중 (스피너 표시) |

### 토큰 바인딩

```
surface: ghost-button.surface.{state}
text: ghost-button.text.{state}
border: ghost-button.border.{state}
radius: radius.md
padding: spacing.12 spacing.24
font: typography.text.md.semibold
```

### 접근성

- role="button"
- aria-disabled="true" when disabled
- aria-busy="true" when loading
- 최소 44x44 터치 영역
- 텍스트 대비 4.5:1 이상

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: These components can toggle between the AI variant and the default variant depending on the user’s interaction. If the user manually overrides the ...
- **Primer**: I get so much joy from writing HTML and CSS, and design systems are one level up - systematically making UIs accessible and consistent. I love conc...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- size prop: sm / md / lg (터치 영역은 항상 최소 44px 보장)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## button / icon-button

**역할**: 아이콘만 있는 액션 버튼

**탐지 출처**: baseline

### 구조 (Anatomy)

- container
- label
- leading-icon(optional)
- trailing-icon(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `disabled` | 비활성 (상호작용 불가) |
| `loading` | 로딩 중 (스피너 표시) |

### 토큰 바인딩

```
surface: icon-button.surface.{state}
text: icon-button.text.{state}
border: icon-button.border.{state}
radius: radius.md
padding: spacing.12 spacing.24
font: typography.text.md.semibold
```

### 접근성

- role="button"
- aria-disabled="true" when disabled
- aria-busy="true" when loading
- 최소 44x44 터치 영역
- 텍스트 대비 4.5:1 이상

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: These components can toggle between the AI variant and the default variant depending on the user’s interaction. If the user manually overrides the ...
- **Primer**: I get so much joy from writing HTML and CSS, and design systems are one level up - systematically making UIs accessible and consistent. I love conc...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- size prop: sm / md / lg (터치 영역은 항상 최소 44px 보장)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## button / link-button

**역할**: 텍스트 링크 스타일 버튼

**탐지 출처**: baseline

### 구조 (Anatomy)

- container
- label
- leading-icon(optional)
- trailing-icon(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `disabled` | 비활성 (상호작용 불가) |
| `loading` | 로딩 중 (스피너 표시) |

### 토큰 바인딩

```
surface: link-button.surface.{state}
text: link-button.text.{state}
border: link-button.border.{state}
radius: radius.md
padding: spacing.12 spacing.24
font: typography.text.md.semibold
```

### 접근성

- role="button"
- aria-disabled="true" when disabled
- aria-busy="true" when loading
- 최소 44x44 터치 영역
- 텍스트 대비 4.5:1 이상

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: These components can toggle between the AI variant and the default variant depending on the user’s interaction. If the user manually overrides the ...
- **Primer**: I get so much joy from writing HTML and CSS, and design systems are one level up - systematically making UIs accessible and consistent. I love conc...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- size prop: sm / md / lg (터치 영역은 항상 최소 44px 보장)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / data-table

**역할**: 정렬·필터 가능한 데이터 테이블

**탐지 출처**: data tables

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: Data table Modal
- **Primer**: DataTable DataTable is a 2-dimensional data structure where each row is an item, and each column is a data point about the item.

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / column-header

**역할**: 테이블 컬럼 헤더 (정렬 토글)

**탐지 출처**: data tables

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / row-actions

**역할**: 행별 액션 메뉴

**탐지 출처**: data tables

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## navigation / pagination

**역할**: 페이지 이동 컨트롤

**탐지 출처**: data tables

### 구조 (Anatomy)

- container
- nav-item
- icon(optional)
- label
- indicator(active)
- badge(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `collapsed` | 접힌 상태 |

### 토큰 바인딩

```
surface: surface.nav.{state}
text: text.nav.{state}
indicator: color.accent.500
padding: spacing.8 spacing.16
```

### 접근성

- nav landmark (role="navigation")
- aria-current="page" for active item
- 키보드 화살표 탐색 지원

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration

### 레퍼런스 근거

- **Carbon Design System**: Library menu navigation There are two kinds of symbols — library symbols and document symbols. Library symbols are available in any Sketch document...
- **Primer**: Octicon nav items navigation 12 px

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- active 상태는 URL/라우터와 자동 동기화
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / filter-chip

**역할**: 활성 필터를 칩으로 표시/해제

**탐지 출처**: data tables

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / text-field

**역할**: 단일 줄 텍스트 입력

**탐지 출처**: forms

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / textarea

**역할**: 여러 줄 텍스트 입력

**탐지 출처**: forms

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / select

**역할**: 드롭다운 선택

**탐지 출처**: forms

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Select Data table
- **Primer**: Primer color design tokens are made available within data-attribute selectors on the body tag or other high level dom element. There are three dist...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / checkbox

**역할**: 체크박스

**탐지 출처**: forms

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Checkbox Form
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / radio-group

**역할**: 라디오 버튼 그룹

**탐지 출처**: forms

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / form-section

**역할**: 폼 섹션 그룹핑과 레이블

**탐지 출처**: forms

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## button / form-actions

**역할**: 폼 하단 제출/취소 버튼 영역

**탐지 출처**: forms

### 구조 (Anatomy)

- container
- label
- leading-icon(optional)
- trailing-icon(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `disabled` | 비활성 (상호작용 불가) |
| `loading` | 로딩 중 (스피너 표시) |

### 토큰 바인딩

```
surface: form-actions.surface.{state}
text: form-actions.text.{state}
border: form-actions.border.{state}
radius: radius.md
padding: spacing.12 spacing.24
font: typography.text.md.semibold
```

### 접근성

- role="button"
- aria-disabled="true" when disabled
- aria-busy="true" when loading
- 최소 44x44 터치 영역
- 텍스트 대비 4.5:1 이상

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: These components can toggle between the AI variant and the default variant depending on the user’s interaction. If the user manually overrides the ...
- **Primer**: I get so much joy from writing HTML and CSS, and design systems are one level up - systematically making UIs accessible and consistent. I love conc...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- size prop: sm / md / lg (터치 영역은 항상 최소 44px 보장)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / tag

**역할**: 분류/라벨 태그

**탐지 출처**: tags and labels

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: Tag Date picker
- **Primer**: Primer color design tokens are made available within data-attribute selectors on the body tag or other high level dom element. There are three dist...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## feedback / status-badge

**역할**: 상태를 색상으로 표시하는 뱃지

**탐지 출처**: tags and labels

### 구조 (Anatomy)

- container
- icon
- message
- action(optional)
- close-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `info` | 정보 알림 |
| `success` | 성공 알림 |
| `warning` | 경고 알림 |
| `danger` | 에러/위험 알림 |

### 토큰 바인딩

```
surface: feedback.info.surface
text: feedback.info.text
icon: feedback.info.icon
border: feedback.info.border
radius: radius.sm
```

### 접근성

- role="alert" for urgent messages
- role="status" for non-urgent
- aria-live="polite" or "assertive"
- 닫기 버튼에 aria-label 필수

### 브랜드 적용

- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: We welcome all feedback, designs, or ideas in order to produce the best possible experience for our users. If you're interested in contributing, ch...
- **Primer**: Messaging components are used to provide important and relevant information to the user, including feedback, contextual information, product update...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- auto-dismiss 시간은 내용 길이에 비례 (기본 5초)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / chip

**역할**: 선택/해제 가능한 칩

**탐지 출처**: tags and labels

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## navigation / app-shell

**역할**: 전체 앱 레이아웃과 네비게이션 컨테이너

**탐지 출처**: workspace navigation

### 구조 (Anatomy)

- container
- nav-item
- icon(optional)
- label
- indicator(active)
- badge(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `collapsed` | 접힌 상태 |

### 토큰 바인딩

```
surface: surface.nav.{state}
text: text.nav.{state}
indicator: color.accent.500
padding: spacing.8 spacing.16
```

### 접근성

- nav landmark (role="navigation")
- aria-current="page" for active item
- 키보드 화살표 탐색 지원

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration

### 레퍼런스 근거

- **Carbon Design System**: Library menu navigation There are two kinds of symbols — library symbols and document symbols. Library symbols are available in any Sketch document...
- **Primer**: Octicon nav items navigation 12 px

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- active 상태는 URL/라우터와 자동 동기화
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## navigation / sidebar-nav

**역할**: 주요 섹션 간 이동을 위한 사이드 네비게이션

**탐지 출처**: workspace navigation

### 구조 (Anatomy)

- container
- nav-item
- icon(optional)
- label
- indicator(active)
- badge(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `collapsed` | 접힌 상태 |

### 토큰 바인딩

```
surface: surface.nav.{state}
text: text.nav.{state}
indicator: color.accent.500
padding: spacing.8 spacing.16
```

### 접근성

- nav landmark (role="navigation")
- aria-current="page" for active item
- 키보드 화살표 탐색 지원

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration

### 레퍼런스 근거

- **Carbon Design System**: Total panel width (“sidebar nav”) + Left outside margin + Right outside margin = Total margins Artboard width - Total margins = Total width
- **Primer**: Octicon nav items navigation 12 px

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- active 상태는 URL/라우터와 자동 동기화
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## navigation / topbar

**역할**: 앱 상단 바 (로고, 검색, 사용자 메뉴)

**탐지 출처**: workspace navigation

### 구조 (Anatomy)

- container
- nav-item
- icon(optional)
- label
- indicator(active)
- badge(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `collapsed` | 접힌 상태 |

### 토큰 바인딩

```
surface: surface.nav.{state}
text: text.nav.{state}
indicator: color.accent.500
padding: spacing.8 spacing.16
```

### 접근성

- nav landmark (role="navigation")
- aria-current="page" for active item
- 키보드 화살표 탐색 지원

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration

### 레퍼런스 근거

- **Carbon Design System**: Library menu navigation There are two kinds of symbols — library symbols and document symbols. Library symbols are available in any Sketch document...
- **Primer**: Octicon nav items navigation 12 px

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- active 상태는 URL/라우터와 자동 동기화
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## navigation / breadcrumb

**역할**: 현재 위치를 계층적으로 표시

**탐지 출처**: workspace navigation

### 구조 (Anatomy)

- container
- nav-item
- icon(optional)
- label
- indicator(active)
- badge(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `collapsed` | 접힌 상태 |

### 토큰 바인딩

```
surface: surface.nav.{state}
text: text.nav.{state}
indicator: color.accent.500
padding: spacing.8 spacing.16
```

### 접근성

- nav landmark (role="navigation")
- aria-current="page" for active item
- 키보드 화살표 탐색 지원

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration

### 레퍼런스 근거

- **Carbon Design System**: Library menu navigation There are two kinds of symbols — library symbols and document symbols. Library symbols are available in any Sketch document...
- **Primer**: Octicon nav items navigation 12 px

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- active 상태는 URL/라우터와 자동 동기화
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## navigation / tab-bar

**역할**: 섹션 내 하위 탭 전환

**탐지 출처**: workspace navigation

### 구조 (Anatomy)

- container
- nav-item
- icon(optional)
- label
- indicator(active)
- badge(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `collapsed` | 접힌 상태 |

### 토큰 바인딩

```
surface: surface.nav.{state}
text: text.nav.{state}
indicator: color.accent.500
padding: spacing.8 spacing.16
```

### 접근성

- nav landmark (role="navigation")
- aria-current="page" for active item
- 키보드 화살표 탐색 지원

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration

### 레퍼런스 근거

- **Carbon Design System**: Library menu navigation There are two kinds of symbols — library symbols and document symbols. Library symbols are available in any Sketch document...
- **Primer**: Octicon nav items navigation 12 px

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- active 상태는 URL/라우터와 자동 동기화
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## overlay / modal-dialog

**역할**: 확인/입력을 받는 모달

**탐지 출처**: modal and dialog

### 구조 (Anatomy)

- backdrop
- container
- header
- content
- footer(optional)
- close-button

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `closed` | 닫힌 상태 |
| `opening` | 열리는 중 (전환 애니메이션) |
| `open` | 열린 상태 |
| `closing` | 닫히는 중 |

### 토큰 바인딩

```
surface: surface.overlay
backdrop: color.neutral.900/60
radius: radius.lg
shadow: elevation.modal
padding: spacing.24
```

### 접근성

- role="dialog" with aria-modal="true"
- focus trap (Tab 순환)
- Escape로 닫기
- aria-labelledby로 제목 연결
- 닫은 후 trigger 요소로 포커스 복귀

### 브랜드 적용

- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음

### 레퍼런스 근거

- **Primer**: ActionMenu is composed of ActionList and Overlay patterns used for quick actions and selections. AnchoredOverlay

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- Escape / backdrop click으로 닫기, 열 때 첫 focusable 요소로 이동
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## overlay / bottom-sheet

**역할**: 모바일용 하단 시트

**탐지 출처**: modal and dialog

### 구조 (Anatomy)

- backdrop
- container
- header
- content
- footer(optional)
- close-button

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `closed` | 닫힌 상태 |
| `opening` | 열리는 중 (전환 애니메이션) |
| `open` | 열린 상태 |
| `closing` | 닫히는 중 |

### 토큰 바인딩

```
surface: surface.overlay
backdrop: color.neutral.900/60
radius: radius.lg
shadow: elevation.modal
padding: spacing.24
```

### 접근성

- role="dialog" with aria-modal="true"
- focus trap (Tab 순환)
- Escape로 닫기
- aria-labelledby로 제목 연결
- 닫은 후 trigger 요소로 포커스 복귀

### 브랜드 적용

- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음

### 레퍼런스 근거

- **Primer**: ActionMenu is composed of ActionList and Overlay patterns used for quick actions and selections. AnchoredOverlay

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- Escape / backdrop click으로 닫기, 열 때 첫 focusable 요소로 이동
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## overlay / confirm-dialog

**역할**: 삭제/위험 작업 확인 다이얼로그

**탐지 출처**: modal and dialog

### 구조 (Anatomy)

- backdrop
- container
- header
- content
- footer(optional)
- close-button

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `closed` | 닫힌 상태 |
| `opening` | 열리는 중 (전환 애니메이션) |
| `open` | 열린 상태 |
| `closing` | 닫히는 중 |

### 토큰 바인딩

```
surface: surface.overlay
backdrop: color.neutral.900/60
radius: radius.lg
shadow: elevation.modal
padding: spacing.24
```

### 접근성

- role="dialog" with aria-modal="true"
- focus trap (Tab 순환)
- Escape로 닫기
- aria-labelledby로 제목 연결
- 닫은 후 trigger 요소로 포커스 복귀

### 브랜드 적용

- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음

### 레퍼런스 근거

- **Primer**: ActionMenu is composed of ActionList and Overlay patterns used for quick actions and selections. AnchoredOverlay

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- Escape / backdrop click으로 닫기, 열 때 첫 focusable 요소로 이동
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / pricing-card

**역할**: 플랜별 가격/기능 비교 카드

**탐지 출처**: pricing and plans

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / feature-comparison

**역할**: 플랜 간 기능 비교 테이블

**탐지 출처**: pricing and plans

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## feedback / upgrade-banner

**역할**: 업그레이드 유도 배너

**탐지 출처**: pricing and plans

### 구조 (Anatomy)

- container
- icon
- message
- action(optional)
- close-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `info` | 정보 알림 |
| `success` | 성공 알림 |
| `warning` | 경고 알림 |
| `danger` | 에러/위험 알림 |

### 토큰 바인딩

```
surface: feedback.info.surface
text: feedback.info.text
icon: feedback.info.icon
border: feedback.info.border
radius: radius.sm
```

### 접근성

- role="alert" for urgent messages
- role="status" for non-urgent
- aria-live="polite" or "assertive"
- 닫기 버튼에 aria-label 필수

### 브랜드 적용

- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: We welcome all feedback, designs, or ideas in order to produce the best possible experience for our users. If you're interested in contributing, ch...
- **Primer**: Messaging components are used to provide important and relevant information to the user, including feedback, contextual information, product update...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- auto-dismiss 시간은 내용 길이에 비례 (기본 5초)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / avatar

**역할**: 사용자 프로필 이미지/이니셜

**탐지 출처**: user profile and avatar

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Primer**: Avatar Avatar is an image that represents a user or organization.

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## overlay / user-menu

**역할**: 사용자 드롭다운 메뉴

**탐지 출처**: user profile and avatar

### 구조 (Anatomy)

- backdrop
- container
- header
- content
- footer(optional)
- close-button

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `closed` | 닫힌 상태 |
| `opening` | 열리는 중 (전환 애니메이션) |
| `open` | 열린 상태 |
| `closing` | 닫히는 중 |

### 토큰 바인딩

```
surface: surface.overlay
backdrop: color.neutral.900/60
radius: radius.lg
shadow: elevation.modal
padding: spacing.24
```

### 접근성

- role="dialog" with aria-modal="true"
- focus trap (Tab 순환)
- Escape로 닫기
- aria-labelledby로 제목 연결
- 닫은 후 trigger 요소로 포커스 복귀

### 브랜드 적용

- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음

### 레퍼런스 근거

- **Primer**: ActionMenu is composed of ActionList and Overlay patterns used for quick actions and selections. AnchoredOverlay

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- Escape / backdrop click으로 닫기, 열 때 첫 focusable 요소로 이동
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / profile-card

**역할**: 사용자 프로필 요약 카드

**탐지 출처**: user profile and avatar

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## feedback / step-progress

**역할**: 단계별 진행 표시

**탐지 출처**: onboarding and stepper

### 구조 (Anatomy)

- container
- icon
- message
- action(optional)
- close-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `info` | 정보 알림 |
| `success` | 성공 알림 |
| `warning` | 경고 알림 |
| `danger` | 에러/위험 알림 |

### 토큰 바인딩

```
surface: feedback.info.surface
text: feedback.info.text
icon: feedback.info.icon
border: feedback.info.border
radius: radius.sm
```

### 접근성

- role="alert" for urgent messages
- role="status" for non-urgent
- aria-live="polite" or "assertive"
- 닫기 버튼에 aria-label 필수

### 브랜드 적용

- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: We welcome all feedback, designs, or ideas in order to produce the best possible experience for our users. If you're interested in contributing, ch...
- **Primer**: Messaging components are used to provide important and relevant information to the user, including feedback, contextual information, product update...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- auto-dismiss 시간은 내용 길이에 비례 (기본 5초)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## navigation / wizard-layout

**역할**: 위저드 레이아웃 (이전/다음)

**탐지 출처**: onboarding and stepper

### 구조 (Anatomy)

- container
- nav-item
- icon(optional)
- label
- indicator(active)
- badge(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `hover` | 마우스 오버 시 |
| `active` | 클릭/탭 중 |
| `collapsed` | 접힌 상태 |

### 토큰 바인딩

```
surface: surface.nav.{state}
text: text.nav.{state}
indicator: color.accent.500
padding: spacing.8 spacing.16
```

### 접근성

- nav landmark (role="navigation")
- aria-current="page" for active item
- 키보드 화살표 탐색 지원

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration

### 레퍼런스 근거

- **Carbon Design System**: Library menu navigation There are two kinds of symbols — library symbols and document symbols. Library symbols are available in any Sketch document...
- **Primer**: Octicon nav items navigation 12 px

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- active 상태는 URL/라우터와 자동 동기화
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## overlay / tooltip-guide

**역할**: 기능 안내 툴팁

**탐지 출처**: onboarding and stepper

### 구조 (Anatomy)

- backdrop
- container
- header
- content
- footer(optional)
- close-button

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `closed` | 닫힌 상태 |
| `opening` | 열리는 중 (전환 애니메이션) |
| `open` | 열린 상태 |
| `closing` | 닫히는 중 |

### 토큰 바인딩

```
surface: surface.overlay
backdrop: color.neutral.900/60
radius: radius.lg
shadow: elevation.modal
padding: spacing.24
```

### 접근성

- role="dialog" with aria-modal="true"
- focus trap (Tab 순환)
- Escape로 닫기
- aria-labelledby로 제목 연결
- 닫은 후 trigger 요소로 포커스 복귀

### 브랜드 적용

- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음

### 레퍼런스 근거

- **Primer**: ActionMenu is composed of ActionList and Overlay patterns used for quick actions and selections. AnchoredOverlay

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- Escape / backdrop click으로 닫기, 열 때 첫 focusable 요소로 이동
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / chart-container

**역할**: 차트 래퍼 (타이틀, 범례 포함)

**탐지 출처**: charts and visualization

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## overlay / chart-tooltip

**역할**: 데이터 포인트 호버 시 상세 정보

**탐지 출처**: charts and visualization

### 구조 (Anatomy)

- backdrop
- container
- header
- content
- footer(optional)
- close-button

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `closed` | 닫힌 상태 |
| `opening` | 열리는 중 (전환 애니메이션) |
| `open` | 열린 상태 |
| `closing` | 닫히는 중 |

### 토큰 바인딩

```
surface: surface.overlay
backdrop: color.neutral.900/60
radius: radius.lg
shadow: elevation.modal
padding: spacing.24
```

### 접근성

- role="dialog" with aria-modal="true"
- focus trap (Tab 순환)
- Escape로 닫기
- aria-labelledby로 제목 연결
- 닫은 후 trigger 요소로 포커스 복귀

### 브랜드 적용

- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음

### 레퍼런스 근거

- **Primer**: ActionMenu is composed of ActionList and Overlay patterns used for quick actions and selections. AnchoredOverlay

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- Escape / backdrop click으로 닫기, 열 때 첫 focusable 요소로 이동
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / chart-legend

**역할**: 차트 범례

**탐지 출처**: charts and visualization

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / search-field

**역할**: 검색 입력 필드

**탐지 출처**: search and filter

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / search-results

**역할**: 검색 결과 목록

**탐지 출처**: search and filter

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / filter-panel

**역할**: 필터 옵션 패널

**탐지 출처**: search and filter

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## overlay / autocomplete

**역할**: 자동완성 드롭다운

**탐지 출처**: search and filter

### 구조 (Anatomy)

- backdrop
- container
- header
- content
- footer(optional)
- close-button

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `closed` | 닫힌 상태 |
| `opening` | 열리는 중 (전환 애니메이션) |
| `open` | 열린 상태 |
| `closing` | 닫히는 중 |

### 토큰 바인딩

```
surface: surface.overlay
backdrop: color.neutral.900/60
radius: radius.lg
shadow: elevation.modal
padding: spacing.24
```

### 접근성

- role="dialog" with aria-modal="true"
- focus trap (Tab 순환)
- Escape로 닫기
- aria-labelledby로 제목 연결
- 닫은 후 trigger 요소로 포커스 복귀

### 브랜드 적용

- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음

### 레퍼런스 근거

- **Primer**: Autocomplete Autocomplete allows users to quickly filter through a list of options and pick one or more values for a field.

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- Escape / backdrop click으로 닫기, 열 때 첫 focusable 요소로 이동
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / kanban-board

**역할**: 칸반 보드 레이아웃

**탐지 출처**: kanban and board

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / kanban-column

**역할**: 칸반 컬럼 (상태별)

**탐지 출처**: kanban and board

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / kanban-card

**역할**: 드래그 가능한 작업 카드

**탐지 출처**: kanban and board

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## feedback / toast

**역할**: 일시적 성공/에러 알림

**탐지 출처**: notifications

### 구조 (Anatomy)

- container
- icon
- message
- action(optional)
- close-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `info` | 정보 알림 |
| `success` | 성공 알림 |
| `warning` | 경고 알림 |
| `danger` | 에러/위험 알림 |

### 토큰 바인딩

```
surface: feedback.info.surface
text: feedback.info.text
icon: feedback.info.icon
border: feedback.info.border
radius: radius.sm
```

### 접근성

- role="alert" for urgent messages
- role="status" for non-urgent
- aria-live="polite" or "assertive"
- 닫기 버튼에 aria-label 필수

### 브랜드 적용

- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: We welcome all feedback, designs, or ideas in order to produce the best possible experience for our users. If you're interested in contributing, ch...
- **Primer**: Messaging components are used to provide important and relevant information to the user, including feedback, contextual information, product update...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- auto-dismiss 시간은 내용 길이에 비례 (기본 5초)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## feedback / inline-alert

**역할**: 페이지 내 알림 배너

**탐지 출처**: notifications

### 구조 (Anatomy)

- container
- icon
- message
- action(optional)
- close-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `info` | 정보 알림 |
| `success` | 성공 알림 |
| `warning` | 경고 알림 |
| `danger` | 에러/위험 알림 |

### 토큰 바인딩

```
surface: feedback.info.surface
text: feedback.info.text
icon: feedback.info.icon
border: feedback.info.border
radius: radius.sm
```

### 접근성

- role="alert" for urgent messages
- role="status" for non-urgent
- aria-live="polite" or "assertive"
- 닫기 버튼에 aria-label 필수

### 브랜드 적용

- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: We welcome all feedback, designs, or ideas in order to produce the best possible experience for our users. If you're interested in contributing, ch...
- **Primer**: Messaging components are used to provide important and relevant information to the user, including feedback, contextual information, product update...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- auto-dismiss 시간은 내용 길이에 비례 (기본 5초)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## feedback / empty-state

**역할**: 데이터가 없을 때 안내 화면

**탐지 출처**: notifications

### 구조 (Anatomy)

- container
- icon
- message
- action(optional)
- close-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `info` | 정보 알림 |
| `success` | 성공 알림 |
| `warning` | 경고 알림 |
| `danger` | 에러/위험 알림 |

### 토큰 바인딩

```
surface: feedback.info.surface
text: feedback.info.text
icon: feedback.info.icon
border: feedback.info.border
radius: radius.sm
```

### 접근성

- role="alert" for urgent messages
- role="status" for non-urgent
- aria-live="polite" or "assertive"
- 닫기 버튼에 aria-label 필수

### 브랜드 적용

- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: We welcome all feedback, designs, or ideas in order to produce the best possible experience for our users. If you're interested in contributing, ch...
- **Primer**: Empty states Empty states are used to fill spaces when no content has been added yet, or is temporarily empty due to the nature of the feature.

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- auto-dismiss 시간은 내용 길이에 비례 (기본 5초)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## feedback / banner

**역할**: 전체 화면 상단 공지 배너

**탐지 출처**: notifications

### 구조 (Anatomy)

- container
- icon
- message
- action(optional)
- close-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `info` | 정보 알림 |
| `success` | 성공 알림 |
| `warning` | 경고 알림 |
| `danger` | 에러/위험 알림 |

### 토큰 바인딩

```
surface: feedback.info.surface
text: feedback.info.text
icon: feedback.info.icon
border: feedback.info.border
radius: radius.sm
```

### 접근성

- role="alert" for urgent messages
- role="status" for non-urgent
- aria-live="polite" or "assertive"
- 닫기 버튼에 aria-label 필수

### 브랜드 적용

- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내
- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 레퍼런스 근거

- **Carbon Design System**: We welcome all feedback, designs, or ideas in order to produce the best possible experience for our users. If you're interested in contributing, ch...
- **Primer**: Banner Banner is used to highlight important information.

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- auto-dismiss 시간은 내용 길이에 비례 (기본 5초)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / stat-card

**역할**: 주요 수치를 표시하는 통계 카드

**탐지 출처**: dashboard cards

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / insight-card

**역할**: 인사이트나 트렌드를 요약하는 카드

**탐지 출처**: dashboard cards

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / activity-card

**역할**: 최근 활동 피드 카드

**탐지 출처**: dashboard cards

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / section-header

**역할**: 대시보드 섹션 구분 헤더

**탐지 출처**: dashboard cards

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / comment-thread

**역할**: 댓글 스레드 목록

**탐지 출처**: comments and discussion

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / comment-input

**역할**: 댓글 입력 영역

**탐지 출처**: comments and discussion

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## overlay / mention-popup

**역할**: @멘션 자동완성 팝업

**탐지 출처**: comments and discussion

### 구조 (Anatomy)

- backdrop
- container
- header
- content
- footer(optional)
- close-button

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `closed` | 닫힌 상태 |
| `opening` | 열리는 중 (전환 애니메이션) |
| `open` | 열린 상태 |
| `closing` | 닫히는 중 |

### 토큰 바인딩

```
surface: surface.overlay
backdrop: color.neutral.900/60
radius: radius.lg
shadow: elevation.modal
padding: spacing.24
```

### 접근성

- role="dialog" with aria-modal="true"
- focus trap (Tab 순환)
- Escape로 닫기
- aria-labelledby로 제목 연결
- 닫은 후 trigger 요소로 포커스 복귀

### 브랜드 적용

- [editorial+precise+trustworthy] motion: 콘텐츠 전환 위주, UI chrome 모션 최소화 + 120-180ms, 군더더기 없는 전환 + 모든 전환에 동일한 easing/duration
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음

### 레퍼런스 근거

- **Primer**: ActionMenu is composed of ActionList and Overlay patterns used for quick actions and selections. AnchoredOverlay

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- Escape / backdrop click으로 닫기, 열 때 첫 focusable 요소로 이동
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / chat-message

**역할**: 채팅 메시지 말풍선

**탐지 출처**: chat and messaging

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## input / chat-input

**역할**: 메시지 입력 영역

**탐지 출처**: chat and messaging

### 구조 (Anatomy)

- container
- label
- input-area
- helper-text(optional)
- leading-icon(optional)
- clear-button(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `focus` | 키보드 포커스 시 |
| `filled` | 값이 입력된 상태 |
| `error` | 유효성 검증 실패 |
| `disabled` | 비활성 (상호작용 불가) |
| `readonly` | 읽기 전용 |

### 토큰 바인딩

```
surface: surface.input.{state}
text: text.input.{state}
border: border.input.{state}
radius: radius.sm
padding: spacing.8 spacing.12
font: typography.text.md.regular
```

### 접근성

- label과 input을 for/id로 연결
- aria-describedby로 helper/error text 연결
- aria-invalid="true" when error
- aria-required="true" when required

### 브랜드 적용

- [editorial+precise+trustworthy] hover: 텍스트 underline 또는 color shift, 장식적 효과 없음 + 정확한 border/outline 변화 + 예측 가능하고 일관된 hover 패턴
- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] feedback: 콘텐츠 맥락 안에서 인라인 표시, 토스트보다 인라인 선호 + 명확한 상태 구분, 진행률/결과를 수치로 표시 + 결과를 반드시 확인, 실패 시 복구 방법 안내

### 레퍼런스 근거

- **Carbon Design System**: Number input Text input
- **Primer**: I worked in data visualization and map-making for most of my career, and solving design problems with data is my jam. To me there's something uniqu...

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- error 상태에서 helper text → error message로 자동 전환
- label은 항상 visible (placeholder만으로 대체 금지)
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분

---

## data-display / chat-thread

**역할**: 대화 스레드 목록

**탐지 출처**: chat and messaging

### 구조 (Anatomy)

- container
- header
- content-area
- footer(optional)
- action(optional)

### 상태 (States)

| 상태 | 설명 |
|------|------|
| `default` | 기본 상태 |
| `loading` | 로딩 중 (스피너 표시) |
| `empty` | 데이터 없음 |
| `error` | 유효성 검증 실패 |

### 토큰 바인딩

```
surface: surface.card.default
border: border.subtle
radius: radius.md
padding: spacing.16 spacing.20
shadow: elevation.raised
```

### 접근성

- 적절한 heading level 사용
- 데이터 테이블은 scope와 caption 필수
- 빈 상태에서 안내 텍스트 제공

### 브랜드 적용

- [editorial+precise+trustworthy] density: 넉넉한 line-height와 margin, 읽기 편한 간격 + 엄격한 spacing scale 준수, 임의 값 금지 + 기존 레이아웃 유지, 갑작스런 위치 변경 없음
- [editorial+precise+trustworthy] color: 타이포그래피로 위계 형성, 컬러보다 weight/size 활용 + 정확한 semantic 분리, 모호한 중간 톤 지양 + 안정적인 neutral 기반, 과한 accent 변화 없음

### 구현 노트

- 기존에 같은 역할의 컴포넌트가 있으면 토큰 교체부터 시작
- variant prop으로 시각적 변형을 관리 (하드코딩 금지)
- 빈 상태(empty-state)와 에러 상태를 반드시 처리
- 텍스트 위계가 핵심 — 컬러보다 weight/size로 구분
