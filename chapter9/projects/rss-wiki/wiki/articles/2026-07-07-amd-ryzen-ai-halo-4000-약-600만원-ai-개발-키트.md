# AMD Ryzen AI Halo, $4000(약 600만원) AI 개발 키트

- 원문: [https://news.hada.io/topic?id=31202](https://news.hada.io/topic?id=31202)
- 발행일: 2026-07-07
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

**요약문**

AMD가 Ryzen AI Max+ 395 프로세서 기반 미니 PC에 ROCm, 드라이버, 모델, 개발 도구를 사전 구성해 묶은 AI 개발 키트 "Ryzen AI Halo"를 $3,999.99에 출시했습니다. 16코어 Zen 5 CPU, Radeon 8060S 내장 GPU, XDNA 2 NPU, 128GB 통합 메모리를 갖췄으나, 256GB/s 메모리 대역폭 제약으로 llama-bench 테스트에서는 약 800GB/s 대역폭의 Apple Silicon Mac Studio에 뒤처졌습니다. 이 제품의 차별점은 하드웨어가 아니라 AMD Ryzen AI Developer Center, Best Known Configurations(BKC), AI Playbooks 등 호환성이 검증된 소프트웨어 출발점을 제공한다는 데 있습니다. 다만 동일 프로세서 장비가 과거 $2,000 수준이었던 점을 고려하면, 커뮤니티에서는 가격 대비 가치에 대한 회의적인 반응이 많습니다.

**핵심 포인트**

- **하드웨어 구성**: Ryzen AI Max+ 395(Zen 5, 16코어/32스레드), Radeon 8060S iGPU, XDNA 2 NPU, 128GB LPDDR5x-8000 통합 메모리, 2TB SSD, $3,999.99 단일 구성. Windows 11 Pro 또는 Linux 사전 설치.
- **성능 한계**: 메모리 대역폭이 256GB/s에 그쳐 토큰 생성에서 Mac Studio(약 800GB/s)가 Gemma 4 기준 2~3배 높은 성능을 기록. Vulkan과 ROCm/HIP 백엔드 간에는 뚜렷한 우열이 없음.
- **진짜 가치는 소프트웨어**: AMD가 호환성을 검증한 BKC, 매월 갱신되는 AI Playbooks, System Reset으로 복귀 가능한 기준 상태 등 환경 설정 부담을 줄이는 통합 개발 경험이 핵심. 다만 일부 playbook은 현재도 실패 사례가 있어 유지보수가 관건.
- **NPU 실사용 확인**: AMD Lemonade와 FastFlowLM으로 XDNA 2 NPU에서 gpt-oss-20b-FLM을 실행, CPU/GPU 사용률이 거의 없는 상태에서 최대 35W 소비로 20 tokens/s 생성을 달성. 전력 효율 측면의 가능성을 입증.
- **전원 방식**: 240W USB-C Power Delivery(EPR, 48V/5A) 단일 전원으로 구동되며, 실측 소비 전력은 200W를 넘지 않음.
- **커뮤니티 반응**: 동일 프로세서 제품(Framework Desktop 등)이 더 저렴하게 존재하고 1년 전에는 $2,000 수준이었다는 점에서 가격 비판이 우세. 같은 가격대라면 CUDA 생태계를 갖춘 NVIDIA DGX Spark나 ASUS GX10이 낫다는 의견과, x86 기반이라 원하는 OS를 자유롭게 설치할 수 있다는 반론이 공존.
