# ArchyAI 홈페이지(랜딩 페이지) 제작 가이드

> 이 문서는 **별도 Claude Code 세션이 ArchyAI 서비스 소개용 웹 홈페이지(랜딩 페이지)를 제작할 때 단독으로 참조**할 수 있도록 작성된 통합 가이드입니다.
> 서비스 정의, 핵심 가치, 타깃 사용자, 기능, 디자인 시스템, 톤·보이스, 페이지 구조, 카피 가이드까지 한 파일에 모두 포함되어 있습니다.
>
> - 작성일: 2026-04-25
> - 출처: `README.md`, `prd/main.md`, `prd/01~13`, `docs/ui-design-system.md`, `docs/user-flows.md`
> - 적용 대상: **ArchyAI 마케팅용 웹 홈페이지** (앱 자체 UI가 아님 — 앱은 Flutter 모바일)

---

## 1. 서비스 한 줄 정의

> **ArchyAI** — *"링크 한 번 공유하면, AI가 장소·이벤트·꿀팁·후기로 알아서 정리해주는 SNS 콘텐츠 아카이빙 앱."*

- 영문 한 줄: *Save SNS links, let AI archive your places, events, tips, and reviews.*
- 카테고리: **AI-powered SNS Content Archiving / Place Discovery / Date Course Planner**
- 플랫폼: iOS · Android (Flutter 단일 코드베이스)

---

## 2. 서비스 개요

### 2.1 무엇을 하는 앱인가
사용자가 인스타그램·유튜브·틱톡·네이버 블로그 등에서 본 콘텐츠 링크를 ArchyAI로 공유하면, AI(Google Gemini)가 콘텐츠를 분석해 **자동으로 5가지 카테고리**로 분류·아카이빙합니다.

| 카테고리 | 설명 | 예시 |
|---|---|---|
| **place** | 맛집·카페·관광지 등 장소 소개/방문 후기 | "성수동 신상 카페" 릴스 |
| **event** | 팝업·공연·전시·모임 등 기간 한정 이벤트 | "○○ 팝업스토어 D-7" 게시물 |
| **tips** | 주식·청소·운동·요리 등 실생활 꿀팁 | "초간단 김치찌개 레시피" 쇼츠 |
| **review** | 제품·서비스·앱 사용 후기 | "에어팟 프로 2 한 달 후기" |
| **unknown** | 위 4가지 외 일반 정보·뉴스·에세이 | 분류 모호한 콘텐츠 |

저장된 **place**는 지도에 자동으로 핀이 찍히고, 여러 장소를 묶어 **데이트 코스**로 추천·공유할 수 있습니다.

### 2.2 왜 만들었나 (Problem)
- SNS에서 본 좋은 장소·정보를 **북마크만 하고 다시 못 찾는** 문제
- 링크마다 정보가 제각각이라 **수동 정리가 번거로움**
- 데이트·외출 계획 시 저장한 장소를 다시 뒤져야 하고, **동선 짜기 비효율**
- 친구·연인과 **계획 공유가 불편**함

### 2.3 어떻게 해결하나 (Solution)
1. **공유시트 한 번** — SNS 링크를 ArchyAI로 공유
2. **AI 자동 분석** — Gemini가 장소명·주소·카테고리·이미지·영업시간 추출 (캐시 적중 시 1초, 미적중 시 30초 내)
3. **자동 분류·태깅** — place / event / tips / review로 분류, 태그 자동 부여
4. **지도 시각화** — 장소는 자동으로 지도에 핀 등록
5. **AI 코스 추천** — 저장된 장소로 동선 최적 데이트 코스 자동 생성
6. **읽기 전용 공유** — 코스/장소를 링크 하나로 공유

---

## 3. 타깃 사용자 (Target Persona)

### 3.1 메인 페르소나
- **이름**: 지훈 (28세) · 직장인
- **상황**: SNS에서 핫플 정보를 자주 보지만 주말마다 어디 갈지 매번 다시 찾음
- **목표**: 링크만 모아두면 자동으로 정리되고, 동선 좋은 코스를 추천받아 공유까지 빠르게
- **제약**: 평일 바쁨, 긴 폼 입력 싫어함, 로딩 길면 이탈
- **성공 정의**: 링크 공유 후 1분 내 코스 초안 + 지도 동선 + 연인과 공유 완료

### 3.2 보조 페르소나
- **민지 (27)** — 데이트 플래너형: 링크 분석 → 장소 저장 → 코스 생성
- **준호 (32)** — 맛집 탐방가형: 검색 → 필터링 → 저장
- **수영 (25)** — 소셜 공유러형: 장소 발견 → 공유 → 협업

### 3.3 인구통계 / 행동 특성
- **연령**: 20~35세
- **관계**: 연인 / 친구와 자주 외출 / 데이트 계획
- **행동**: 인스타·유튜브·틱톡에서 핫플·카페·맛집·전시·공연 정보를 일상적으로 소비
- **디바이스**: 모바일 우선 (iOS/Android)

---

## 4. 핵심 가치 (Core Value Propositions)

홈페이지에서 강조해야 할 **5대 핵심 가치**:

### ① 🤖 AI 자동 분류 (Zero Manual Effort)
> *"링크만 공유하세요. 나머지는 AI가 합니다."*
- Gemini 기반 멀티모달 분석 (텍스트 + 이미지 + 영상 캡션)
- 5개 카테고리 자동 분류 + 신뢰도 스코어
- 사용자 수동 입력 = 0

### ② ⚡ 빠른 응답 (Speed)
> *"캐시 적중 시 1초, 처음 보는 링크도 30초."*
- L1(메모리) + L2(Redis) 다층 캐시
- 캐시 적중률 ≥ 40%, 캐시 적중 p50 ≤ 1s, 미적중 p90 ≤ 30s

### ③ 🗺️ 지도 통합 (Map-First Archive)
> *"저장한 장소가 자동으로 지도에 모입니다."*
- Kakao Map 기반 장소 시각화
- 태그/카테고리 필터링
- 마커 클릭 시 원본 SNS 링크로 즉시 회귀

### ④ 🧭 AI 코스 추천 (Smart Routing)
> *"3개만 골라주세요. 동선은 AI가 짭니다."*
- 영업시간·카테고리 다양성·이동시간 종합 고려
- 사용자 편집 시 머지 모드 (수정 보존 + 대안 제시)

### ⑤ 🔗 간편 공유 (Effortless Sharing)
> *"링크 하나로 코스 전체를 공유하세요."*
- 읽기 전용 미리보기 링크/코드 생성
- 동행자는 앱 설치 없이도 코스 확인 가능

---

## 5. 주요 기능 (Feature List)

홈페이지 "Features" 섹션에 활용할 기능 목록입니다.

| # | 기능 | 한 줄 설명 | 관련 PRD |
|---|---|---|---|
| 1 | SNS 링크 분석 | 인스타·유튜브·틱톡·블로그 링크 자동 분석 | `01-sns-link-analysis` |
| 2 | 장소 자동 저장 | 추출된 장소를 위시리스트에 자동 등록 | `02-place-management` |
| 3 | 5종 카테고리 분류 | place / event / tips / review / unknown | `social-media-analysis-system` |
| 4 | 태그 시스템 | 기본 태그 + 사용자 정의 태그 | `02-place-management` |
| 5 | 지도 시각화 | Kakao Map 기반 마커·핀·검색 | `04-map-visualization` |
| 6 | 데이트 코스 추천 | AI가 동선 최적 코스 제안 | `03-course-recommendation` |
| 7 | 코스 편집 | 순서 변경·장소 교체·이름 지정 | `03-course-recommendation` |
| 8 | 공유 시스템 | 읽기 전용 링크/코드 생성 | `05-sharing-system` |
| 9 | 검색·필터 | 태그·카테고리·즐겨찾기 필터 | `08-search-filter` |
| 10 | 푸시 알림 | 방문 예정 리마인더 (FCM) | `07-notification-system` |
| 11 | iOS 공유 큐 | iOS 공유시트에서 일괄 처리 | `13-ios-share-queue` |
| 12 | 멀티모달 분석 | 이미지·영상 캡션 동시 분석 | `12-multimodal` |

---

## 6. 디자인 시스템 (Design System)

> 본 절은 **앱의 디자인 시스템**입니다. 홈페이지는 앱과 시각적 일관성을 유지하기 위해 동일한 컬러·타이포·간격 토큰을 그대로 채택할 것을 권장합니다.

### 6.1 디자인 원칙
- **다크 테마 단일 운영** — 전체 다크 팔레트, 라이트 모드 미제공
- **Teal 브랜드** — `#1D9E75`를 단일 강조색으로
- **저채도 배경 + 고채도 강조** — 어두운 배경에 brand teal만 도드라지게
- **Material 3 기반** — 표준 컴포넌트 패턴 준수
- **모바일 우선 / 한글 가독성 최우선** — Noto Sans KR 폴백

### 6.2 Color Tokens

#### Brand — Teal
| 토큰 | HEX | 용도 |
|---|---|---|
| `primary` / `teal400` | `#1D9E75` | CTA, 버튼, 링크, 강조 (메인 브랜드) |
| `primary600` / `teal600` | `#0D7A57` | 호버·secondary |
| `primary100` / `brandSubtle` | `#0A2318` | 칩·뱃지 배경 |
| `primary900` | `#07150F` | 진한 브랜드 강조 |

#### Semantic
| 토큰 | HEX | 용도 |
|---|---|---|
| `success` | `#38A169` | 성공 |
| `warning` | `#D69E2E` | 경고 |
| `error` | `#E53E3E` | 에러 |
| `info` | `#3182CE` | 정보 |

#### Dark Background Scale
| 토큰 | HEX | 용도 |
|---|---|---|
| `bgBase` | `#090C10` | 페이지 최하층 배경 (body) |
| `bgElevated` | `#0D1118` | 살짝 올라온 면 (input 배경) |
| `surfaceDefault` | `#141620` | 카드·섹션·시트 배경 |
| `borderSubtle` | `#1A2030` | 구분선·보더 |
| `gray500` | `#5A7A72` | 비활성 아이콘 |

#### Text
| 토큰 | HEX | 용도 |
|---|---|---|
| `textPrimary` | `#D4EEE8` | 본문·헤드라인 |
| `textSecondary` | `#8AADA6` | 보조 텍스트·서브 카피 |
| `textTertiary` | `#5A7A72` | 힌트·캡션·비활성 |

> ⚠️ 일반 흰색(`#FFFFFF`)은 본문에 사용하지 않습니다. 모든 텍스트는 `textPrimary`(#D4EEE8) 기준.

### 6.3 Typography

- **폰트 스택**: `'Google Sans'` → `'Noto Sans KR'` → `sans-serif`
- 웹에서는 Google Fonts CDN으로 `Noto Sans KR` + 영문은 `Inter` 또는 `Google Sans` 대체 가능

| 스타일 | 사이즈 | weight | line-height | 홈페이지 용도 |
|---|---|---|---|---|
| Display / Hero | 48~64px (반응형) | 800 | 1.2 | Hero 섹션 메인 카피 |
| `h1` | 30px | 800 | 1.3 | 섹션 타이틀 |
| `h2` | 24px | 800 | 1.3 | 서브 섹션 |
| `h3` | 20px | 700 | 1.4 | 카드 제목 |
| `h4` | 18px | 700 | 1.4 | 작은 헤더 |
| `bodyLarge` | 16px | 500 | 1.5 | 본문 |
| `bodyMedium` | 14px | 500 | 1.5 | 보조 본문 |
| `bodySmall` | 12px | 500 | 1.5 | 캡션·푸터 |
| `button` | 16px | 700 | 1.0 | 버튼 라벨 |

### 6.4 Spacing Scale (4px 베이스)
`0 / 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64`

홈페이지 권장:
- 섹션 간 수직 패딩: `96~120px` (모바일 `64px`)
- 카드 내부 패딩: `24px`
- 텍스트 블록 간 간격: `16~24px`

### 6.5 Border Radius
| 토큰 | 값 | 용도 |
|---|---|---|
| `radiusSm` | 2px | 미세 요소 |
| `radiusBase` | 4px | 입력 보조 |
| `radiusLg` | 8px | **버튼·카드 기본** |
| `radiusXl` | 12px | 큰 카드 |
| `radius2xl` | 16px | 히어로 이미지·모달 |
| `radiusFull` | 9999px | 칩·아바타 |

### 6.6 컴포넌트 스펙 (홈페이지에 직접 매핑)

#### Primary Button (CTA)
- 배경 `#1D9E75` · 텍스트 `#FFFFFF`
- 패딩 24px(가로) / 16px(세로) · radius `8px`
- elevation 0, hover 시 배경 `#0D7A57`
- 폰트 16px / w700

#### Outline Button
- 배경 transparent · 보더 `1.5px solid #1D9E75` · 텍스트 `#1D9E75`
- radius `8px`

#### Ghost / Text Button
- 텍스트 `#1D9E75` · 패딩 16px / 12px

#### Card
- 배경 `#141620` · 보더 `0.5px solid #1A2030` · radius `8px` · elevation 0
- 호버 시 보더 `#1D9E75`로 전환 권장

#### Input
- 배경 `#0D1118` · 보더 `1px solid #1A2030`
- focus 시 보더 `2px solid #1D9E75`
- placeholder `#5A7A72`

#### Divider
- `#1A2030` · 두께 0.5px

### 6.7 아이콘
- **Material Symbols** 또는 **Lucide** 권장
- 색상: 활성 `textPrimary` (#D4EEE8), 비활성 `textTertiary` (#5A7A72), 강조 `primary` (#1D9E75)
- 카테고리 매핑 예:
  - place → `place` / `restaurant`
  - event → `event` / `local_activity`
  - tips → `lightbulb` / `tips_and_updates`
  - review → `rate_review` / `star`

### 6.8 모션 / 인터랙션
- 트랜지션: `150~250ms` `ease-out`
- 호버 효과: 보더 색 전환 + 미세한 transform 1~2px 위로
- 스크롤 reveal: `opacity 0→1` + `translateY(16px → 0)`, 200ms

---

## 7. 톤 & 보이스 (Tone & Voice)

| 항목 | 가이드 |
|---|---|
| **톤** | 친근하고 똑똑한 친구 / 과장 없음 / 실용적 |
| **인칭** | "당신" 대신 **반말 가까운 존댓말** ("~해보세요", "~해드려요") |
| **금지어** | "blazingly fast", "혁신적", "최고의", 마케팅 과장 표현 |
| **권장 표현** | 구체적 숫자 ("1초 안에", "30초 내", "5종 분류"), 사용자 행동 동사 ("공유", "저장", "추천") |
| **언어** | 기본 한국어, 보조로 영어 (i18n 대응) |
| **이모지** | 섹션 헤더에서 절제된 사용 (1~2개), 본문에는 지양 |

### 7.1 카피 예시 (Hero)
- ✅ "링크 하나면, AI가 알아서 정리해드려요."
- ✅ "SNS에서 본 그 장소, 다시 못 찾을 일 없어요."
- ❌ "혁신적인 AI가 모든 것을 바꿉니다!"
- ❌ "역대 최고의 데이트 플래너"

---

## 8. 홈페이지 정보 구조 (Recommended Page Structure)

> 표준 SaaS 랜딩 페이지 구조. 위에서 아래로 스크롤 흐름.

### 섹션 1. **Header / Nav**
- 좌측: 로고 (텍스트 "ArchyAI" + 아이콘)
- 우측: `기능` · `사용법` · `FAQ` · `다운로드 (CTA)`
- 배경: `bgBase` (`#090C10`), 스크롤 시 살짝 블러된 `surfaceDefault`로 전환

### 섹션 2. **Hero**
- 메인 카피: **"링크 하나면, AI가 알아서 정리해드려요"**
- 서브 카피: "인스타·유튜브·틱톡 링크를 공유하면, AI가 장소·이벤트·꿀팁·후기로 자동 분류합니다."
- CTA: `[App Store 다운로드]` `[Google Play 다운로드]` (Primary + Outline)
- 비주얼: 모바일 목업 (앱 화면 스크린샷) 또는 짧은 데모 영상/Lottie

### 섹션 3. **Problem / Why**
- 사용자 페인 3가지 카드
  1. "북마크만 하고 다시 못 찾아요"
  2. "장소 정보 정리가 너무 번거로워요"
  3. "데이트 코스 짜기, 매번 처음부터"

### 섹션 4. **Solution / How it works** (4-step)
1. **공유** — SNS 링크를 ArchyAI로 공유
2. **분석** — AI가 1초~30초 내 자동 추출
3. **저장** — 5종 카테고리로 자동 분류 + 지도에 핀
4. **활용** — 코스 추천 받고 친구와 공유

> 각 단계는 아이콘 + 1줄 설명 + 스크린샷 1장 권장

### 섹션 5. **Core Features** (5대 가치 — §4 그대로)
- 카드형 그리드 (3 → 모바일 1열)
- 각 카드: 아이콘 / 제목 / 1~2줄 설명 / "더 알아보기" 링크

### 섹션 6. **Categories Showcase**
- "ArchyAI는 5가지로 분류합니다" 강조
- place / event / tips / review / unknown 각각 컬러 칩 + 예시 콘텐츠 미리보기

### 섹션 7. **Demo / Use Cases**
- 페르소나별 시나리오 (지훈/민지/준호/수영) — 1~2개 선택
- 짧은 스토리 + 화면 캡처

### 섹션 8. **Performance / Trust**
- "캐시 히트율 40%↑", "응답 1초", "코스 생성 1분 내" 등 KPI 수치
- 보안·프라이버시 한 줄 ("저장 데이터는 본인만 접근")

### 섹션 9. **FAQ**
- 어떤 SNS를 지원하나요? (인스타·유튜브·틱톡·네이버 블로그)
- 무료인가요?
- 데이터는 어떻게 보호되나요?
- 안드로이드·iOS 모두 지원하나요?

### 섹션 10. **Final CTA**
- 큰 헤드라인 + 다운로드 버튼 2개
- 배경: `surfaceDefault` 또는 brand subtle gradient

### 섹션 11. **Footer**
- 좌측: 로고 + 한 줄 소개
- 컬럼: Product / Company / Legal / Contact
- 하단: © 2026 ArchyAI · 이메일 / 개인정보처리방침 / 이용약관

---

## 9. 권장 기술 스택 (홈페이지)

> 앱은 Flutter지만, **홈페이지는 별도 웹 프로젝트**로 권장.

### 옵션 A — 정적 SaaS 랜딩 (추천)
- **Next.js 14+ (App Router)** + TypeScript
- **Tailwind CSS** — 디자인 토큰을 `tailwind.config.ts`에 그대로 매핑
- **shadcn/ui** — Card·Button 등 베이스 컴포넌트
- **Framer Motion** — 스크롤 reveal·미세 애니메이션
- **next/image** — 스크린샷 최적화
- 배포: **Vercel**

### 옵션 B — 가벼운 옵션
- **Astro** + Tailwind — 더 빠른 LCP, 인터랙션 최소
- 배포: Vercel / Netlify / Cloudflare Pages

### Tailwind 토큰 매핑 예시
```ts
// tailwind.config.ts
theme: {
  extend: {
    colors: {
      brand: {
        DEFAULT: '#1D9E75',
        600: '#0D7A57',
        100: '#0A2318',
        900: '#07150F',
      },
      bg: {
        base: '#090C10',
        elevated: '#0D1118',
      },
      surface: { DEFAULT: '#141620' },
      border: { subtle: '#1A2030' },
      text: {
        primary: '#D4EEE8',
        secondary: '#8AADA6',
        tertiary: '#5A7A72',
      },
      success: '#38A169',
      warning: '#D69E2E',
      error: '#E53E3E',
      info: '#3182CE',
    },
    fontFamily: {
      sans: ['"Google Sans"', '"Noto Sans KR"', 'sans-serif'],
    },
    borderRadius: {
      lg: '8px',
      xl: '12px',
      '2xl': '16px',
    },
  },
}
```

---

## 10. 접근성 (Accessibility)

- 최소 터치 타깃 **44×44px**
- 텍스트 대비 WCAG AA 이상 (`textPrimary` on `bgBase` ≥ 12:1 ✅)
- 모든 인터랙티브 요소에 `aria-label` 또는 적절한 시맨틱 태그
- 포커스 링 명시 — `outline 2px #1D9E75 offset 2px`
- 이미지 `alt` 필수, 데모 영상 캡션 제공
- 키보드 내비게이션 100% 지원

---

## 11. 국제화 (i18n)

- 1차: 한국어 (`ko`)
- 2차: 영어 (`en`)
- Next.js `next-intl` 또는 `next-i18next` 권장
- 날짜·거리 단위 자동 전환 (km/mi)

---

## 12. SEO / Open Graph

| 항목 | 값 |
|---|---|
| **title** | ArchyAI — AI가 정리해주는 SNS 링크 아카이브 |
| **description** | 인스타·유튜브·틱톡 링크를 공유하면 AI가 장소·이벤트·꿀팁·후기로 자동 정리해드려요. 데이트 코스 추천도 무료. |
| **og:image** | 1200×630, 다크 배경 + brand teal 강조 |
| **keywords** | SNS 아카이브, 핫플 저장, 데이트 코스, AI 링크 분석, 인스타 저장 |
| **lang** | `ko-KR` (default), `en` (alt) |
| **canonical** | `https://archyai.app` (가정) |

JSON-LD `SoftwareApplication` 스키마 추가 권장.

---

## 13. 자산 (Assets)

홈페이지 제작 시 필요한 자산 체크리스트:

- [ ] 로고 (SVG, 다크/라이트 양쪽 — 다크 배경에 teal 메인)
- [ ] 파비콘 (16/32/180/512)
- [ ] 앱 스크린샷 5~7장 (홈, 링크 분석, 지도, 코스, 공유)
- [ ] App Store / Google Play 배지 (공식)
- [ ] 짧은 데모 영상 (15~30초) 또는 Lottie
- [ ] OG 이미지 (1200×630)
- [ ] 카테고리 아이콘 5종 (place / event / tips / review / unknown)

> 현재 리포지토리에는 마케팅용 자산이 별도 정리되어 있지 않으므로, **앱 캡처를 활용**하거나 placeholder 사용 후 교체.

---

## 14. 참고 파일 (Repo Cross-Reference)

다른 세션이 더 깊은 정보가 필요할 때 참조:

| 주제 | 경로 |
|---|---|
| 프로젝트 개요 | `README.md`, `CLAUDE.md` |
| 제품 요구사항 (PRD) 메인 | `prd/main.md` |
| 링크 분석 상세 | `prd/01-sns-link-analysis.md`, `prd/social-media-analysis-system.md` |
| 장소 관리 | `prd/02-place-management.md` |
| 코스 추천 | `prd/03-course-recommendation.md` |
| 지도 | `prd/04-map-visualization.md` |
| 공유 | `prd/05-sharing-system.md` |
| 디자인 시스템 (앱) | `docs/ui-design-system.md` |
| 사용자 플로우 | `docs/user-flows.md` |
| 화면 스펙 | `docs/screens/*.md` |
| 컬러 토큰 원본 | `frontend/lib/core/theme/app_colors.dart` |
| 타이포 토큰 원본 | `frontend/lib/core/theme/app_text_styles.dart` |

---

## 15. 빠른 시작 프롬프트 (Other Claude Session용)

다른 Claude Code 세션에서 이 문서를 받아 홈페이지를 만들 때 사용할 수 있는 시작 프롬프트 예:

> *"`docs/homepage-guide.md`를 읽고 ArchyAI 서비스 소개용 랜딩 페이지를 Next.js 14 App Router + Tailwind + shadcn/ui로 제작해줘. 다크 테마 단일, brand teal `#1D9E75`. 섹션 구조는 §8을 따르고, 컬러·타이포·radius 토큰은 §6 / §9의 Tailwind 매핑을 그대로 사용해. 카피 톤은 §7 가이드 준수. 자산이 없으면 placeholder를 사용하고 TODO 주석을 남겨줘."*

---

*최종 업데이트: 2026-04-25*
*문서 버전: 1.0*
