# ColorFit(컬러핏) 상세 기획서 v1.0

> **"내 색을 아는 순간, 선택이 쉬워진다"**
> AI 퍼스널컬러 기반 패션 의사결정 엔진

**작성일:** 2026-03-23
**프로젝트 기간:** 5주 (MVP 4주 + 발표 1주)
**플랫폼:** 모바일 웹 (반응형)

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [문제 정의 및 기획 동기](#2-문제-정의-및-기획-동기)
3. [페르소나 및 사용자 여정 상세](#3-페르소나-및-사용자-여정-상세)
4. [시스템 아키텍처](#4-시스템-아키텍처)
5. [데이터 수집 및 전처리 파이프라인](#5-데이터-수집-및-전처리-파이프라인)
6. [추천 엔진 상세 설계](#6-추천-엔진-상세-설계)
7. [도메인 특화 기능 설계](#7-도메인-특화-기능-설계)
8. [UI/UX 설계](#8-uiux-설계)
9. [사용자 시나리오 및 대화 흐름](#9-사용자-시나리오-및-대화-흐름)
10. [전체 기능 리스트 (Feature Backlog)](#10-전체-기능-리스트)
11. [진단(온보딩) 설계 상세](#11-진단온보딩-설계-상세)
12. [평가 계획](#12-평가-계획)
13. [구현 로드맵](#13-구현-로드맵)
14. [기술 스택 상세](#14-기술-스택-상세)
15. [비즈니스 모델 & GTM 전략](#15-비즈니스-모델--gtm-전략)
16. [리스크 관리 및 대응 전략](#16-리스크-관리-및-대응-전략)
17. [윤리적 고려사항](#17-윤리적-고려사항)
18. [부록](#18-부록)

---

## 1. 프로젝트 개요

### 1.1 프로젝트 비전

ColorFit(컬러핏)은 퍼스널컬러 진단 결과와 실제 패션 쇼핑 사이의 단절을 해소하는 AI 패션 의사결정 엔진이다. 기존 서비스들이 "영감"과 "탐색"에 집중하는 반면, ColorFit은 **"왜 이 옷이 나에게 어울리는지"를 논리적으로 설명하고, 더 합리적인 가격의 대안까지 제시**하여 소비자의 결정 피로를 획기적으로 줄인다. "내 색을 아는 순간, 선택이 쉬워진다"는 슬로건 아래, 탐색이 아닌 결정의 종착지를 지향한다.

### 1.2 핵심 목표

| # | 목표 | 설명 | 성공 지표 (KPI) |
|---|------|------|----------------|
| G1 | 온보딩 완주율 | 퍼스널컬러+TPO+예산 3단계 온보딩을 이탈 없이 완료 | 진단 시작 → 완료율 ≥ 60% |
| G2 | 회원 전환 | 온보딩 완료 사용자를 가입 사용자로 전환 | 진단 완료 → 회원가입 전환율 ≥ 40% |
| G3 | 구매 연결 | 추천 코디에서 실제 외부 쇼핑몰로 이동 | 코디 추천 → 외부 링크 클릭율 ≥ 15% |
| G4 | 재방문 유도 | 저장·피드백 루프로 습관적 재방문 생성 | 주간 재방문율 (WAU/MAU) ≥ 30% |
| G5 | 설명 가치 입증 | 추천 이유가 실제 구매 결정에 영향을 줌 | 추천 이유 열람율 ≥ 50% |
| G6 | 추천 신뢰도 | 추천 코디의 퍼스널컬러 적합도 확보 | 전문가 평가 색상 매칭 정확도 ≥ 80% |

### 1.3 프로젝트 범위

**In-Scope (MVP 4주)**
- 퍼스널컬러 12-tone 선택 온보딩 (직접 선택 방식)
- TPO 8종 + 스타일 무드 + 예산 설정
- 개인화 코디 피드 (스코어링 기반 정렬)
- 코디 카드 1줄 요약 + 추천 이유 2줄
- 점수 뱃지 (personalColorFit / occasionFit)
- 아이템 단품 상세 + 판매처별 가격 비교
- Exact / Similar 구분 + 유사 상품 목록
- 최저가 외부 쇼핑몰 링크
- save(저장) / dislike(싫어요) + 피드 즉시 반영
- Top Pick 단일 추천 / A vs B 비교 판정
- 소셜 로그인 (카카오, 구글) + 게스트 탐색

**Out-of-Scope (Phase 2 이후)**
- 실제 결제(PG 연동) — 외부 링크 방식으로 대체
- 자체 상품 재고 관리
- AI 셀카 기반 퍼스널컬러 자동 진단
- 커뮤니티 / SNS 공유 카드
- 날씨 연동 추천 / 옷장 관리 / 풀세팅 모드
- 푸시 알림 (가격 알림, 아침 코디 알림)

### 1.4 용어 정의

| 용어 | 정의 |
|------|------|
| 퍼스널컬러 12-tone | 봄/여름/가을/겨울 × 라이트/뮤트/딥 등 12가지 세부 톤 분류 체계 |
| TPO | Time(시간)·Place(장소)·Occasion(상황)의 약자. 코디의 맥락을 정의 |
| personalColorFit | 코디 색상이 사용자의 퍼스널컬러 팔레트에 얼마나 적합한지를 0~100으로 수치화 |
| occasionFit | 코디가 선택한 TPO(출근, 소개팅 등)에 얼마나 적합한지를 0~100으로 수치화 |
| colorHarmony | 코디 내 아이템 간 색상 조화도. 60-30-10 법칙 기반 평가 |
| priceEfficiency | 사용자 설정 예산 대비 코디 총액의 효율성 점수 |
| isCompleteOutfit | 상의+하의(또는 원피스) 이상 구성되어 단독 착용 가능한 완성 코디 여부 |
| Exact Match | 동일 브랜드·동일 상품을 다른 판매처에서 판매하는 경우 |
| Similar Match | 동일 카테고리·유사 색상군·유사 가격대의 대체 가능 상품 |
| Top Pick | 저장 목록 또는 추천 목록 중 종합 적합도 최고 1개를 강조 추천하는 기능 |
| 코디 피드 | 사용자 프로필에 맞춰 개인화 정렬된 코디 카드 리스트 |
| 추천 이유 (reasons) | 코디가 추천된 근거를 자연어로 설명하는 1~2줄 문장 |

---

## 2. 문제 정의 및 기획 동기

### 2.1 패션 소비자의 세 가지 반복 고민

| 고민 | 핵심 질문 | 상세 |
|------|----------|------|
| **Fit & Harmony** | "이 옷이 나한테 어울릴까?" | 퍼스널컬러 진단을 받았지만, 막상 쇼핑 시 어떤 색상의 어떤 아이템을 골라야 하는지 연결되지 않음 |
| **Logical Curation** | "왜 나에게 어울리는데?" | 구매를 망설이는 순간, 소비자가 원하는 것은 감각의 강요가 아닌 납득할 수 있는 스타일링 논리 |
| **Smart Consumption** | "동일한 무드, 더 합리적인 대안은?" | 취향에 맞는 스타일을 찾아도 예산에 맞는 대안을 찾기 위해 여러 쇼핑몰을 돌아다니며 시간 소비 |

### 2.2 현재 시장의 한계

| 서비스 | 핵심 강점 | 빠진 고리 (Missing Link) |
|--------|----------|------------------------|
| **Lyst** | 1.6억 유저, 2.7만+ 브랜드의 압도적 탐색 풀 | 개인의 맥락(퍼스널컬러, 체형)과 추천 논리 부재 |
| **Stitch Fix** | 고도화된 1:1 개인화 스타일링 | 폐쇄적 큐레이션, 실시간 가격 비교 불가, 한정된 브랜드 |
| **LTK** | 막강한 크리에이터 기반 룩 발견 | 인플루언서 의존적, 유저 맞춤형 논리 부족 |
| **ModeSens** | 강력한 옴니채널 가격 비교 | 코디 제안 및 초개인화 스타일링 부재 |
| **무신사 / W컨셉** | 국내 최대 패션 커머스 | 퍼스널컬러 기반 필터 없음, 추천 이유 없음 |

### 2.3 White Space

```
                  초개인화(Fit)
                      │
         Stitch Fix   │   ★ ColorFit ★
                      │
  ──────────────────────────────────── 가격 효율(Price)
                      │
         LTK / Lyst   │   ModeSens
                      │
              설명 가능성(Why)
```

**ColorFit이 채우는 빈자리:** 초개인화(Fit) + 납득 가능한 큐레이션(Why) + 가격 효율(Price)을 하나의 여정(Seamless Journey)으로 완결 짓는 통합 결정 엔진

### 2.4 핵심 가설

| # | 가설 | 검증 방법 | 성공 기준 |
|---|------|----------|----------|
| H1 | 퍼스널컬러 기반 추천은 일반 추천 대비 클릭율이 높다 | A/B 테스트: 톤 필터 on/off | CTR 차이 ≥ 20% |
| H2 | 추천 이유 제공은 구매 전환율을 높인다 | A/B 테스트: 이유 표시 on/off | 외부 링크 클릭율 차이 ≥ 15% |
| H3 | 유사 상품 대체재는 이탈율을 낮춘다 | 코디 상세 → 이탈율 비교 | 이탈율 감소 ≥ 10% |
| H4 | 코디 단위 추천은 단품 대비 객단가를 높인다 | 코디 클릭 vs 단품 클릭 평균 가격 | 평균 클릭 코디 가격 ≥ 1.5배 |

---

## 3. 페르소나 및 사용자 여정 상세

### 3.1 Core 페르소나 (MVP)

#### A. 진단러 — 김지은 (25세, 사회초년생)

| 항목 | 내용 |
|------|------|
| 퍼스널컬러 | 여름쿨소프트 (전문 매장에서 진단 받음) |
| 핵심 불편 | 진단 받았는데 막상 쇼핑할 때 뭘 골라야 할지 모름 |
| 목표 | 진단 결과를 실제 쇼핑에 연결하고 싶다 |
| 주요 TPO | 출근룩, 소개팅, 주말 캐주얼 |
| 예산 | 3~10만원/아이템 |
| 디바이스 | 모바일 (인스타 즐겨봄) |

**시나리오 1: 소개팅 룩 찾기**
> "내일 소개팅인데 여름쿨 톤에 데이트룩으로 뭐 입어야 하지?"
1. ColorFit 앱 실행 → 여름쿨소프트 프로필 로드
2. TPO 탭에서 "데이트" 선택
3. 코디 피드에서 여름쿨 팔레트 기반 코디 노출
4. 추천 이유 확인: "여름쿨소프트 핵심 컬러 라벤더 블루 계열 + 데이트 룩에 적합한 A라인 실루엣"
5. 아이템별 가격 확인 → 최저가 무신사 링크로 이동 → 구매

**시나리오 2: 진단 결과가 뭔지 헷갈릴 때**
> "여름쿨소프트가 정확히 어떤 색이지?"
1. 마이페이지 → 톤 설명 화면 진입
2. 대표 색상 스와치 + "차갑고 부드러운 파스텔 계열이 피부를 밝게 만들어요" 설명
3. 추천색(라벤더, 소프트 핑크) / 비추천색(오렌지, 카키) 팔레트 프리뷰
4. 잘못 골랐다면 → 온보딩 수정으로 재선택

#### B. 바쁜이 — 박민준 (32세, 직장 3년차)

| 항목 | 내용 |
|------|------|
| 퍼스널컬러 | 가을웜딥 (진단 받았지만 기억 희미) |
| 핵심 불편 | 코디 고민할 시간이 없음. 사도 후회할까봐 결정 못함 |
| 목표 | 빠르게 "이거 사도 되겠다" 확신 얻고 싶다 |
| 주요 TPO | 출근룩, 중요한 미팅, 주말 편한 외출 |
| 예산 | 5~15만원/아이템 |
| 디바이스 | 모바일 (출퇴근 중 사용) |

**시나리오 1: 출퇴근 5분 코디 탐색**
> "5분 안에 이번 주 입을 출근룩 후보 3개만 찾고 싶어"
1. 홈 진입 즉시 코디 피드 (로딩 최소화)
2. TPO 탭 "출근" 선택 → 가을웜딥 코디 빠르게 스캔
3. 마음에 드는 2개 저장 → dislike로 나머지 빠르게 넘김
4. 퇴근 후 저장 목록에서 상세 확인 → 구매 결정

**시나리오 2: 미팅 전날 급하게 코디 확정**
> "내일 중요한 미팅인데 오피스룩 빨리 골라야 해, 20만원 이내"
1. 예산 슬라이더를 20만원으로 조정
2. TPO = "오피스/비즈니스" 전환
3. isCompleteOutfit 우선 → 상하의 완성 코디 먼저 노출
4. 코디 전체 최저가 합산 확인 → "총 17.8만원" → 즉시 결정

**시나리오 3: A vs B 비교 판정**
> "두 코디 중 어떤 게 나은지 모르겠어"
1. 저장한 2개 코디를 A vs B 비교 모드로 진입
2. 색상 적합도 / TPO 적합도 / 가격 효율을 나란히 비교
3. "A안이 가을웜딥 적합도 92점, B안은 78점" → A안 결정

#### C. 탐색러 — 이서연 (22세, 대학생)

| 항목 | 내용 |
|------|------|
| 퍼스널컬러 | 봄웜라이트 (유튜브로 셀프 진단) |
| 핵심 불편 | 마음에 드는 옷 발견 → 비슷한 저렴한 거 찾다가 시간 낭비 |
| 목표 | 내 취향 스타일을 최대한 저렴하게 구성하고 싶다 |
| 주요 TPO | 데이트, 학교, 파티, 여행 |
| 예산 | 1~5만원/아이템 |
| 디바이스 | 모바일 (유튜브·틱톡 주 소비) |

**시나리오 1: 마음에 드는 코디의 저렴한 버전**
> "이 코디 좋은데 총 25만원이네... 비슷한 느낌으로 10만원 이내 없나"
1. 코디 상세 화면에서 예산 재설정 → 10만원 이내
2. 유사 코디 자동 재구성 → 동일 톤/무드 유지하되 저가 아이템으로 교체
3. 아이템별 Similar 상품 확인 (SPA 브랜드 대안)
4. "유사도 87%, 가격 8.2만원" → 저가 코디 선택

**시나리오 2: 색상 조합 배우기**
> "이 코디가 왜 예쁜지 이해하고 싶어"
1. 코디 카드에서 "추천 이유 상세" 펼치기
2. 색상 근거: "봄웜라이트 핵심 컬러 코랄 + 아이보리의 톤온톤"
3. 상황 적합성: "데이트 룩에 어울리는 부드러운 실루엣"
4. 점수 뱃지: personalColorFit 94 / occasionFit 88

#### D. 결정 피로형 — 최수빈 (28세, 직장인)

| 항목 | 내용 |
|------|------|
| 퍼스널컬러 | 여름쿨뮤트 (진단 받음) |
| 핵심 불편 | 저장만 30개, 선택지가 많으면 결정 못함 |
| 목표 | 하나만 강하게 추천받고 바로 결정 |
| 주요 TPO | 일상, 출근, 약속 |
| 예산 | 5~10만원/아이템 |
| 디바이스 | 모바일 (여러 쇼핑 앱 비교 중) |

**시나리오 1: 선택 장애 해결**
> "저장한 게 너무 많아서 뭘 사야 할지 모르겠어"
1. 저장 목록에서 "Top Pick" 버튼 탭
2. 종합 적합도 최고 1개 코디가 강조 표시
3. "이 코디가 수빈님께 가장 잘 어울려요" + 간결한 3줄 이유
4. 확신 → 외부 링크 → 구매

**시나리오 2: One-shot 추천**
> "그냥 오늘 입을 거 하나만 골라줘"
1. 홈 화면 "오늘의 컬러핏" 버튼
2. TPO 자동 추론 (평일 오전 = 출근) + 여름쿨뮤트 프로필
3. 최적 코디 1개 즉시 제시
4. "이 코디 어때요?" → [좋아요] [다른 거 볼래요]

### 3.2 확장 페르소나 (Phase 2~3)

| | E. 뉴비 | F. 일상러 | G. 공유러 | H. 활용러 | I. 세팅러 |
|---|---|---|---|---|---|
| 나이 | 20세 | 29세 | 24세 | 30세 | 19세 |
| 핵심 문제 | 톤 몰라서 시작 못함 | 매일 아침 10분 고민 | 왜 어울리는지 설명 못함 | 항상 같은 옷만 입음 | 예산 빠듯한데 전신 필요 |
| 핵심 기능 | AI 셀카 진단 | 날씨 연동 추천 | 스타일 카드 + SNS 공유 | 역방향 추천 + 가상 피팅 | 풀세팅 패키지 |
| Phase | Phase 2 | Phase 2 | Phase 2~3 | Phase 2~3 | Phase 2~3 |

### 3.3 사용자 여정 6단계 상세

```
[인지]         [가입/로그인]      [온보딩]          [탐색]            [결정]          [재방문]
  │                │                │                │                │                │
  ▼                ▼                ▼                ▼                ▼                ▼
SNS/검색에서     카카오/구글       12-tone 선택      코디 피드         가격 비교 후      저장 목록
서비스 발견      소셜 로그인       TPO 선택          추천 이유 확인     구매 결정         다시 확인
  │            1탭 완료           스타일 무드        save / dislike   외부 쇼핑몰       가격 변동
  │            게스트 탐색 가능    예산 설정          Top Pick         이동              피드 조정
  │                                                 A vs B 비교
  │
  └── "퍼스널컬러 코디 추천" 검색 / 인스타 광고 / 친구 공유 링크
```

**단계별 핵심 UX 설계 포인트:**

| 단계 | 핵심 설계 | 사용자 심리 |
|------|----------|-----------|
| 인지 | 1분 진단 테스트 바이럴 콘텐츠 | "재밌어 보인다, 해볼까?" |
| 가입 | 로그인 없이 추천 1회 체험 가능 | "강제 가입 없으니 일단 해보자" |
| 온보딩 | 탭 3번으로 완료, 텍스트 입력 없음 | "진짜 빠르다, 30초면 끝이네" |
| 탐색 | 추천 이유 + 점수 뱃지로 신뢰 형성 | "이유가 있으니 믿음이 가네" |
| 결정 | 가격 비교 + 유사 상품으로 합리적 선택 | "여기가 더 싸네, 바로 사자" |
| 재방문 | 저장 코디 + 자동 로그인 + 업데이트 피드 | "저번에 찜해둔 거 확인하자" |

### 3.4 성장 플라이휠

```
                ┌──── E. 뉴비: 셀카 진단 유입 ────┐
                │                                  │
                ▼                                  │
    A/B/C/D Core 페르소나                           │
    ┌─────────────────────┐                        │
    │ 추천 → 설명 → 확신  │                        │
    │ → 구매 → 피드백     │                        │
    └─────────────────────┘                        │
                │                                  │
                ▼                                  │
         F. 일상러: 매일 알림 리텐션                 │
                │                                  │
                ▼                                  │
         G. 공유러: SNS 바이럴 ────────────────────┘
                │
                ▼
         H. 활용러: 옷장 활용 깊은 참여
                │
                ▼
         I. 세팅러: 풀세팅 구매 전환

    유입 → 코어 경험 → 리텐션 → 바이럴 → 전환
```

---

## 4. 시스템 아키텍처

### 4.1 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                      UI Layer (Client)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 온보딩    │  │ 코디 피드 │  │ 코디 상세 │  │ 아이템    │   │
│  │ 위자드    │  │ + TPO 탭  │  │ + 추천이유│  │ 상세+가격 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                    Next.js 15 + React 19                     │
│                    TailwindCSS + Framer Motion               │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS / REST API
┌────────────────────────┼────────────────────────────────────┐
│                   API Layer (Server)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Auth      │  │ Profile   │  │ Feed      │  │ Price     │   │
│  │ Service   │  │ Service   │  │ Service   │  │ Service   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                    Python FastAPI 0.115+                      │
│                    Pydantic v2 + SQLAlchemy 2.0               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────┐
│              Recommendation Engine Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Color Matcher │  │ Outfit Scorer │  │ Reason       │      │
│  │ (톤 매핑)     │  │ (코디 스코어링)│  │ Generator    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Similar      │  │ Top Pick     │                         │
│  │ Finder       │  │ Selector     │                         │
│  └──────────────┘  └──────────────┘                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────┐
│                    Data Layer                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL │  │ Redis     │  │ Naver     │  │ 12-tone   │   │
│  │(사용자,   │  │ Cache     │  │ Shopping  │  │ Palette   │   │
│  │ 코디, 반응)│  │           │  │ API       │  │ DB        │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 아키텍처 설계 원칙

| 원칙 | 설명 | 적용 |
|------|------|------|
| **Speed First** | 모바일 출퇴근 사용 환경에서 3초 이내 피드 로딩 | Redis 캐시, 코디 프리컴퓨팅, 이미지 CDN |
| **Explainability** | 모든 추천에는 반드시 이유가 동반 | Reason Generator가 스코어 기여 요인을 자연어로 변환 |
| **Modularity** | 추천 로직 변경이 UI에 영향 없음 | 스코어링/필터링/정렬을 독립 모듈로 분리 |

### 4.3 추천 엔진 파이프라인

```
사용자 요청                     추천 결과
    │                              ▲
    ▼                              │
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│ Profile │───▶│ Filter │───▶│ Score  │───▶│ Re-rank│───▶│ Reason │
│ Load    │    │        │    │        │    │        │    │ Gen    │
└────────┘    └────────┘    └────────┘    └────────┘    └────────┘
    │              │              │              │              │
 퍼스널컬러     톤 범위 필터   personalColor  isComplete    상위 2개
 TPO            TPO 태그 필터    Fit 계산      Outfit 가산   기여 요인
 예산            가격 범위       occasionFit    dislike 제외  → 자연어
 스타일 무드     필터            colorHarmony   다양성 보장   템플릿 변환
                                priceEff
```

### 4.4 쿼리 라우터

| 사용자 의도 | 예시 | 처리 경로 |
|------------|------|----------|
| 코디 추천 | "출근룩 보여줘" | Profile → Filter → Score → Feed |
| 단품 검색 | "니트 찾아줘" | 카테고리 필터 → 아이템 리스트 |
| 가격 비교 | "이거 어디가 제일 싸?" | Price Service → 판매처 비교 |
| 유사 상품 | "비슷한 거 더 싼 거 없어?" | Similar Finder → 대체재 리스트 |
| 톤 설명 | "여름쿨이 뭐야?" | 12-tone DB → 설명 콘텐츠 |
| TPO 변경 | "소개팅 룩으로 바꿔" | TPO 업데이트 → 피드 재생성 |
| 저장 관리 | "저장한 거 보여줘" | User DB → 저장 리스트 |
| Top Pick | "뭐 사야 할지 골라줘" | Top Pick Selector → 1개 강추 |

---

## 5. 데이터 수집 및 전처리 파이프라인

### 5.1 전체 파이프라인

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Collect  │───▶│ Clean   │───▶│Structure│───▶│  Index  │───▶│  Serve  │
│          │    │         │    │         │    │         │    │         │
│ API 호출  │    │ 정규화   │    │ 색상→톤  │    │ 코디 조합│    │ 피드 생성│
│ 크롤링    │    │ 중복 제거 │    │ 매핑    │    │ 스코어   │    │ 캐시    │
│ DB 구축   │    │ 누락 보완 │    │ TPO 태깅│    │ 프리계산 │    │ API 응답│
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### 5.2 데이터 소스별 상세

#### 네이버 쇼핑 API

| 항목 | 내용 |
|------|------|
| 엔드포인트 | `https://openapi.naver.com/v1/search/shop.json` |
| 호출 제한 | 하루 25,000회 (개인 키 기준) |
| 핵심 필드 | `title`, `link`, `image`, `lprice`, `hprice`, `mallName`, `category1~4` |
| 활용 계획 | 카테고리별 상품 수집 → 색상 추출 → 톤 매핑 → 코디 조합 |

```python
# 네이버 쇼핑 API 수집 코드
import httpx
from typing import list

NAVER_CLIENT_ID = "YOUR_CLIENT_ID"
NAVER_CLIENT_SECRET = "YOUR_CLIENT_SECRET"

async def search_naver_shopping(query: str, display: int = 100, start: int = 1) -> list[dict]:
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "start": start, "sort": "sim"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json().get("items", [])

# 카테고리별 수집 전략
FASHION_QUERIES = [
    "여성 블라우스 봄", "여성 니트 가을", "여성 원피스 여름",
    "남성 셔츠 출근", "남성 자켓 오피스", "여성 카디건 캐주얼",
    # ... TPO × 카테고리 × 시즌 조합
]
```

#### 무신사 / W컨셉 상품 데이터

| 항목 | 내용 |
|------|------|
| 접근 방식 | 공개 API 없음 → 상품 페이지 정적 크롤링 + 카테고리 탐색 |
| 핵심 필드 | 상품명, 가격, 브랜드, 카테고리, 색상, 이미지 URL |
| 수집 규모 | 카테고리당 200~500개, 총 5,000~10,000개 상품 |
| 주의사항 | robots.txt 준수, 요청 간격 2초 이상, 상업적 이용 제한 확인 |

#### 퍼스널컬러 12-tone 팔레트 DB

| 항목 | 내용 |
|------|------|
| 데이터 구성 | 12개 톤 × 각 20~30개 대표 색상 = 약 300개 색상 코드 |
| 형식 | HEX + RGB + HSL + 색상명(한글) |
| 출처 | 퍼스널컬러 전문가 자료 + 색채학 표준 팔레트 |
| 활용 | 상품 이미지 색상 → 가장 가까운 톤 매핑의 기준 데이터 |

#### 코디 이미지 데이터셋

| 항목 | 내용 |
|------|------|
| 수집처 | 무신사 코디숍, W컨셉 스타일링, 인스타그램 패션 계정 |
| 규모 | MVP 기준 500~1,000개 코디 세트 |
| 라벨링 | 카테고리(상의/하의/아우터), 색상 태그, TPO 태그, 시즌 태그 |
| 활용 | 코디 조합 생성의 레퍼런스 + 피드 이미지 |

### 5.3 수집 일정

| 소스 | 예상 시간 | 데이터 건수 | 저장 용량 |
|------|----------|-----------|----------|
| 네이버 쇼핑 API | 3일 | 20,000 상품 | ~500MB (이미지 포함) |
| 무신사 크롤링 | 2일 | 5,000 상품 | ~200MB |
| W컨셉 크롤링 | 1일 | 3,000 상품 | ~120MB |
| 12-tone 팔레트 | 0.5일 | 300 색상 | ~1MB |
| 코디 데이터셋 | 2일 | 800 코디 | ~400MB |
| **합계** | **~8.5일** | **~28,000건** | **~1.2GB** |

### 5.4 전처리 과정

#### 상품 데이터 정규화

```python
import re
from dataclasses import dataclass

@dataclass
class NormalizedProduct:
    product_id: str
    name: str
    brand: str
    category: str       # 상의/하의/아우터/원피스/신발/가방
    color_hex: str       # 대표 색상 HEX
    tone_id: str         # 매핑된 12-tone ID
    price: int
    mall_name: str
    mall_url: str
    image_url: str
    tags: list[str]      # TPO/시즌/스타일 태그

def normalize_product(raw: dict) -> NormalizedProduct:
    name = re.sub(r"<[^>]+>", "", raw["title"])  # HTML 태그 제거
    brand = extract_brand(name)
    category = classify_category(raw["category1"], raw["category2"])
    color_hex = extract_dominant_color(raw["image"])  # 이미지에서 주요 색상 추출
    tone_id = map_color_to_tone(color_hex)  # HEX → 12-tone 매핑

    return NormalizedProduct(
        product_id=generate_id(raw),
        name=name,
        brand=brand,
        category=category,
        color_hex=color_hex,
        tone_id=tone_id,
        price=int(raw["lprice"]),
        mall_name=raw["mallName"],
        mall_url=raw["link"],
        image_url=raw["image"],
        tags=generate_tags(category, name),
    )
```

#### 색상 → 퍼스널컬러 톤 매핑 알고리즘

```python
import colorsys
import numpy as np

# 12-tone 팔레트 DB (각 톤의 대표 색상 리스트)
TONE_PALETTES: dict[str, list[tuple[int, int, int]]] = {
    "spring_warm_light": [(255, 183, 150), (255, 213, 166), ...],
    "summer_cool_soft": [(176, 166, 198), (159, 185, 204), ...],
    "autumn_warm_deep": [(139, 90, 43), (165, 100, 50), ...],
    "winter_cool_deep": [(30, 30, 80), (70, 20, 50), ...],
    # ... 12개 톤
}

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def color_distance(c1: tuple, c2: tuple) -> float:
    """CIE76 색차 근사 (RGB 유클리드 거리)"""
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def map_color_to_tone(hex_color: str) -> str:
    """상품 색상 HEX → 가장 가까운 12-tone 매핑"""
    rgb = hex_to_rgb(hex_color)
    best_tone = ""
    best_distance = float("inf")

    for tone_id, palette in TONE_PALETTES.items():
        min_dist = min(color_distance(rgb, p) for p in palette)
        if min_dist < best_distance:
            best_distance = min_dist
            best_tone = tone_id

    return best_tone

def calculate_personal_color_fit(product_tone: str, user_tone: str) -> float:
    """상품 톤과 사용자 톤의 적합도 (0~100)"""
    if product_tone == user_tone:
        return 100.0

    TONE_COMPATIBILITY = {
        # (상품 톤, 사용자 톤) → 적합도
        ("spring_warm_light", "spring_warm_bright"): 85.0,
        ("spring_warm_light", "autumn_warm_deep"): 60.0,
        ("summer_cool_soft", "summer_cool_light"): 85.0,
        ("summer_cool_soft", "winter_cool_deep"): 55.0,
        # ... 12×12 매트릭스
    }
    return TONE_COMPATIBILITY.get((product_tone, user_tone), 40.0)
```

### 5.5 코디 스코어링 알고리즘

```python
from dataclasses import dataclass

@dataclass
class OutfitScore:
    personal_color_fit: float   # 0~100
    occasion_fit: float         # 0~100
    color_harmony: float        # 0~100
    price_efficiency: float     # 0~100
    total_score: float          # 가중합
    reasons: list[str]          # 추천 이유 2줄

# 가중치 (합 = 1.0)
WEIGHTS = {
    "personal_color_fit": 0.35,
    "occasion_fit": 0.25,
    "color_harmony": 0.20,
    "price_efficiency": 0.20,
}

def score_outfit(outfit: list[NormalizedProduct], user_profile: dict) -> OutfitScore:
    # 1. personalColorFit: 코디 내 모든 아이템의 톤 적합도 평균
    pcf_scores = [
        calculate_personal_color_fit(item.tone_id, user_profile["tone"])
        for item in outfit
    ]
    personal_color_fit = sum(pcf_scores) / len(pcf_scores)

    # 2. occasionFit: TPO 태그 매칭
    user_tpo = user_profile["tpo"]
    matching_tags = sum(1 for item in outfit if user_tpo in item.tags)
    occasion_fit = (matching_tags / len(outfit)) * 100

    # 3. colorHarmony: 60-30-10 법칙
    color_harmony = calculate_color_harmony([item.color_hex for item in outfit])

    # 4. priceEfficiency: 예산 대비 효율
    total_price = sum(item.price for item in outfit)
    budget_max = user_profile["budget_max"]
    if total_price <= budget_max:
        price_efficiency = 100.0 - (total_price / budget_max) * 20  # 예산 내면 80~100
    else:
        overshoot = (total_price - budget_max) / budget_max
        price_efficiency = max(0, 80.0 - overshoot * 100)

    # 5. 가중합
    total = (
        personal_color_fit * WEIGHTS["personal_color_fit"]
        + occasion_fit * WEIGHTS["occasion_fit"]
        + color_harmony * WEIGHTS["color_harmony"]
        + price_efficiency * WEIGHTS["price_efficiency"]
    )

    # 6. 추천 이유 생성
    reasons = generate_reasons(personal_color_fit, occasion_fit, color_harmony,
                               user_profile, outfit)

    return OutfitScore(
        personal_color_fit=round(personal_color_fit, 1),
        occasion_fit=round(occasion_fit, 1),
        color_harmony=round(color_harmony, 1),
        price_efficiency=round(price_efficiency, 1),
        total_score=round(total, 1),
        reasons=reasons,
    )

def calculate_color_harmony(hex_colors: list[str]) -> float:
    """60-30-10 법칙 기반 색상 조화도"""
    if len(hex_colors) < 2:
        return 70.0
    rgbs = [hex_to_rgb(h) for h in hex_colors]
    hsls = [colorsys.rgb_to_hls(r/255, g/255, b/255) for r, g, b in rgbs]

    # 색상 간 명도/채도 차이가 적당하면 조화로움
    hue_spread = max(h[0] for h in hsls) - min(h[0] for h in hsls)
    if 0.05 < hue_spread < 0.35:   # 유사색 조합
        return 90.0
    elif hue_spread < 0.05:         # 톤온톤
        return 85.0
    elif 0.4 < hue_spread < 0.6:   # 보색 대비
        return 75.0
    else:
        return 65.0
```

### 5.6 메타데이터 스키마

```json
{
  "outfit_id": "outfit_2026_0001",
  "items": [
    {
      "product_id": "naver_12345",
      "category": "상의",
      "name": "소프트 라벤더 블라우스",
      "brand": "무신사 스탠다드",
      "color_hex": "#B0A6C6",
      "tone_id": "summer_cool_soft",
      "price": 32900,
      "mall_name": "무신사",
      "mall_url": "https://store.musinsa.com/...",
      "image_url": "https://image.musinsa.com/..."
    },
    {
      "product_id": "naver_67890",
      "category": "하의",
      "name": "아이보리 와이드 슬랙스",
      "color_hex": "#F5F0E8",
      "tone_id": "summer_cool_soft",
      "price": 45000,
      "mall_name": "W컨셉",
      "mall_url": "https://www.wconcept.co.kr/..."
    }
  ],
  "scores": {
    "personal_color_fit": 94.2,
    "occasion_fit": 88.0,
    "color_harmony": 90.5,
    "price_efficiency": 82.3,
    "total_score": 89.1
  },
  "reasons": [
    "여름쿨소프트 핵심 컬러 라벤더 계열로 피부톤이 밝아 보여요",
    "데이트 룩에 적합한 부드러운 실루엣 조합이에요"
  ],
  "tags": ["summer_cool", "date", "feminine", "spring_season"],
  "is_complete_outfit": true,
  "total_price": 77900,
  "lowest_total_price": 71200
}
```

---

## 6. 추천 엔진 상세 설계

### 6.1 코디 추천 파이프라인

| 단계 | 입력 | 처리 | 출력 |
|------|------|------|------|
| 1. Profile Load | 사용자 ID | DB에서 프로필 조회 | 톤, TPO, 예산, 무드, 반응 히스토리 |
| 2. Candidate Filter | 전체 코디 DB | 톤 범위 + TPO 태그 + 가격 범위 필터 | 후보 코디 200~500개 |
| 3. Scoring | 후보 코디 | 4축 스코어링 (PCF, OF, CH, PE) | 점수 부여된 코디 |
| 4. Re-ranking | 점수 코디 | 완성도 가산, dislike 제외, 다양성 | 정렬된 상위 50개 |
| 5. Reason Gen | 상위 코디 | 기여 요인 → 자연어 템플릿 | 코디 + 이유 2줄 |

### 6.2 유사 상품(Similar) 매칭

```python
def find_similar_products(product: NormalizedProduct, limit: int = 5) -> list[dict]:
    """카테고리 + 색상군 + 가격대 기반 유사 상품 검색"""
    candidates = db.query(Product).filter(
        Product.category == product.category,
        Product.product_id != product.product_id,
    ).all()

    scored = []
    for c in candidates:
        # 색상 유사도 (0~1)
        color_sim = 1.0 - color_distance(
            hex_to_rgb(product.color_hex),
            hex_to_rgb(c.color_hex)
        ) / 441.67  # max RGB distance = sqrt(255^2 * 3)

        # 가격 유사도
        price_ratio = min(product.price, c.price) / max(product.price, c.price)

        # 종합 유사도
        similarity = color_sim * 0.6 + price_ratio * 0.4

        match_type = "exact" if (
            c.name_normalized == product.name_normalized and c.brand == product.brand
        ) else "similar"

        scored.append({
            "product": c,
            "similarity": similarity,
            "match_type": match_type,
        })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:limit]
```

### 6.3 Top Pick 단일 추천

```python
def select_top_pick(saved_outfits: list[OutfitScore], user_profile: dict) -> dict:
    """저장 목록에서 종합 적합도 최고 1개 선정"""
    if not saved_outfits:
        # 저장 목록 비어있으면 전체 추천에서 Top 1
        return get_feed(user_profile, limit=1)[0]

    # 저장 코디 중 total_score 최고
    top = max(saved_outfits, key=lambda o: o.total_score)

    return {
        "outfit": top,
        "message": f"저장하신 {len(saved_outfits)}개 코디 중 가장 잘 어울리는 코디예요",
        "highlight_reason": top.reasons[0],
    }

def compare_ab(outfit_a: OutfitScore, outfit_b: OutfitScore) -> dict:
    """A vs B 비교 판정"""
    comparison = {
        "personal_color_fit": {"A": outfit_a.personal_color_fit, "B": outfit_b.personal_color_fit},
        "occasion_fit": {"A": outfit_a.occasion_fit, "B": outfit_b.occasion_fit},
        "price_efficiency": {"A": outfit_a.price_efficiency, "B": outfit_b.price_efficiency},
        "total": {"A": outfit_a.total_score, "B": outfit_b.total_score},
    }

    winner = "A" if outfit_a.total_score >= outfit_b.total_score else "B"
    winning_outfit = outfit_a if winner == "A" else outfit_b

    # 승리 이유: 가장 큰 차이를 보인 축
    diffs = {
        k: abs(v["A"] - v["B"]) for k, v in comparison.items() if k != "total"
    }
    key_factor = max(diffs, key=diffs.get)

    return {
        "comparison": comparison,
        "winner": winner,
        "reason": f"{key_factor} 점수에서 {winner}안이 더 높아요",
        "winning_outfit": winning_outfit,
    }
```

### 6.4 추천 이유 생성

```python
REASON_TEMPLATES = {
    "personal_color_fit": [
        "{tone_name} 핵심 컬러 {color_name} 계열로 피부톤이 밝아 보여요",
        "{tone_name}에 잘 어울리는 {color_name} 톤의 조합이에요",
    ],
    "occasion_fit": [
        "{tpo_name}에 적합한 {style_desc} 실루엣이에요",
        "{tpo_name} 분위기에 맞는 단정한 코디예요",
    ],
    "color_harmony": [
        "{color1}과 {color2}의 조화로운 톤온톤 매치예요",
        "60-30-10 비율로 균형 잡힌 색상 배합이에요",
    ],
    "price_efficiency": [
        "예산 {budget}만원 이내에서 최적의 조합이에요",
        "가성비 좋은 {brand} 아이템으로 구성했어요",
    ],
}

def generate_reasons(pcf, of, ch, profile, outfit) -> list[str]:
    """상위 2개 기여 요인을 자연어로 변환"""
    scores = {
        "personal_color_fit": pcf * WEIGHTS["personal_color_fit"],
        "occasion_fit": of * WEIGHTS["occasion_fit"],
        "color_harmony": ch * WEIGHTS["color_harmony"],
        "price_efficiency": outfit_price_eff * WEIGHTS["price_efficiency"],
    }

    top_2 = sorted(scores, key=scores.get, reverse=True)[:2]
    reasons = []
    for factor in top_2:
        template = REASON_TEMPLATES[factor][0]
        reason = template.format(
            tone_name=TONE_NAMES[profile["tone"]],
            color_name=get_dominant_color_name(outfit),
            tpo_name=TPO_NAMES[profile["tpo"]],
            style_desc=get_style_description(outfit),
            color1=get_color_name(outfit[0].color_hex),
            color2=get_color_name(outfit[1].color_hex) if len(outfit) > 1 else "",
            budget=profile["budget_max"] // 10000,
            brand=outfit[0].brand,
        )
        reasons.append(reason)

    return reasons
```

### 6.5 예상 성능

| 추천 방식 | 예상 CTR | 외부 링크 클릭율 | 비고 |
|----------|---------|----------------|------|
| 규칙 기반 (톤 필터만) | 8~12% | 5~8% | Baseline |
| 스코어링 (4축) | 15~20% | 10~14% | 개인화 효과 |
| 스코어링 + 리랭킹 | 18~25% | 12~18% | 다양성 + 완성도 가산 |
| Top Pick (1개 강추) | 30~40% | 20~30% | 결정 피로 해소 효과 |

---

## 7. 도메인 특화 기능 설계

### 7.1 퍼스널컬러 12-tone 매칭 시스템

#### 12-tone 분류 체계

| 시즌 | 톤 | 대표색 HEX | 특성 | 추천색 | 비추천색 |
|------|-----|-----------|------|--------|---------|
| 봄웜 | 라이트 | #FFCBA4 | 밝고 따뜻한 파스텔 | 코랄, 피치, 아이보리 | 검정, 네이비, 버건디 |
| 봄웜 | 브라이트 | #FF6B6B | 선명하고 화사한 | 레드 오렌지, 터콰이즈 | 카키, 머스타드 |
| 봄웜 | 뮤트 | #D4A574 | 부드럽고 따뜻한 중간톤 | 살몬, 웜 베이지 | 블루 그레이, 차콜 |
| 여름쿨 | 라이트 | #9FB5D4 | 밝고 시원한 파스텔 | 라벤더, 스카이블루 | 오렌지, 카키 |
| 여름쿨 | 소프트 | #B0A6C6 | 부드럽고 차분한 | 소프트 핑크, 라일락 | 비비드 레드, 골드 |
| 여름쿨 | 뮤트 | #8B8B9E | 차분하고 연한 | 로즈 그레이, 민트 | 오렌지, 카멜 |
| 가을웜 | 딥 | #8B5A2B | 깊고 풍부한 | 버건디, 테라코타 | 핫핑크, 네온 |
| 가을웜 | 뮤트 | #A0856C | 차분하고 자연스러운 | 올리브, 머스타드 | 파스텔 핑크, 라벤더 |
| 가을웜 | 브라이트 | #D4722A | 선명하고 따뜻한 | 오렌지, 터메릭 | 파스텔 블루, 실버 |
| 겨울쿨 | 딥 | #1E1E4E | 깊고 선명한 | 블랙, 로열블루 | 베이지, 카멜 |
| 겨울쿨 | 브라이트 | #CC0066 | 강렬하고 차가운 | 퓨시아, 에메랄드 | 브라운, 카키 |
| 겨울쿨 | 라이트 | #E0E0F0 | 밝고 차가운 | 아이시 핑크, 화이트 | 오렌지, 올리브 |

#### 상품 색상 → 톤 매핑 흐름도

```
상품 이미지
    │
    ▼
┌───────────────┐
│ 이미지 색상    │  ← PIL/OpenCV로 주요 색상 추출
│ 추출 (K-means) │    상위 3개 색상 클러스터
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ HEX → RGB     │
│ 변환           │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 12-tone 팔레트 │  ← 각 톤의 대표색과 유클리드 거리 계산
│ 거리 계산      │    가장 가까운 톤 선정
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ tone_id 태깅   │  → "summer_cool_soft"
│ + 적합 톤 리스트│  → ["summer_cool_light", "winter_cool_bright"]
└───────────────┘
```

### 7.2 TPO 기반 코디 큐레이션

| TPO | 설명 | 코디 특성 | 키워드 |
|-----|------|----------|--------|
| 출근 | 오피스 데일리 | 단정함, 비즈니스 캐주얼 | 블라우스, 슬랙스, 로퍼 |
| 미팅/면접 | 중요한 비즈니스 | 포멀, 신뢰감 | 재킷, 셔츠, 펌프스 |
| 소개팅/데이트 | 로맨틱, 첫인상 | 여성스러움/깔끔함, 포인트 컬러 | 원피스, 니트, 스커트 |
| 친구 모임 | 편하면서 세련된 | 캐주얼, 트렌디 | 데님, 스니커즈, 가디건 |
| 행사/하객 | 격식 있는 자리 | 포멀, 화려함 절제 | 셋업, 블라우스, 힐 |
| 여행 | 편안하고 활동적 | 캐주얼, 레이어드 | 바람막이, 편한 팬츠 |
| 주말 | 휴식, 동네 외출 | 편안함, 깔끔 | 맨투맨, 조거팬츠, 스니커즈 |
| 홈웨어 | 집에서 편하게 | 편안함 극대화 | 파자마, 라운지웨어 |

### 7.3 설명 가능한 추천 (Explainable Recommendation)

#### 추천 이유 3레이어

```
┌─────────────────────────────────────────┐
│ Layer 1: 색상 근거                        │
│ "여름쿨소프트 핵심 컬러 라벤더 계열이에요" │
├─────────────────────────────────────────┤
│ Layer 2: 피부톤 효과                      │
│ "차가운 보라 계열이 피부의 분홍기를 살려요" │
├─────────────────────────────────────────┤
│ Layer 3: 상황 적합성                      │
│ "데이트 룩에 어울리는 부드러운 실루엣이에요"│
└─────────────────────────────────────────┘
         ↓ (코디 카드에는 Layer 1+3만 노출)
         ↓ (상세 펼치기 시 3레이어 모두 노출)
```

#### 점수 뱃지 시각화

```
┌──────────────────────────┐
│  personalColorFit  94    │  ████████████████░░  (코랄 바)
│  occasionFit       88    │  ██████████████░░░░  (블루 바)
│  colorHarmony      91    │  █████████████████░  (퍼플 바)
│  priceEfficiency   82    │  █████████████░░░░░  (그린 바)
│  ─────────────────────── │
│  종합 점수         89.1  │  ★★★★☆
└──────────────────────────┘
```

### 7.4 가격 비교 & 유사 상품 시스템

#### 판매처별 가격 비교 테이블 구조

```
┌──────────────────────────────────────────────┐
│  소프트 라벤더 블라우스                         │
│  ─────────────────────────────────────────── │
│  판매처        가격        유형      링크      │
│  ─────────────────────────────────────────── │
│  무신사       ₩32,900    Exact    [바로가기]  │
│  W컨셉       ₩34,500    Exact    [바로가기]  │ ← 최저가 강조
│  29CM        ₩35,000    Exact    [바로가기]  │
│  ─────────────────────────────────────────── │
│  유사 상품 (Similar)                           │
│  ─────────────────────────────────────────── │
│  라일락 셔링 블라우스  ₩24,900  87% 유사  [보기]│
│  퍼플 린넨 블라우스    ₩19,900  82% 유사  [보기]│
└──────────────────────────────────────────────┘
```

---

## 8. UI/UX 설계

### 8.1 프레임워크 선정

| 기준 | Next.js 15 | React SPA | Vue 3 | Flutter Web |
|------|-----------|-----------|-------|-------------|
| SSR/SEO | O (App Router) | X (CSR) | O (Nuxt) | X |
| 모바일 성능 | 우수 (서버 컴포넌트) | 양호 | 양호 | 양호 |
| 생태계 | 최대 | 최대 | 중간 | 성장 중 |
| 팀 경험 | 높음 | 높음 | 중간 | 낮음 |
| **선정** | **채택** | — | — | — |

**선정 근거:** Next.js 15의 App Router + React Server Components로 초기 로딩 속도 최적화. 모바일 웹에서 체감 성능이 가장 중요한 B(바쁜이) 페르소나를 위해 SSR 필수.

### 8.2 온보딩 화면 와이어프레임

```
┌─────────────────────────────┐
│        Step 1 / 3            │
│    ● ○ ○  진행바             │
│                              │
│  내 퍼스널컬러를 알고 있나요?  │
│                              │
│  ┌─────┐ ┌─────┐ ┌─────┐   │
│  │봄웜  │ │봄웜  │ │봄웜  │   │
│  │라이트│ │브라이│ │뮤트  │   │
│  │ 🟡  │ │ 🟠  │ │ 🟤  │   │
│  └─────┘ └─────┘ └─────┘   │
│  ┌─────┐ ┌─────┐ ┌─────┐   │
│  │여름쿨│ │여름쿨│ │여름쿨│   │
│  │라이트│ │소프트│ │뮤트  │   │
│  │ 🔵  │ │ 🟣  │ │ ⚪  │   │
│  └─────┘ └─────┘ └─────┘   │
│  ┌─────┐ ┌─────┐ ┌─────┐   │
│  │가을웜│ │가을웜│ │가을웜│   │
│  │딥   │ │뮤트  │ │브라이│   │
│  │ 🟫  │ │ 🫒  │ │ 🧡  │   │
│  └─────┘ └─────┘ └─────┘   │
│  ┌─────┐ ┌─────┐ ┌─────┐   │
│  │겨울쿨│ │겨울쿨│ │겨울쿨│   │
│  │딥   │ │브라이│ │라이트│   │
│  │ ⚫  │ │ 💜  │ │ 🤍  │   │
│  └─────┘ └─────┘ └─────┘   │
│                              │
│  [ 잘 모르겠어요 → 도움말 ]   │
│                              │
│       [ 다음 → ]             │
└─────────────────────────────┘
```

### 8.3 코디 피드 화면 와이어프레임

```
┌─────────────────────────────┐
│  ColorFit        🔔  👤     │
│─────────────────────────────│
│ [출근] [데이트] [주말] [행사] │  ← TPO 탭
│─────────────────────────────│
│  예산: ₩3만 ──●────── ₩10만 │  ← 예산 슬라이더
│─────────────────────────────│
│                              │
│  ┌─────────────────────┐    │
│  │  [코디 이미지]        │    │
│  │                      │    │
│  │  여름쿨소프트 데이트룩  │    │
│  │  라벤더 블라우스 +     │    │  ← 1줄 요약
│  │  아이보리 슬랙스       │    │
│  │                      │    │
│  │  "핵심 컬러 라벤더 계열│    │  ← 추천 이유
│  │   로 피부톤이 밝아요"  │    │
│  │                      │    │
│  │  ₩77,900  PCF 94     │    │  ← 가격 + 점수
│  │                      │    │
│  │  [♡ 저장]    [✕ 넘기기]│    │
│  └─────────────────────┘    │
│                              │
│  ┌─────────────────────┐    │
│  │  [다음 코디 카드]      │    │
│  │  ...                  │    │
│  └─────────────────────┘    │
│                              │
│ ──── ──── ──── ──── ────    │
│  홈   피드  저장  Top  마이   │  ← 하단 탭바
└─────────────────────────────┘
```

### 8.4 코디 상세 화면 와이어프레임

```
┌─────────────────────────────┐
│  ← 뒤로                     │
│─────────────────────────────│
│                              │
│     [코디 전체 이미지]        │
│                              │
│─────────────────────────────│
│  추천 이유                    │
│  ────────                    │
│  🎨 여름쿨소프트 핵심 컬러    │
│     라벤더 계열               │
│  👗 데이트 룩에 적합한        │
│     부드러운 실루엣           │
│  [상세 보기 ▼]               │
│─────────────────────────────│
│  점수                        │
│  PCF ████████████░░ 94      │
│  OF  ██████████░░░░ 88      │
│─────────────────────────────│
│  아이템 구성                  │
│  ←  [블라우스]  [슬랙스]  →  │  ← 캐러셀
│      ₩32,900    ₩45,000     │
│    [가격비교]   [가격비교]    │
│─────────────────────────────│
│  코디 합계: ₩77,900          │
│  최저가 합계: ₩71,200        │
│─────────────────────────────│
│                              │
│  [♡ 저장]  [A vs B 비교]     │
│                              │
└─────────────────────────────┘
```

### 8.5 모바일 최적화 설계 원칙

| 원칙 | 구현 |
|------|------|
| 터치 타겟 최소 48px | 모든 버튼/링크 48×48px 이상 |
| 3초 이내 피드 로딩 | 이미지 lazy loading + WebP + CDN |
| 스와이프 제스처 | 코디 카드 좌/우 스와이프 = dislike/save |
| 원핸드 사용 | 하단 탭바 + 엄지 닿는 범위에 핵심 액션 |
| 오프라인 대응 | 마지막 조회 피드 캐시 (Service Worker) |

---

## 9. 사용자 시나리오 및 대화 흐름

### 시나리오 1: A 진단러 — 소개팅 룩 찾기

```
김지은(25세, 여름쿨소프트)이 내일 소개팅을 앞두고 ColorFit을 연다.

1. [홈 화면] 자동 로그인 → 여름쿨소프트 프로필 로드
2. [TPO 탭] "데이트" 탭 선택
3. [코디 피드] 여름쿨 팔레트 기반 데이트룩 코디 노출
   → 첫 번째 코디: 라벤더 블라우스 + 아이보리 와이드 슬랙스
   → 카드 하단: "여름쿨소프트 핵심 컬러 라벤더 계열로 피부톤이 밝아 보여요"
   → PCF 94 / OF 88
4. [코디 상세] 카드 탭 → 상세 진입
   → 아이템별 가격: 블라우스 ₩32,900 / 슬랙스 ₩45,000
   → 코디 합계: ₩77,900
5. [가격 비교] 블라우스 → 무신사 ₩32,900 / W컨셉 ₩34,500
   → "무신사에서 보기" 탭 → 외부 이동
6. [구매 완료 후 복귀] "이 추천이 도움이 됐나요?" → [👍 구매했어요]
```

### 시나리오 2: B 바쁜이 — 출퇴근 5분 코디

```
박민준(32세, 가을웜딥)이 출근 지하철에서 5분 틈새 시간에 ColorFit을 연다.

1. [홈 화면] 자동 로그인 → 가을웜딥 프로필 로드 → 즉시 피드 노출
2. [TPO 탭] "출근" 탭 (기본값)
3. [빠른 스캔] 코디 카드를 빠르게 훑음
   → 첫 번째 코디: 차콜 재킷 + 버건디 니트 + 네이비 슬랙스
   → 1줄 요약: "가을웜딥 핵심 딥톤 조합, 출근룩 완성"
   → 스와이프 왼쪽 = dislike → 다음 코디
   → 두 번째 코디 마음에 듦 → ♡ 저장
4. [반복] 2개 더 스캔 → 1개 추가 저장
5. [퇴근 후] 저장 목록 진입 → 상세 확인 → 가격 비교 → 구매

총 소요 시간: 3분 이내
```

### 시나리오 3: B 바쁜이 — 미팅 전날 급하게

```
박민준이 내일 중요 미팅 앞두고 저녁에 ColorFit을 연다.

1. [예산 변경] 슬라이더를 20만원으로 조정
2. [TPO 전환] "미팅/면접" 탭 선택
3. [피드] isCompleteOutfit 우선 → 상하의+아우터 완성 코디 먼저
   → "차콜 수트 셋업 + 화이트 셔츠" / 총 ₩178,000
   → PCF 91 / OF 96
4. [코디 합계] "총 ₩178,000, 예산 내 OK"
5. [즉시 결정] 외부 링크 → 바로 구매
```

### 시나리오 4: C 탐색러 — 저렴한 버전 찾기

```
이서연(22세, 봄웜라이트)이 마음에 드는 코디를 발견하지만 가격이 25만원.

1. [코디 상세] "코랄 트위드 자켓 + 크림 니트 + 베이지 슬랙스" / ₩253,000
2. [예산 재설정] 슬라이더를 10만원 이내로 변경
3. [유사 코디 재구성] 동일 톤/무드 유지 + 저가 아이템
   → "코랄 가디건 + 아이보리 티 + 베이지 팬츠" / ₩82,000
   → 유사도 87%
4. [아이템별 Similar] 코랄 가디건 → 3개 대안 (₩24,900 ~ ₩35,000)
5. [최저가 선택] → 외부 링크 → 구매
```

### 시나리오 5: D 결정 피로형 — Top Pick

```
최수빈(28세, 여름쿨뮤트)이 저장한 코디 12개 중 뭘 살지 모름.

1. [저장 목록] 12개 코디 나열
2. [Top Pick 버튼] 탭
3. [결과] "12개 코디 중 수빈님께 가장 잘 어울리는 코디예요"
   → 여름쿨뮤트 최적 코디 1개 강조
   → "로즈 그레이 니트가 여름쿨뮤트의 차분한 매력을 살려요"
4. [확신] → 바로 구매 결정
```

### 시나리오 6: D 결정 피로형 — A vs B 비교

```
최수빈이 2개 코디 사이에서 고민 중.

1. [저장 목록] 코디 A, B 각각 체크
2. [A vs B 비교] 버튼 탭
3. [비교 화면]
   │            A안           │         B안          │
   │ PCF       92            │ PCF      78          │
   │ OF        88            │ OF       91          │
   │ 가격    ₩89,000         │ 가격   ₩72,000       │
   │ 종합      87.5          │ 종합     82.3         │
4. [판정] "A안이 색상 적합도에서 더 높아요" → A안 결정
```

### 시나리오 7: A 진단러 — 톤 헷갈릴 때

```
김지은이 여름쿨소프트가 정확히 뭔지 헷갈림.

1. [마이페이지] → "내 퍼스널컬러" 탭
2. [톤 설명 화면]
   → 여름쿨소프트: "차갑고 부드러운 색이 피부를 투명하게 만들어요"
   → 대표색 스와치: 라벤더, 소프트 핑크, 로즈 그레이, 파우더 블루
   → 추천색 vs 비추천색 비교 팔레트
3. [확인] "맞는 것 같아" → 피드로 돌아감
   또는 "다른 것 같아" → [톤 재선택] → 온보딩 수정
```

### 시나리오 8: C 탐색러 — 색상 조합 공부

```
이서연이 추천된 코디의 색상 조합이 왜 예쁜지 알고 싶음.

1. [코디 카드] "추천 이유 상세 ▼" 펼치기
2. [3레이어 노출]
   🎨 색상 근거: "봄웜라이트 핵심 컬러 코랄 + 아이보리 톤온톤"
   💆 피부톤 효과: "따뜻한 코랄이 봄웜 피부의 생기를 살려요"
   👗 상황 적합성: "데이트 분위기에 맞는 부드러운 A라인"
3. [점수 뱃지] PCF 94 / OF 88 / CH 91 / PE 82
4. [학습 효과] "아, 코랄이랑 아이보리가 이래서 잘 어울리는 거구나"
```

### 9.2 사용자 행동 유형 분류

| 유형 | 예시 행동 | 예상 빈도 | 핵심 기능 |
|------|----------|----------|----------|
| 코디 탐색 | 피드 스크롤, TPO 전환 | 40% | 코디 피드, TPO 탭 |
| 가격 비교 | 아이템 상세 → 판매처 비교 | 20% | 가격 비교, 외부 링크 |
| 저장/관리 | save, 저장 목록 조회 | 15% | save, 저장 목록 |
| 추천 이유 확인 | reasons 펼치기, 점수 확인 | 10% | 추천 이유, 점수 뱃지 |
| 결정 지원 | Top Pick, A vs B | 8% | Top Pick, 비교 |
| 프로필 관리 | 톤 변경, 예산 조정 | 5% | 온보딩 수정, 슬라이더 |
| dislike | 스와이프/버튼 넘기기 | 2% | dislike |

---

## 10. 전체 기능 리스트

### 10.1 MVP 기능 (4주) — 31개

| # | 기능 | 설명 | 출처 | 담당 |
|---|------|------|------|------|
| F-01 | 12-tone 팔레트 선택 온보딩 | 스와치 카드로 직접 선택 | A | FE |
| F-02 | 스타일 무드 멀티 선택 | 캐주얼·미니멀·러블리 등 복수 선택 | A,C | FE |
| F-03 | TPO 선택 (8종) | 출근/소개팅/면접/모임/행사/여행/주말/홈웨어 | A,B | FE |
| F-04 | 예산 슬라이더 (min/max) | 아이템당 예산 범위 설정 | B | FE |
| F-05 | 퍼스널컬러 톤 설명 화면 | 톤 특성·대표색·추천/비추천색 안내 | A | FE |
| F-06 | 코디 피드 (개인화 정렬) | 스코어링 기반 피드 | ALL | FE+BE |
| F-07 | 코디 카드 1줄 요약 | 색상·가격대·이유 1줄 표시 | B | FE |
| F-08 | TPO 탭 빠른 전환 | 피드 상단 탭으로 TPO 즉시 변경 | B | FE |
| F-09 | 코디 상세 (아이템 캐러셀) | 전체 룩 + 개별 아이템 상세 | ALL | FE |
| F-10 | 추천 이유 표시 (reasons 2줄) | 상위 2개 기여 요인 자연어 | A,B,D | BE |
| F-11 | 점수 뱃지 시각화 | PCF / OF 바 차트 | A | FE |
| F-12 | 아이템 단품 상세 진입 | 코디 → 단품 페이지 이동 | C | FE |
| F-13 | 판매처별 가격 비교 | 여러 쇼핑몰 가격 나란히 비교 | A,B,C | BE+FE |
| F-14 | Exact / Similar 구분 표시 | 동일 상품 vs 유사 상품 구분 | B | BE |
| F-15 | 유사 상품 (Similar) 목록 | 카테고리·색상 기반 대체재 | B,C | BE |
| F-16 | 최저가 외부 링크 | 외부 쇼핑몰 이동 | ALL | FE |
| F-17 | save (저장) | 나중에 보기용 찜 | B,C,D | FE+BE |
| F-18 | dislike (싫어요 + 피드 즉시 제외) | 싫어요 시 해당 코디 제외 | B,C | FE+BE |
| F-19 | 추천 이유 열람 이벤트 로깅 | view_reason 이벤트 수집 | A | BE |
| F-20 | 코디 전체 최저가 합산 | 아이템별 최저가 합산 표시 | B | BE |
| F-21 | isCompleteOutfit 우선 정렬 | 완성 코디 먼저 노출 | B | BE |
| F-22 | 예산 빠른 변경 | 피드에서 슬라이더 즉시 조정 | B | FE |
| F-23 | 시즌 태그 필터 | 봄/여름/가을/겨울 키워드 | C | FE |
| F-24 | lastObservedAt 표시 | 상품 최종 확인 시점 | A,B | BE |
| F-25 | 온보딩 수정 (프로필 재설정) | 톤·TPO 재설정 | A | FE |
| F-26 | Top Pick 단일 추천 | 저장 중 최고 적합도 1개 강추 | D | BE |
| F-27 | A vs B 비교 판정 | 두 코디 나란히 비교 | B,D | FE+BE |
| F-28 | One-shot 추천 | 오늘의 룩 즉시 제시 | B,D | BE |
| F-29 | 추천 이유 3레이어 상세 | 색상 근거+피부톤+상황 | A,C | BE |
| F-30 | 구매 후 피드백 수집 | 👍/🤔/👎 + 이유 태그 | A,B | FE+BE |
| F-31 | 진단 결과 카드 | 캐릭터 타입명 + 팔레트 | A | FE |

### 10.2 Phase 2 (~6개월) — 주요 기능

| # | 기능 | 출처 |
|---|------|------|
| F-32 | 저장 목록 조회 + 폴더 분류 | B,C,D |
| F-33 | 가격 알림 (목표가 설정) | B,C |
| F-34 | 저장 기반 취향 학습 | C,D |
| F-35 | 트렌드 태그 필터 | C |
| F-36 | AI 셀카 퍼스널컬러 진단 | E |
| F-37 | 날씨 연동 "오늘의 코디" | F |
| F-38 | 스타일 카드 SNS 공유 | G |
| F-39 | 보유 옷 역방향 추천 | H |
| F-40 | 풀세팅 패키지 모드 | I |

### 10.3 Phase 3 (장기)

| # | 기능 | 출처 |
|---|------|------|
| F-41 | AI 가상 피팅 시뮬레이터 | H |
| F-42 | 코디 캘린더 (착용 기록) | B |
| F-43 | 커뮤니티 피드 | G |
| F-44 | B2B API (외부 연동) | — |
| F-45 | 유료 스타일 리포트 | — |

### 10.4 페르소나별 핵심 기능 매핑

```
A. 진단러 (김지은)     → F-01 F-05 F-10 F-11 F-25 F-29 F-31    "왜 나에게 맞는지 설명"
B. 바쁜이 (박민준)     → F-07 F-08 F-13 F-20 F-21 F-27 F-28    "빠른 결정 + 가격 확신"
C. 탐색러 (이서연)     → F-02 F-12 F-15 F-18 F-23 F-29          "다양한 탐색 + 저가 대체재"
D. 결정피로 (최수빈)   → F-26 F-27 F-28 F-17                     "1개 강추로 결정 피로 제거"
```

---

## 11. 진단(온보딩) 설계 상세

### 11.1 랜딩 페이지

| 요소 | 내용 |
|------|------|
| 헤드라인 | "내 색을 아는 순간, 선택이 쉬워진다" |
| 서브카피 | "어울리는 이유까지, 컬러핏이 골라줄게요" |
| CTA | [무료로 시작하기] — 로그인 없이 바로 온보딩 진입 |
| 하단 소셜 프루프 | "3,000명이 컬러핏으로 선택했어요" |

### 11.2 진단 3 Step

**Step 1: 퍼스널컬러 설정 (~30초)**
- 이미 아는 사람 → 12-tone 스와치 그리드에서 1탭 선택
- 모르는 사람 → "잘 모르겠어요" → 2문항 간이 진단
  - Q1: "피부톤에 가장 가까운 이미지를 골라주세요" (봄웜/여름쿨/가을웜/겨울쿨)
  - Q2: "평소 자주 입는 상의 색 계열은?" (베이직/어스톤/파스텔/비비드)
- 선택 후 대표색 팔레트 프리뷰 → "이 색들이 나에게 어울리나요?" 확인

**Step 2: TPO & 스타일 무드 (~15초)**
- TPO 2개 선택 (최대 3개): 버튼 탭 방식, 텍스트 입력 없음
- 스타일 무드 복수 선택: [캐주얼] [미니멀] [러블리] [클래식] [스트릿] [에디토리얼]

**Step 3: 예산 (~10초)**
- 듀얼 슬라이더 (min ~ max)
- 또는 빠른 선택: [~3만] [3~5만] [5~10만] [10만+]

### 11.3 이탈 방지 전략

| 전략 | 구현 |
|------|------|
| 게스트 체험 | 로그인 없이 온보딩+피드 1회 체험 가능 |
| 프로그레스 바 | "Step 1/3" 표시 → 끝이 보이는 안심감 |
| 스킵 옵션 | "나중에 설정할래요" → 기본값(봄웜 라이트)으로 진입 |
| 결과 즉시 보상 | 온보딩 완료 즉시 "나에게 맞는 코디 3개" 노출 |

### 11.4 재방문 사용자 플로우

```
앱 실행 → 토큰 확인 → 자동 로그인
  → "민준님, 다시 오셨네요"
  → 이전 프로필(가을웜딥, 출근, 5~15만원) 자동 로드
  → [새 추천 받기] [저장한 코디 보기]
  → 바로 피드 진입 (온보딩 스킵)
```

---

## 12. 평가 계획

### 12.1 추천 품질 메트릭

| 메트릭 | 설명 | 목표값 |
|--------|------|--------|
| CTR (클릭율) | 코디 카드 노출 → 상세 진입 | ≥ 20% |
| 추천 이유 열람율 | 코디 상세 → reasons 펼치기 | ≥ 50% |
| 외부 링크 전환율 | 아이템 상세 → 외부 쇼핑몰 이동 | ≥ 15% |
| save율 | 코디 노출 → 저장 | ≥ 10% |
| dislike율 | 코디 노출 → 싫어요 | ≤ 15% |

### 12.2 평가 데이터셋

| 구성 | 규모 | 설명 |
|------|------|------|
| 코디-평가 쌍 | 400개 | 100 코디 × 4 TPO |
| 전문가 평가 | 50개 코디 | 퍼스널컬러 전문가 2인 매칭 정확도 평가 |
| 사용자 테스트 | 20명 | 5분 자유 탐색 + SUS 설문 + 인터뷰 |

### 12.3 비교 실험 설계

| # | 실험 | 독립변수 | 종속변수 | 가설 |
|---|------|---------|---------|------|
| E1 | 추천 방식 | 규칙 기반 vs 스코어링 vs 스코어링+리랭킹 | CTR, save율 | 스코어링+리랭킹이 가장 높다 |
| E2 | 추천 이유 유무 | 이유 있음 vs 없음 | 외부 링크 클릭율 | 이유 있을 때 15%+ 높다 |
| E3 | 가격 비교 유무 | 가격 비교 있음 vs 없음 | 전환율 | 가격 비교 시 전환율 높다 |
| E4 | Top Pick 유무 | 일반 피드 vs Top Pick | 결정 시간, 구매율 | Top Pick 시 결정 빠르다 |

### 12.4 사용자 경험 평가

- **SUS (System Usability Scale):** 목표 ≥ 75점 (양호)
- **인터뷰 핵심 질문:**
  - "추천 이유가 구매 결정에 도움이 됐나요?"
  - "퍼스널컬러 기반 추천이 기존 쇼핑 앱과 어떻게 다르게 느껴졌나요?"
  - "Top Pick 기능이 결정을 쉽게 만들었나요?"

---

## 13. 구현 로드맵

### 13.1 간트 차트

```
         W1          W2          W3          W4          W5
      3/24-3/28   3/31-4/4    4/7-4/11   4/14-4/18   4/21-4/25
      ─────────  ─────────  ─────────  ─────────  ─────────
데이터  ████████
수집    ████████

온보딩  ░░██████  ████████
UI

추천              ████████  ████████
엔진

코디 피드          ████████  ████████
UI

가격 비교                    ████████  ████████

결정 지원                              ████████
(Top Pick)

통합 테스트                            ████████  ████████

버그 수정                                        ████████
발표 준비                                        ████████
```

### 13.2 주차별 상세

| 주차 | 작업 | 산출물 |
|------|------|--------|
| **W1** | 데이터 수집 (네이버 쇼핑 API + 크롤링) + DB 구축 + 12-tone 팔레트 세팅 + 온보딩 UI 시작 | 상품 DB 20,000건, 온보딩 Step 1 화면 |
| **W2** | 추천 엔진 코어 (스코어링 4축 + 필터 + 리랭킹) + 코디 피드 UI + 추천 이유 생성 | 코디 피드 동작, 추천 이유 2줄 노출 |
| **W3** | 가격 비교 기능 + 유사 상품(Similar) + 아이템 상세 + Exact/Similar 구분 | 가격 비교 테이블, 유사 상품 목록 |
| **W4** | Top Pick + A vs B 비교 + One-shot + 통합 테스트 + 버그 수정 | 결정 지원 기능 완성, 전체 플로우 테스트 |
| **W5** | 최종 버그 수정 + 성능 최적화 + 발표 자료 작성 + 데모 준비 | 발표 자료, 데모 영상 |

### 13.3 마일스톤

| # | 마일스톤 | 시점 | 완료 기준 |
|---|---------|------|----------|
| M1 | 데이터 수집 완료 | W1 금 | 상품 DB 20,000건 + 12-tone 팔레트 |
| M2 | 온보딩 플로우 완성 | W2 월 | 3 Step 온보딩 → 피드 진입 |
| M3 | 추천 엔진 v1 | W2 금 | 스코어링 기반 코디 피드 동작 |
| M4 | 가격 비교 완성 | W3 금 | Exact/Similar + 외부 링크 |
| M5 | 전체 MVP 완성 | W4 금 | Top Pick + 통합 테스트 통과 |
| M6 | 발표 준비 완료 | W5 목 | 발표 자료 + 데모 |

---

## 14. 기술 스택 상세

### 14.1 기술 스택 다이어그램

```
┌─────────────────────────────────────────────┐
│  Client Layer                                │
│  Next.js 15.2 + React 19 + TypeScript 5.6   │
│  TailwindCSS 4.0 + Framer Motion 11         │
├─────────────────────────────────────────────┤
│  CDN / Hosting                               │
│  Vercel (프론트) + Cloudflare Images (이미지) │
├─────────────────────────────────────────────┤
│  API Layer                                   │
│  Python 3.13 + FastAPI 0.115 + Uvicorn       │
│  Pydantic v2 + SQLAlchemy 2.0                │
├─────────────────────────────────────────────┤
│  Logic Layer                                 │
│  NumPy 2.2 (색상 계산) + Pillow 11 (이미지)   │
│  scikit-learn 1.6 (색상 클러스터링)            │
├─────────────────────────────────────────────┤
│  Data Layer                                  │
│  PostgreSQL 17 + Redis 7.4 (캐시)            │
│  Supabase (호스팅) 또는 Railway              │
└─────────────────────────────────────────────┘
```

### 14.2 핵심 라이브러리

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| Next.js | 15.2 | SSR + App Router + React Server Components |
| React | 19 | UI 렌더링 |
| TypeScript | 5.6 | 타입 안전성 |
| TailwindCSS | 4.0 | 유틸리티 기반 스타일링 |
| Framer Motion | 11 | 스와이프/전환 애니메이션 |
| FastAPI | 0.115 | REST API 서버 |
| Pydantic | 2.10 | 데이터 검증 |
| SQLAlchemy | 2.0 | ORM |
| httpx | 0.28 | 비동기 HTTP 클라이언트 |
| Pillow | 11.1 | 이미지 색상 추출 |
| NumPy | 2.2 | 색상 거리 계산 |
| scikit-learn | 1.6 | K-means 색상 클러스터링 |
| Redis | 7.4 | 피드 캐싱 |
| PostgreSQL | 17 | 메인 DB |

### 14.3 API 엔드포인트 설계

| Method | Endpoint | 설명 | 응답 |
|--------|----------|------|------|
| POST | `/api/onboarding` | 온보딩 프로필 저장 | 사용자 프로필 |
| GET | `/api/feed` | 코디 피드 조회 | 코디 리스트 + 스코어 + 이유 |
| GET | `/api/outfit/{id}` | 코디 상세 | 코디 + 아이템 + 점수 상세 |
| GET | `/api/item/{id}` | 아이템 상세 | 아이템 + 판매처 가격 |
| GET | `/api/item/{id}/similar` | 유사 상품 | Similar 리스트 |
| POST | `/api/reaction` | save / dislike | 반응 저장 |
| GET | `/api/saved` | 저장 목록 | 저장한 코디 리스트 |
| GET | `/api/top-pick` | Top Pick | 최적 1개 코디 |
| POST | `/api/compare` | A vs B 비교 | 비교 결과 + 판정 |
| GET | `/api/tone/{id}` | 톤 설명 | 톤 상세 정보 |

### 14.4 DB 스키마 개요

```sql
-- 사용자
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255),
    provider VARCHAR(20),          -- kakao, google
    tone_id VARCHAR(30),           -- summer_cool_soft
    tpo_primary VARCHAR(20),
    tpo_secondary VARCHAR(20),
    style_moods TEXT[],            -- {casual, minimal}
    budget_min INT,
    budget_max INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 상품
CREATE TABLE products (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(500),
    brand VARCHAR(100),
    category VARCHAR(20),          -- top, bottom, outer, onepiece, shoes, bag
    color_hex VARCHAR(7),
    tone_id VARCHAR(30),
    price INT,
    mall_name VARCHAR(50),
    mall_url TEXT,
    image_url TEXT,
    tags TEXT[],
    last_observed_at TIMESTAMPTZ
);

-- 코디
CREATE TABLE outfits (
    id VARCHAR(50) PRIMARY KEY,
    item_ids TEXT[],               -- product IDs
    total_price INT,
    lowest_total_price INT,
    is_complete_outfit BOOLEAN,
    tags TEXT[],
    scores JSONB,                  -- {pcf, of, ch, pe, total}
    reasons TEXT[]
);

-- 사용자 반응
CREATE TABLE reactions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    outfit_id VARCHAR(50) REFERENCES outfits(id),
    reaction_type VARCHAR(10),     -- save, dislike, click, purchase
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 14.5 배포 구성

| 컴포넌트 | 호스팅 | 비용 (월) |
|---------|--------|----------|
| 프론트엔드 (Next.js) | Vercel Free/Pro | $0~$20 |
| 백엔드 (FastAPI) | Railway | $5~$10 |
| DB (PostgreSQL) | Supabase Free | $0 |
| 캐시 (Redis) | Upstash Free | $0 |
| 이미지 CDN | Cloudflare Free | $0 |
| **합계** | | **$5~$30/월** |

---

## 15. 비즈니스 모델 & GTM 전략

### 15.1 수익 모델

| Phase | 수익원 | 설명 | 예상 수익 |
|-------|--------|------|----------|
| Phase 1 (MVP) | 제휴 커머스 수수료 | 외부 쇼핑몰 클릭/구매 CPA/CPS | 클릭당 ₩50~200 |
| Phase 2 | 프리미엄 구독 | 1:1 채팅, 디지털 옷장, 실시간 특가 알림 | ₩4,900/월 |
| Phase 2 | B2B 광고 | 타겟팅 유저 대상 브랜드 기획전 노출 | CPM 기반 |
| Phase 3 | Style Intelligence API | 외부 커머스를 위한 AI 추천 SaaS | 호출당 과금 |

### 15.2 GTM 퍼널

| Stage | Core Message | Product Role |
|-------|-------------|-------------|
| Discovery | "내 톤에 맞는 실패 없는 룩 찾기" | 1분 진단 테스트 기반 유입 |
| Conversion | "이 무드, 내 예산으로 맞춰볼까?" | 유사 코디 + 가격 비교로 구매 전환 |
| Retention | "시즌별 내 옷장 스마트 캐디" | 계절 변화·행사 시 맞춤 알림 |

### 15.3 유입 채널

| 채널 | 전략 | 예시 |
|------|------|------|
| Organic Content | 숏폼 바이럴 (릴스/틱톡) | "봄웜라이트를 위한 10만원 이하 하객룩 풀세팅" |
| Interactive Tool | 1분 퍼스널 스타일 진단 | 결과 카드 공유 → 바이럴 유입 |
| Social Proof | 스타일 카드 공유 유도 | #컬러핏 #내색찾기 해시태그 |

---

## 16. 리스크 관리 및 대응 전략

### 16.1 기술적 리스크

| 리스크 | 확률 | 영향 | 대응 전략 |
|--------|------|------|----------|
| 네이버 쇼핑 API 호출 제한 | 높음 | 높음 | 캐싱 적극 활용 + 수집 데이터 선 저장 + 호출 최적화 |
| 퍼스널컬러-상품 색상 매칭 정확도 낮음 | 중간 | 높음 | 전문가 검수 50개 + 매핑 알고리즘 반복 튜닝 |
| 코디 조합 품질 부족 | 중간 | 높음 | 전문가 큐레이션 시드 데이터 200개 + 룰 기반 보정 |
| 추천 이유 부자연스러움 | 중간 | 중간 | 템플릿 다양화 (톤별 20개+) + 사용자 테스트 피드백 |
| 모바일 성능 저하 | 낮음 | 높음 | 이미지 최적화 + 무한 스크롤 가상화 + CDN |
| 외부 쇼핑몰 링크 유효성 | 높음 | 낮음 | lastObservedAt 주기 갱신 + 깨진 링크 자동 감지 |

### 16.2 일정 리스크

| 리스크 | 확률 | 대응 |
|--------|------|------|
| 데이터 수집 지연 (API 제한) | 중간 | W1에 집중 수집 + 부족 시 샘플 데이터로 대체 |
| 추천 엔진 개발 복잡도 | 중간 | W2에 단순 규칙 기반 v0.5 우선 + 이후 스코어링 고도화 |
| UI 완성도 부족 | 낮음 | 핵심 화면(피드+상세) 우선 + 나머지는 최소 UI |
| 팀원 일정 충돌 | 낮음 | 주 2회 스탠드업 + 슬랙 비동기 업데이트 |

### 16.3 MVP 전략 (우선순위)

| 우선순위 | 기능 |
|---------|------|
| **필수 (Must)** | 온보딩, 코디 피드, 추천 이유 2줄, 가격 비교, save/dislike, 외부 링크 |
| **우선순위 2 (Should)** | Top Pick, A vs B, One-shot, 점수 뱃지, Exact/Similar 구분 |
| **우선순위 3 (Could)** | 추천 이유 3레이어 상세, 시즌 필터, 구매 후 피드백, 진단 결과 카드 |

---

## 17. 윤리적 고려사항

### 17.1 데이터 라이선스

| 소스 | 라이선스 | 준수 사항 |
|------|---------|----------|
| 네이버 쇼핑 API | 네이버 개발자 이용약관 | 상업적 이용 제한 확인, 호출 제한 준수 |
| 무신사/W컨셉 크롤링 | robots.txt 준수 | 크롤링 간격 준수, 캐싱 최소화, 원본 출처 명시 |
| 퍼스널컬러 팔레트 | 공개 색채학 자료 | 출처 명시 |

### 17.2 개인정보 보호

- 퍼스널컬러 데이터는 서비스 추천 목적으로만 사용
- 저장/반응 데이터는 사용자 동의 하에 추천 개선에 활용
- 계정 삭제 시 모든 개인 데이터 즉시 삭제 (Phase 2)
- 소셜 로그인 시 최소 정보만 요청 (이메일, 닉네임)

### 17.3 추천의 투명성

- 모든 코디 추천에 반드시 추천 이유(reasons) 표시
- 광고/제휴 상품은 "광고" 라벨 명시
- 스코어링 기준(4축 가중치) 공개 가능

### 17.4 체형/외모 민감성

- "어울리지 않는다"는 부정적 표현 배제
- "이 색상이 더 잘 어울려요"로 긍정적 대안 제시
- 체형 관련 표현 없음 (퍼스널컬러 = 색상 중심)
- 모든 성별/체형에 포용적인 언어 사용

---

## 18. 부록

### 18.1 네이버 쇼핑 API 응답 예시

```json
{
  "lastBuildDate": "Sun, 23 Mar 2026 14:00:00 +0900",
  "total": 1234567,
  "start": 1,
  "display": 10,
  "items": [
    {
      "title": "무신사 스탠다드 <b>라벤더</b> 블라우스",
      "link": "https://search.shopping.naver.com/...",
      "image": "https://shopping-phinf.pstatic.net/...",
      "lprice": "32900",
      "hprice": "0",
      "mallName": "무신사",
      "productId": "12345678",
      "productType": "1",
      "brand": "무신사 스탠다드",
      "maker": "",
      "category1": "패션의류",
      "category2": "여성의류",
      "category3": "블라우스/셔츠",
      "category4": ""
    }
  ]
}
```

### 18.2 프로젝트 디렉토리 구조

```
colorfit/
├── frontend/                    # Next.js 15
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # 랜딩
│   │   ├── onboarding/
│   │   │   ├── step1/page.tsx   # 퍼스널컬러 선택
│   │   │   ├── step2/page.tsx   # TPO + 무드
│   │   │   └── step3/page.tsx   # 예산
│   │   ├── feed/page.tsx        # 코디 피드
│   │   ├── outfit/[id]/page.tsx # 코디 상세
│   │   ├── item/[id]/page.tsx   # 아이템 상세
│   │   ├── saved/page.tsx       # 저장 목록
│   │   ├── compare/page.tsx     # A vs B 비교
│   │   └── profile/page.tsx     # 마이페이지
│   ├── components/
│   │   ├── OutfitCard.tsx
│   │   ├── ToneSwatchGrid.tsx
│   │   ├── ScoreBadge.tsx
│   │   ├── PriceCompareTable.tsx
│   │   ├── TPOTabs.tsx
│   │   └── BudgetSlider.tsx
│   ├── lib/
│   │   └── api.ts               # API 클라이언트
│   └── package.json
│
├── backend/                     # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── feed.py
│   │   │   ├── outfit.py
│   │   │   ├── item.py
│   │   │   ├── reaction.py
│   │   │   └── top_pick.py
│   │   ├── services/
│   │   │   ├── scoring.py       # 코디 스코어링
│   │   │   ├── color_matcher.py # 색상→톤 매핑
│   │   │   ├── similar_finder.py
│   │   │   ├── reason_generator.py
│   │   │   └── top_pick.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── outfit.py
│   │   │   └── reaction.py
│   │   └── db/
│   │       ├── database.py
│   │       └── palettes.py      # 12-tone 팔레트 데이터
│   ├── scripts/
│   │   ├── collect_naver.py     # 네이버 쇼핑 수집
│   │   ├── crawl_musinsa.py     # 무신사 크롤링
│   │   ├── preprocess.py        # 전처리
│   │   └── generate_outfits.py  # 코디 조합 생성
│   └── requirements.txt
│
├── data/
│   ├── palettes/                # 12-tone 팔레트 JSON
│   ├── products/                # 수집 상품 데이터
│   └── outfits/                 # 생성 코디 데이터
│
├── docker-compose.yml
└── README.md
```

### 18.3 참고 자료

1. McAuley, J. et al. (2015). "Image-Based Recommendations on Styles and Substitutes." SIGIR.
2. He, R., & McAuley, J. (2016). "Ups and Downs: Modeling the Visual Evolution of Fashion Trends with One-Class Collaborative Filtering." WWW.
3. Vasileva, M.I. et al. (2018). "Learning Type-Aware Embeddings for Fashion Compatibility." ECCV.
4. 한국색채학회 (2024). "퍼스널컬러 12-tone 분류 체계 가이드라인."
5. Nielsen Norman Group (2025). "Mobile UX Design Patterns for E-Commerce."
6. Naver Developers. "쇼핑 검색 API 레퍼런스." developers.naver.com.
7. Stitch Fix (2025). "Algorithms Behind Our Styling Recommendations." multithreaded.stitchfix.com.
8. WGSN (2026). "Global Fashion AI Technology Report 2026."

---

> **ColorFit** — 내 색을 아는 순간, 선택이 쉬워진다.
> 어울리는 이유까지, 컬러핏이 골라줄게요.
