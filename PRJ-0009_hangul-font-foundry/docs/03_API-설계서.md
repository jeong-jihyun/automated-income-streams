# PRJ-0009 API 설계서
버전 1.0 · 모바일 클라이언트와 기존 Python CLI를 연결하는 REST 초안

## 1. 아키텍처
Mobile Web/PWA → HTTPS API → 작업 큐/작업 실행기 → 기존 hangul_font_kit CLI → 파일 저장소.
현재 README에 명시된 실행 인터페이스를 감싸는 API 제안이며, 아래 엔드포인트가 저장소에 이미 구현되어 있다는 뜻은 아니다.

## 2. 공통 규칙
- Base URL: /api/v1
- Content-Type: application/json (파일 업로드는 multipart/form-data)
- 인증: 배포 시 세션 또는 Bearer 토큰 적용
- 모든 작업 응답에 requestId와 createdAt 포함
- 오류 형식: { code, message, details, requestId }

## 3. 엔드포인트
### 프로젝트
- POST /projects : 프로젝트 생성
- GET /projects/{projectId} : 프로젝트 요약/진행률
- PATCH /projects/{projectId}/settings : 폰트 설정 갱신
- GET /projects/{projectId}/glyphs?status=&q=&page=&size= : 글리프 검색

### 문자 세트
- POST /projects/{projectId}/charset
  - Request: { includeHangul2350:true, includeLatin:true, includeDigits:true, includeSymbols:true }
  - Response: { jobId, status:"queued" }

### 글리프 파일
- POST /projects/{projectId}/glyphs/upload (multipart)
- GET /projects/{projectId}/glyphs/{codePoint}
- DELETE /projects/{projectId}/glyphs/{codePoint}

### 검수
- POST /projects/{projectId}/checks
  - Request: { glyphDirectory:"glyphs" }
  - Response: { jobId, status:"queued" }
- GET /jobs/{jobId}
- GET /projects/{projectId}/checks/latest

### 빌드
- POST /projects/{projectId}/builds
  - Request: { outputDirectory:"font_out", allowMissing:false }
  - Response: { jobId, status:"queued" }
- GET /projects/{projectId}/builds
- GET /artifacts/{artifactId}/download

## 4. 데이터 모델 초안
- Project(id, name, fontFamily, createdAt, updatedAt)
- Glyph(projectId, codePoint, character, fileName, status, updatedAt)
- CheckRun(id, projectId, status, errorCount, warningCount, startedAt, finishedAt)
- CheckIssue(id, checkRunId, codePoint, severity, ruleCode, message, line)
- BuildRun(id, projectId, status, allowMissing, startedAt, finishedAt)
- Artifact(id, buildRunId, type, fileName, size, checksum, storageKey)

## 5. 작업 상태
queued → running → succeeded | failed | cancelled
진행률은 실제 작업 실행기에서 보고한 값만 노출한다. 알 수 없는 경우 null로 반환하고 임의로 증가시키지 않는다.

## 6. 오류 코드
- PROJECT_NOT_FOUND
- INVALID_GLYPH_FILENAME
- INVALID_SVG_VIEWBOX
- UNSUPPORTED_SVG_COMMAND
- OPEN_CONTOUR
- MISSING_GLYPHS
- BUILD_FAILED
- ARTIFACT_NOT_FOUND
- UPLOAD_TOO_LARGE

## 7. 보안 및 운영
SVG 파서는 외부 엔티티/외부 URL을 비활성화하고, 업로드 파일명은 서버에서 재생성한다. 작업별 CPU/메모리/시간 제한, 프로젝트별 접근 권한, 다운로드 만료 URL, 감사 로그를 둔다. 사용자 업로드 SVG를 실행 가능한 HTML로 렌더링하지 않는다.
