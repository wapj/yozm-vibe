# 메모리 아끼면서 Cross Entropy Loss 계산하기

- 원문: [https://news.hada.io/topic?id=31168](https://news.hada.io/topic?id=31168)
- 발행일: 2026-07-06
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

요약과 핵심 포인트를 정리했습니다.

## 요약

이 글은 긴 context와 큰 vocabulary를 가진 LLM 학습에서 LM head와 cross entropy loss 계산이 가장 큰 메모리 소비처가 되는 이유를 분석합니다. 128K context 환경에서는 logits 텐서 하나가 약 40GB에 달해 모델 weight보다도 커집니다. 저자는 16B 모델을 128K context로 학습하다 실제로 겪은 OOM 문제에서 출발하여, cross entropy의 forward/backward를 처음부터 유도하고, sequence 축을 chunk로 나누는 단순한 방식이 peak memory를 낮추지 못하는 원인(autograd가 backward 시점까지 chunk별 계산 그래프를 유지함)을 설명합니다. 해결책으로 각 chunk의 gradient를 forward pass 안에서 즉시 계산하여 큰 텐서가 그래프에 남지 않게 하는 FLCE(Fused Linear Cross Entropy) 기법을 소개하고, 메모리/지연시간 트레이드오프 분석과 실제 kernel 구현 과정까지 다룹니다.

## 핵심 포인트

- **문제**: 128K context에서 logits 텐서(sequence 길이 × vocab 크기)가 약 40GB로, 모델 weight보다 큰 메모리를 차지하여 OOM의 주요 원인이 됩니다.
- **단순 chunking의 한계**: sequence 축으로 chunk를 나누어도 autograd가 각 chunk의 계산 그래프를 backward까지 보관하므로 peak memory가 줄어들지 않습니다.
- **FLCE의 핵심 아이디어**: 각 chunk의 gradient를 forward pass 도중에 즉시 계산해 버리면, 큰 logits 텐서를 계산 그래프에 유지할 필요가 없어집니다.
- **이론적 기반**: cross entropy의 forward/backward 수식을 처음부터 유도하여 gradient를 조기에 계산할 수 있는 근거를 제시합니다.
- **실용적 내용**: 메모리와 지연시간 사이의 트레이드오프 분석, 실제 kernel 구현 walkthrough를 포함합니다.
