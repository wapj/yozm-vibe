# Ternlight - 브라우저(WASM)에서 실행되는 7MB 임베딩 모델

- 원문: [https://news.hada.io/topic?id=31218](https://news.hada.io/topic?id=31218)
- 발행일: 2026-07-08
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

## 요약

Ternlight는 브라우저와 엣지 런타임에서 서버 호출 없이 동작하는 초소형 텍스트 임베딩 모델입니다. `all-MiniLM-L6-v2`를 교사 모델로 증류하고 BitNet b1.58 방식의 삼진(ternary) 양자화 인지 학습을 적용해, 엔진·모델·BERT 토크나이저를 단일 `.wasm` 파일(base 7MB, mini 5MB)로 통합했습니다. GPU 없이 CPU만으로 임베딩당 수 밀리초 수준의 성능을 내며, 약 30배 압축에도 정확도 손실은 소폭에 그칩니다. 데이터가 기기를 벗어나지 않아 프라이버시 보호, 오프라인 검색, 정적 사이트의 시맨틱 검색 등에 적합합니다.

## 핵심 포인트

- **초소형 단일 번들**: 엔진 + 모델 + 토크나이저를 하나의 `.wasm`에 통합. postinstall이나 런타임 fetch가 필요 없으며, base 7.2MB / mini 5.0MB(gzip 기준)
- **삼진 가중치 설계**: 모든 가중치가 -1, 0, +1이라 추론이 덧셈·뺄셈으로 처리되며, 처음부터 삼진 모델로 학습(QAT)해 품질을 유지. 추론 엔진은 Rust로 작성해 WASM SIMD로 컴파일
- **간결한 API**: `embed`, `cosineSim`, `similar` 세 함수로 구성. 문자열을 384차원 L2 정규화 벡터로 변환하며, 코드 3줄로 시맨틱 검색 구현 가능. Node, 브라우저, Cloudflare Workers, Deno, Bun 등을 지원
- **성능 지표**: base는 임베딩당 약 5.1ms(약 195 emb/s), Spearman 0.844 / mini는 약 2.5ms(약 400 emb/s), Spearman 0.820. 최대 입력은 128 토큰
- **활용처**: 입력 즉시 검색(search-as-you-type), 프라이버시 민감 앱, 오프라인 우선 앱(브라우저 확장·Obsidian 플러그인), 엣지 런타임, IoT 기기, 백엔드 없는 정적 사이트 검색
- **커뮤니티 반응**: 정적 벡터 검색(Pagefind 유사), SQLite/HNSW와의 하이브리드 검색 결합 가능성에 관심이 높은 반면, 저사양 CPU에서 공표 수치 대비 처리량이 낮다는 보고(400 emb/s 대비 35 emb/s)와 데모 검색 품질에 대한 지적도 있음. MIT 라이선스로 공개됨
