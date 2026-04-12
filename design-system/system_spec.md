# ColorFit System Spec

## 1. Positioning

- **Brand**: ColorFit
- **Product**: 퍼스널컬러 진단 결과를 실제 쇼핑과 코디 의사결정으로 연결하는 AI 패션 추천 앱
- **Audience**: 퍼스널컬러 기반 쇼핑 결정을 돕고 싶은 사용자, 코디 추천과 실제 구매 연결을 원하는 모바일 쇼핑 사용자, 내 취향과 톤에 맞는 패션 큐레이션을 원하는 사용자
- **Platforms**: mobile web
- **Accessibility floor**: WCAG 2.2 AA

## 2. Identity Guardrails

- **Brand keywords**: editorial, precise, trustworthy, warm
- **Anti-keywords**: generic, noisy, clinical, cheap
- **Tone of voice**: clear, reassuring, curated, confident
- **Visual direction**: warm neutrals, serif-sans contrast, measured whitespace, fashion editorial hierarchy, tonal accent cues
- **Interaction direction**: guided decision flow, explainable scoring, low-noise motion, confidence-building comparison

## 3. Design Principles

- **Editorial Hierarchy**: 타이포그래피와 여백으로 위계를 만들고, 장식은 의미를 돕는 범위에서만 사용합니다.
- **Precision Over Ornament**: 장식보다 정보의 정렬, 상태의 정확성, 반응의 일관성을 우선합니다.
- **Trust Through Consistency**: 예측 가능한 인터랙션과 안정적인 시각 언어로 신뢰를 쌓습니다.
- **Warm**: `warm`를 시각적 선택과 인터랙션 선택의 기본 기준으로 삼습니다.

## 4. Foundation Priorities

- **Grid, container, and page rhythm** (high): signal 42
- **Content design and microcopy rules** (high): signal 36
- **Accessibility rules and contrast baseline** (high): signal 35
- **Color tokens and semantic color policy** (high): signal 35
- **Icon family and stroke policy** (high): signal 30

## 5. Token Strategy

- **Layering**: core -> semantic -> component
- **Core categories**: color, spacing, radius, typography, motion, elevation
- **Semantic categories**: surface, text, border, focus, feedback
- **Component categories**: button, input, navigation, overlay, editor
- **Typography families**: display, text, mono
- **Spacing scale**: 0, 2, 4, 8, 12, 16, 24, 32, 48, 64, 96

### Typography System (auto-resolved)

- **Heading**: Lora
- **Body**: Pretendard
- **Korean**: Pretendard
- **Product type detected**: editorial
- **Pairing source**: auto-scored
- **Line height**: relaxed
- **Type scale**: base 16px, ratio 1.333 (xs=12px, sm=14px, md=16px, lg=21px, xl=28px, 2xl=38px, 3xl=50px)
- **Strategy**:
  - 헤딩(세리프) + 본문(산세리프) 대비 구조 — 에디토리얼 정석
  - 한글 서체: Pretendard — 라틴과 x-height/weight 조화
  - editorial 키워드 → 넉넉한 line-height, 헤딩에 serif 사용
  - precise 키워드 → tight letter-spacing, tabular figures 권장
- **Heading note**: 본문 읽기에 최적화된 세리프. 블로그, 매거진에 많이 사용.
- **Body note**: 한글 UI 서체의 사실상 표준. Apple SD Gothic Neo 기반이지만 더 정교함. 라틴은 Inter 계열.
- **Loading**: Pretendard(preload), Lora(preload) | display: swap

## 6. Color Reference

- No curated color reference connected.

## 7. Component Strategy

- **Product primitives**: personal color onboarding, recommendation feed, outfit detail and comparison, shopping price comparison, closet analysis, ai try-on
- **Required families**: button, feedback, input, navigation, data-display, foundation, overlay

- **button**: primary-button, secondary-button, ghost-button, icon-button, cta-button
- **feedback**: reason-chip, top-pick-badge, price-highlight-badge, inline-alert, empty-state, toast
- **input**: tone-selector, mood-tag-selector, budget-range-slider, upload-dropzone, multi-item-selector, text-field, search-field, segmented-control
- **navigation**: mobile-topbar, mobile-tab-bar, back-button, section-tabs
- **data-display**: score-bar-chart, comparison-overlay-chart, price-compare-table, closet-grid, item-score-badge, analysis-summary-card
- **foundation**: step-progress, preference-card, outfit-feed-card, tpo-filter-tab, save-toggle, recommendation-reason-list, merchant-row, similar-item-card
- **overlay**: outfit-detail-sheet, try-on-preview, generation-state-panel, bottom-sheet, modal-dialog

## 8. Implementation Guardrails

- 기존 핵심 화면, 진입점, 작업 흐름은 명시적 승인 없이 제거하거나 숨기지 않음
- 전면 셸 리라이트보다 토큰 -> primitive -> feature surface 순서의 점진적 롤아웃을 우선
- 새 시각 규칙은 지원 대상 테마와 breakpoint 전체에서 먼저 검증
- 기존 데이터 밀도와 업무 완료 경로를 유지한 상태에서 시각 품질을 높이는 방향을 우선
- 기능 위치 변경, 정보 구조 변경, 패널 제거는 별도의 migration plan이 있을 때만 수행

## 9. Reference Absorption Rule

- Analysed live reference sources: 3
- Rule: copy visuals from no single source; absorb patterns only when they reinforce brand keywords and avoid anti-keywords.
- Use references to validate structure, accessibility, token discipline, and documentation quality.

## 10. Ontology Targets

- **component**: 121
- **design_system**: 68
- **layout**: 42
- **content**: 36
- **accessibility**: 35
- **color**: 35
- **pattern**: 35
- **iconography**: 30

## 11. Profile Validation

- No validation issues.
