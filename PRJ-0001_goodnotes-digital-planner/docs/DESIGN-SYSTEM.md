# 디자인 시스템 — Goodnotes Digital Planner

- 문서 ID: PRJ-0001-DESIGN-SYSTEM
- 버전: 1.0
- 상태: 디자인 기준선(구현 전)
- 방향: Minimal Editorial + Digital Productivity
- 관련 문서: [UI 설계서](./UI-DESIGN-SPEC.md), [모바일 대응 기획](../MOBILE-RESPONSIVE-PLAN.md)

## 1. 디자인 원칙

- 차분한 편집 디자인과 디지털 생산성 도구의 명료함을 결합한다.
- 종이 플래너를 연상시키는 따뜻한 아이보리와 네이비를 중심으로 한다.
- 콘텐츠와 결과 미리보기를 우선하고 장식은 절제한다.
- 모바일 우선으로 설계하고 태블릿·데스크톱에서 정보 밀도를 확장한다.
- 색상만으로 선택·오류·성공 상태를 전달하지 않는다.
- UI 디자인과 PDF 산출물 디자인은 별도 규칙으로 관리한다.

## 2. 컬러 토큰

| Token | Value | 용도 |
|---|---|---|
| color.canvas | #F7F5F0 | 앱 배경 |
| color.surface | #FFFFFF | 카드·입력 표면 |
| color.surface.subtle | #F1EFE9 | 보조 패널 |
| color.text.primary | #202A35 | 주요 텍스트 |
| color.text.secondary | #66717C | 보조 텍스트 |
| color.text.muted | #8B9298 | 메타 정보 |
| color.border | #E5E1D8 | 기본 경계선 |
| color.border.strong | #CFC9BD | 강조 경계선 |
| color.brand.primary | #26384A | 주요 액션 |
| color.brand.hover | #1D2D3D | 주요 액션 hover |
| color.accent.sage | #A8B6A0 | 보조 강조 |
| color.accent.rose | #D8A6A0 | 보조 강조 |
| color.accent.sand | #D8C5A3 | 보조 강조 |
| color.status.success | #35745A | 성공 |
| color.status.warning | #9A6A25 | 주의 |
| color.status.error | #B54747 | 오류 |
| color.status.info | #426B8A | 정보 |

상태 컬러는 아이콘·텍스트 레이블과 함께 사용한다. 실제 대비율은 구현 후 WCAG 2.2 AA 기준으로 검사한다.

## 3. 타이포그래피

| Token | Value | 용도 |
|---|---|---|
| font.family.ui | Pretendard, "Noto Sans KR", sans-serif | UI 기본 |
| font.family.editorial | "Noto Serif KR", serif | 제한적 제목 포인트 |
| font.size.xs | 12px | 메타 |
| font.size.sm | 14px | 보조 문구 |
| font.size.md | 16px | 본문·입력 |
| font.size.lg | 18px | 카드 제목 |
| font.size.xl | 24px | 화면 제목 |
| font.size.2xl | 32px | 데스크톱 대제목 |
| font.weight.regular | 400 | 본문 |
| font.weight.medium | 500 | 레이블 |
| font.weight.semibold | 600 | 제목·버튼 |
| line.height.tight | 1.25 | 제목 |
| line.height.normal | 1.5 | 본문 |
| line.height.relaxed | 1.65 | 긴 설명 |

폰트 파일을 추가할 경우 라이선스와 번들 크기를 확인하고 시스템 폰트 대체 순서를 제공한다.

## 4. 간격·모서리·그림자

### 간격(4px 기반)
| Token | Value |
|---|---:|
| space.1 | 4px |
| space.2 | 8px |
| space.3 | 12px |
| space.4 | 16px |
| space.5 | 20px |
| space.6 | 24px |
| space.8 | 32px |
| space.10 | 40px |
| space.12 | 48px |

### 모서리 및 그림자
| Token | Value |
|---|---|
| radius.sm | 6px |
| radius.md | 10px |
| radius.lg | 16px |
| radius.xl | 22px |
| radius.pill | 999px |
| shadow.card | 0 2px 12px rgba(32,42,53,0.05) |
| shadow.overlay | 0 12px 32px rgba(32,42,53,0.12) |

경계선으로 기본 계층을 구분하고 그림자는 오버레이 등 필요한 경우에만 사용한다.

## 5. 반응형 레이아웃 토큰

| Token | Value | 규칙 |
|---|---|---|
| breakpoint.mobile | max 767px | 모바일 단일 열 |
| breakpoint.tablet | 768~1023px | 태블릿 1~2열 |
| breakpoint.desktop | min 1024px | 데스크톱 병렬 배치 |
| container.mobile | 100%, 좌우 16px | 작은 화면 |
| container.tablet | 100%, 좌우 24px | 중간 화면 |
| container.desktop | max 1120px | 중앙 정렬 |
| control.height | 44~48px | 입력·액션 |
| touch.target.min | 44×44px | 터치 권장 기준 |

320px부터 1440px 이상까지 검증한다. 고정 하단 액션은 모바일 Safe Area와 가상 키보드를 고려한다.

## 6. 컴포넌트 규격

### Button
- Primary: 네이비 배경과 흰색 텍스트
- Secondary: 밝은 표면과 중립 경계선
- Tertiary: 배경 없는 텍스트 액션
- Danger: 위험 작업에 한정
- 상태: default, hover, focus-visible, active, disabled, loading
- 기본 높이 48px, 최소 터치 영역 44px

### Input / Select
- 흰색 표면, 1px 경계선, 10px radius
- 높이 48px 권장
- 레이블을 입력 요소 외부에 명시
- placeholder를 레이블 대용으로 사용하지 않음
- 오류 문구를 필드와 연결

### Theme Card
- 실제 테마를 나타내는 색상 샘플과 테마명 표시
- 선택 상태를 테두리·체크·텍스트로 구분
- 카드 전체를 터치 영역으로 제공

### Toggle Option
- 스위치와 설명 레이블을 함께 제공
- 상태를 스크린 리더가 인식할 수 있도록 구현

### Card / Panel
- 흰색 표면, 기본 경계선, 16px radius
- 내부 여백 20~24px
- 불필요한 카드 중첩 지양

### Status / Alert
- 성공·주의·오류·정보를 구분
- 아이콘만 단독 사용하지 않음
- 오류에는 해결 방법 또는 재시도 안내 제공

## 7. 아이콘 및 그래픽

- 단순한 선형 아이콘을 사용하고 크기·선 굵기를 통일한다.
- 아이콘 단독 버튼에는 접근 가능한 이름을 제공한다.
- 장식 아이콘은 보조 기술에서 제외하고 기능 아이콘은 의미를 전달한다.
- 실제 생성 결과와 샘플 미리보기를 명확히 구분한다.

## 8. 인터랙션 원칙

- hover, focus-visible, active, disabled 상태를 일관되게 제공한다.
- 설정 변경은 요약 영역에 즉시 반영한다.
- 실제 측정되지 않는 진행률을 임의로 표시하지 않는다.
- 생성 중 중복 요청을 차단한다.
- 네트워크 오류에도 설정값을 보존한다.
- 애니메이션은 목적이 있을 때만 사용하고 prefers-reduced-motion을 존중한다.

## 9. CSS 변수 기준

구현 시 ui/src/styles/tokens.css 등 단일 파일에서 토큰을 관리한다.

~~~css
:root {
  --color-canvas: #F7F5F0;
  --color-surface: #FFFFFF;
  --color-surface-subtle: #F1EFE9;
  --color-text-primary: #202A35;
  --color-text-secondary: #66717C;
  --color-border: #E5E1D8;
  --color-brand-primary: #26384A;
  --color-brand-hover: #1D2D3D;
  --color-accent-sage: #A8B6A0;
  --color-accent-rose: #D8A6A0;
  --color-accent-sand: #D8C5A3;
  --font-family-ui: Pretendard, "Noto Sans KR", sans-serif;
  --font-family-editorial: "Noto Serif KR", serif;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 22px;
}
~~~

## 10. 구현 가이드

- 토큰 외 임의 색상·간격을 컴포넌트별로 중복 선언하지 않는다.
- 기존 React 18/Vite 및 JavaScript 구현 구조를 우선 유지한다.
- 공통 UI 컴포넌트와 도메인 실행 로직을 분리한다.
- Electron IPC와 웹 API는 실행 어댑터로 분리한다.
- 웹 UI가 반응형이라는 사실만으로 웹 PDF 생성이 가능하다고 간주하지 않는다.
- PDF의 색상·폰트·페이지 레이아웃은 별도 엔진 규칙으로 관리한다.

## 11. 디자인 QA 체크리스트

- [ ] 정의된 토큰을 사용했는가?
- [ ] 제목·본문·레이블 위계가 일관적인가?
- [ ] 터치 타깃이 충분한가?
- [ ] 320px 화면에서 가로 넘침이 없는가?
- [ ] 고정 CTA가 Safe Area·키보드·콘텐츠를 가리지 않는가?
- [ ] 포커스·오류·비활성·로딩 상태가 있는가?
- [ ] 상태가 색상 외 텍스트로도 전달되는가?
- [ ] 미리보기의 실제/샘플 여부가 구분되는가?
- [ ] 모바일·태블릿·데스크톱 브라우저에서 검증했는가?
- [ ] 기존 Electron 실행 흐름에 회귀가 없는가?

## 12. 변경 이력

| 버전 | 일자 | 내용 |
|---|---|---|
| 1.0 | 2026-11-21 | 반응형 웹을 포함한 디자인 토큰·컴포넌트·접근성 기준 최초 작성 |
