# Preprocess QA Report

- 생성 시각: 2026-06-02T10:36:14
- 대상 파일: `260512_렉사응답_QA 테스트.xlsx`
- 총 질문 수: 90

## 전체 요약

| 기대 | 총개수 | 일치 | 불일치 | 오류 |
| --- | ---: | ---: | ---: | ---: |
| A | 60 | 0 | 0 | 60 |
| B | 10 | 0 | 0 | 10 |
| C | 12 | 0 | 0 | 12 |
| D | 8 | 0 | 0 | 8 |

## A 기대 질문 중 A로 판단된 항목

- 개수: 0

없음

## A 기대 질문 중 A가 아닌 것으로 판단된 항목

- 개수: 60

### [1] 1. 지역/상권 진단형
- 질문: 압구정동 상권의 핵심 특징이 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: ConnectError: [Errno 8] nodename nor servname provided, or not known

### [2] 1. 지역/상권 진단형
- 질문: 역삼1동이 유동인구는 많은데 왜 매출 전환이 약하다고 보지?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: ConnectError: [Errno 8] nodename nor servname provided, or not known

### [3] 1. 지역/상권 진단형
- 질문: 삼성1동과 청담동 중 어느 쪽이 임대료 부담이 더 큰 편이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [4] 1. 지역/상권 진단형
- 질문: 강남구에서 점포 증가세가 좋은 동은 어디야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [5] 1. 지역/상권 진단형
- 질문: 강남구에서 5년 생존율 기준으로 안정적인 동은 어디야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [6] 2. 상권 비교형
- 질문: 압구정동 vs 청담동, F&B 통건물 투자엔 어디가 더 나아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [7] 2. 상권 비교형
- 질문: 신사동 vs 논현동, 임차 안정성은 어디가 좋아 보여?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [8] 2. 상권 비교형
- 질문: 대치1동과 역삼2동 중 임대료 대비 매출 효율이 더 좋은 곳은?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [9] 2. 상권 비교형
- 질문: 강남구청역 생활권과 압구정로데오 생활권의 차이를 설명해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [10] 2. 상권 비교형
- 질문: 강남구 안에서 '고매출인데 임대료 부담도 큰 동'만 골라줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [11] 3. 업종 적합도 판단형
- 질문: 압구정동은 체험형 리테일이 맞아, 일반 음식점이 맞아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + (생활백서/연령별 인구)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [12] 3. 업종 적합도 판단형
- 질문: 역삼권은 병원/사무실/카페 중 뭐가 더 어울려?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + (생활백서/연령별 인구)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [13] 3. 업종 적합도 판단형
- 질문: 강남에서 서비스업 비중이 높은 지역은 어디야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + (생활백서/연령별 인구)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [14] 3. 업종 적합도 판단형
- 질문: 직장인구 기반 상권이면 어떤 업종이 유리해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + (생활백서/연령별 인구)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [15] 3. 업종 적합도 판단형
- 질문: 유동인구는 많은데 매출 전환이 약한 지역엔 어떤 전략이 필요해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + 연령별 인구 현황
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [16] 4. 특정 매물 1차 검토형
- 질문: 이 건물 어때?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [17] 4. 특정 매물 1차 검토형
- 질문: 이 매물(관악구 봉천동 908-24)의 장점/단점 5개만 정리해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [18] 4. 특정 매물 1차 검토형
- 질문: 이 물건(관악구 봉천동 908-24)은 수익형으로 봐야 해, 토지가치형으로 봐야 해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [19] 4. 특정 매물 1차 검토형
- 질문: 이 건물(관악구 봉천동 908-24)은 초보 투자자가 건드릴 물건이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [20] 4. 특정 매물 1차 검토형
- 질문: 이 매물(관악구 봉천동 908-24) 1차 검토 의견 알려줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [21] 5. 적정가/호가 판단형
- 질문: 이 건물(관악구 봉천동 908-24) 20억이면 적정가야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [22] 5. 적정가/호가 판단형
- 질문: (관악구 봉천동 908-24 매물 실거래가 26년 4원 1일 기준으로 19.5억인데) 최근 인근 거래사례 기준으로 비싼 편이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [23] 5. 적정가/호가 판단형
- 질문: (관악구 봉천동 908-24 매물 실거래가 26년 4원 1일 기준으로 19.5억인데)대지평당 기준으로 보면 이 호가가 과열이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [24] 5. 적정가/호가 판단형
- 질문: (관악구 봉천동 908-24 매물 실거래가 26년 4원 1일 기준으로 19.5억인데)신축 프리미엄 감안해도 이 가격이 설명돼?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [25] 5. 적정가/호가 판단형
- 질문: (마포구 대흥동 466-4가 4억에) 급매라고 하는데 진짜 급매로 볼 수 있어?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [26] 6. 매물 추천/소싱형
- 질문: 압구정로데오역 도보 5분 이내, 150억 이하, 대지 200㎡ 이상 매물만 골라줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [27] 6. 매물 추천/소싱형
- 질문: 강남구청역 인근에서 병원이나 사무실 세팅 가능한 건물 추천해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [28] 6. 매물 추천/소싱형
- 질문: 강남구청역 인근에서 주차 4대 이상 되는 청담동 매물 보여줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [29] 6. 매물 추천/소싱형
- 질문: 강남구청역 인근에서 코너 건물만 추려줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [30] 6. 매물 추천/소싱형
- 질문: 영등포,구로,서촌 제3종일반주거지역 중 개발여지 있어 보이는 물건만 보여줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [31] 7. 건축물/개발 가능성 1차 선별형
- 질문: 이 건물(마포구 대흥동 466-4)은 신축보다 리모델링이 나아 보여?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + REXA DB + 실거래 내역 + 공시지가
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [32] 7. 건축물/개발 가능성 1차 선별형
- 질문: 영등포에 오래된 저층 건물 중 개발여지 있어 보이는 물건 찾아줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [33] 7. 건축물/개발 가능성 1차 선별형
- 질문: 같은 가격이면 연식 좋은 신축이 나아, 대지 큰 구축이 나아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [34] 7. 건축물/개발 가능성 1차 선별형
- 질문: (마포구 대흥동 466-4) 현재 건축물 용도 기준으로 어떤 활용이 가능해 보여?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + REXA DB + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [35] 7. 건축물/개발 가능성 1차 선별형
- 질문: (영등포구 대림동 810-31) 건물대장 기준으로 특이사항이 있는지 체크해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [36] 8. 임대 안정성/운영 리스크형
- 질문: 영등포구 대림동 상권은 임차가 빨리 붙는 편일까?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(한계명시)
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [37] 8. 임대 안정성/운영 리스크형
- 질문: 임대료 부담이 큰데 운영 난이도도 높은 지역이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [38] 8. 임대 안정성/운영 리스크형
- 질문: 강남에서 월세 부담 대비 생존율이 괜찮은 곳은 어디야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [39] 8. 임대 안정성/운영 리스크형
- 질문: 강남은 온라인플랫폼 수수료 부담이 큰 업종에 불리한 지역일까?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서(+생활백서)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [40] 8. 임대 안정성/운영 리스크형
- 질문: 연무장길은 권리금·월세 부담을 감안하면 진입 난이도가 높은 상권이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [41] 9. 투자전략/포지셔닝형
- 질문: 20억 예산이면 강남 소형 꼬마빌딩이 나아, 성수 준공업 건물이 나아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(상담형)
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [42] 9. 투자전략/포지셔닝형
- 질문: 에쿼티 5억에 월매출 1200만원정도 나오는데 임대수익형으로 갈지, 토지가치형으로 갈지 판단해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 실거래 내역 + 건축물대장 + 공시지가
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [43] 9. 투자전략/포지셔닝형
- 질문: 강남에선 역세권 소형 근생과 대지 큰 이면물건 중 뭐가 더 나아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 실거래 내역 + 공시지가
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [44] 9. 투자전략/포지셔닝형
- 질문: 지금 시장에선 신축 프리미엄을 사는 게 맞아, 구축 리포지셔닝이 맞아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변(거시판단 한계)
- 필수 데이터 소스: 실거래 내역 + 건축물대장 + 공시지가 + REXA DB
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [45] 9. 투자전략/포지셔닝형
- 질문: 내 투자성향이 보수적이면 어떤 유형의 건물을 봐야 해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(상담형)
- 필수 데이터 소스: REXA DB + 건축물대장 + 실거래 내역 + 사용자 입력
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [46] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 먼저 볼 순서 정해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [47] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 리스크가 가장 낮은 매물부터 정렬해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [48] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 입지 대비 가격이 가장 좋은 매물은 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [49] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 개발여지, 임대안정성, 진입가 기준으로 점수 매겨줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(한계명시)
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [50] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 초보 투자자용 / 공격적 투자자용으로 나눠줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(상담형)
- 필수 데이터 소스: REXA DB + 건축물대장 + 실거래 내역 + 사용자 성향 입력
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [51] 11. 매물 설명문/브리핑 자동화형
- 질문: 이 매물(종로구 삼청동 134-6번지) 1페이지 브리핑 써줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [52] 11. 매물 설명문/브리핑 자동화형
- 질문: 종로구 삼청동 134-6번지에 대해 대표님 보고용으로 핵심만 정리해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [53] 11. 매물 설명문/브리핑 자동화형
- 질문: 이 매물(종로구 삼청동 134-6번지) 장점/리스크/확인필요사항 3줄씩 써줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [54] 11. 매물 설명문/브리핑 자동화형
- 질문: (종로구 삼청동 134-6번지) 중개사 미팅용 질문 리스트 만들어줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [55] 11. 매물 설명문/브리핑 자동화형
- 질문: (종로구 삼청동 134-6번지) 고객에게 보낼 소개문으로 바꿔줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [56] 12. 누락정보/추가조사 항목 제안형
- 질문: 이 물건 (종로구 삼청동 134-6번지) 판단하려면 지금 뭐가 더 필요해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [57] 12. 누락정보/추가조사 항목 제안형
- 질문: (종로구 삼청동 134-6번지) 적정가 평가 전에 추가로 확인할 항목은 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [58] 12. 누락정보/추가조사 항목 제안형
- 질문: 이 건물(종로구 삼청동 134-6번지)에서 가장 위험한 미확인 포인트 3개만 알려줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [59] 12. 누락정보/추가조사 항목 제안형
- 질문: (종로구 삼청동 134-6번지) 실사 전에 꼭 확인해야 할 서류는 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [60] 12. 누락정보/추가조사 항목 제안형
- 질문: (종로구 삼청동 134-6번지) 에서 현재 데이터만으로는 판단 어려운 부분이 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

## 전체 상세 결과

## 기대 A

### [1] 1. 지역/상권 진단형
- 질문: 압구정동 상권의 핵심 특징이 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: ConnectError: [Errno 8] nodename nor servname provided, or not known

### [2] 1. 지역/상권 진단형
- 질문: 역삼1동이 유동인구는 많은데 왜 매출 전환이 약하다고 보지?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: ConnectError: [Errno 8] nodename nor servname provided, or not known

### [3] 1. 지역/상권 진단형
- 질문: 삼성1동과 청담동 중 어느 쪽이 임대료 부담이 더 큰 편이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [4] 1. 지역/상권 진단형
- 질문: 강남구에서 점포 증가세가 좋은 동은 어디야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [5] 1. 지역/상권 진단형
- 질문: 강남구에서 5년 생존율 기준으로 안정적인 동은 어디야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [6] 2. 상권 비교형
- 질문: 압구정동 vs 청담동, F&B 통건물 투자엔 어디가 더 나아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [7] 2. 상권 비교형
- 질문: 신사동 vs 논현동, 임차 안정성은 어디가 좋아 보여?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [8] 2. 상권 비교형
- 질문: 대치1동과 역삼2동 중 임대료 대비 매출 효율이 더 좋은 곳은?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [9] 2. 상권 비교형
- 질문: 강남구청역 생활권과 압구정로데오 생활권의 차이를 설명해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [10] 2. 상권 비교형
- 질문: 강남구 안에서 '고매출인데 임대료 부담도 큰 동'만 골라줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [11] 3. 업종 적합도 판단형
- 질문: 압구정동은 체험형 리테일이 맞아, 일반 음식점이 맞아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + (생활백서/연령별 인구)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [12] 3. 업종 적합도 판단형
- 질문: 역삼권은 병원/사무실/카페 중 뭐가 더 어울려?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + (생활백서/연령별 인구)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [13] 3. 업종 적합도 판단형
- 질문: 강남에서 서비스업 비중이 높은 지역은 어디야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + (생활백서/연령별 인구)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [14] 3. 업종 적합도 판단형
- 질문: 직장인구 기반 상권이면 어떤 업종이 유리해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + (생활백서/연령별 인구)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [15] 3. 업종 적합도 판단형
- 질문: 유동인구는 많은데 매출 전환이 약한 지역엔 어떤 전략이 필요해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서 + 연령별 인구 현황
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [16] 4. 특정 매물 1차 검토형
- 질문: 이 건물 어때?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [17] 4. 특정 매물 1차 검토형
- 질문: 이 매물(관악구 봉천동 908-24)의 장점/단점 5개만 정리해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [18] 4. 특정 매물 1차 검토형
- 질문: 이 물건(관악구 봉천동 908-24)은 수익형으로 봐야 해, 토지가치형으로 봐야 해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [19] 4. 특정 매물 1차 검토형
- 질문: 이 건물(관악구 봉천동 908-24)은 초보 투자자가 건드릴 물건이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [20] 4. 특정 매물 1차 검토형
- 질문: 이 매물(관악구 봉천동 908-24) 1차 검토 의견 알려줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [21] 5. 적정가/호가 판단형
- 질문: 이 건물(관악구 봉천동 908-24) 20억이면 적정가야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [22] 5. 적정가/호가 판단형
- 질문: (관악구 봉천동 908-24 매물 실거래가 26년 4원 1일 기준으로 19.5억인데) 최근 인근 거래사례 기준으로 비싼 편이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [23] 5. 적정가/호가 판단형
- 질문: (관악구 봉천동 908-24 매물 실거래가 26년 4원 1일 기준으로 19.5억인데)대지평당 기준으로 보면 이 호가가 과열이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [24] 5. 적정가/호가 판단형
- 질문: (관악구 봉천동 908-24 매물 실거래가 26년 4원 1일 기준으로 19.5억인데)신축 프리미엄 감안해도 이 가격이 설명돼?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [25] 5. 적정가/호가 판단형
- 질문: (마포구 대흥동 466-4가 4억에) 급매라고 하는데 진짜 급매로 볼 수 있어?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [26] 6. 매물 추천/소싱형
- 질문: 압구정로데오역 도보 5분 이내, 150억 이하, 대지 200㎡ 이상 매물만 골라줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [27] 6. 매물 추천/소싱형
- 질문: 강남구청역 인근에서 병원이나 사무실 세팅 가능한 건물 추천해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [28] 6. 매물 추천/소싱형
- 질문: 강남구청역 인근에서 주차 4대 이상 되는 청담동 매물 보여줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [29] 6. 매물 추천/소싱형
- 질문: 강남구청역 인근에서 코너 건물만 추려줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [30] 6. 매물 추천/소싱형
- 질문: 영등포,구로,서촌 제3종일반주거지역 중 개발여지 있어 보이는 물건만 보여줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [31] 7. 건축물/개발 가능성 1차 선별형
- 질문: 이 건물(마포구 대흥동 466-4)은 신축보다 리모델링이 나아 보여?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + REXA DB + 실거래 내역 + 공시지가
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [32] 7. 건축물/개발 가능성 1차 선별형
- 질문: 영등포에 오래된 저층 건물 중 개발여지 있어 보이는 물건 찾아줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [33] 7. 건축물/개발 가능성 1차 선별형
- 질문: 같은 가격이면 연식 좋은 신축이 나아, 대지 큰 구축이 나아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + 공시지가 + REXA DB + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [34] 7. 건축물/개발 가능성 1차 선별형
- 질문: (마포구 대흥동 466-4) 현재 건축물 용도 기준으로 어떤 활용이 가능해 보여?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장 + REXA DB + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [35] 7. 건축물/개발 가능성 1차 선별형
- 질문: (영등포구 대림동 810-31) 건물대장 기준으로 특이사항이 있는지 체크해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 건축물대장
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [36] 8. 임대 안정성/운영 리스크형
- 질문: 영등포구 대림동 상권은 임차가 빨리 붙는 편일까?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(한계명시)
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [37] 8. 임대 안정성/운영 리스크형
- 질문: 임대료 부담이 큰데 운영 난이도도 높은 지역이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [38] 8. 임대 안정성/운영 리스크형
- 질문: 강남에서 월세 부담 대비 생존율이 괜찮은 곳은 어디야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [39] 8. 임대 안정성/운영 리스크형
- 질문: 강남은 온라인플랫폼 수수료 부담이 큰 업종에 불리한 지역일까?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서(+생활백서)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [40] 8. 임대 안정성/운영 리스크형
- 질문: 연무장길은 권리금·월세 부담을 감안하면 진입 난이도가 높은 상권이야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [41] 9. 투자전략/포지셔닝형
- 질문: 20억 예산이면 강남 소형 꼬마빌딩이 나아, 성수 준공업 건물이 나아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(상담형)
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [42] 9. 투자전략/포지셔닝형
- 질문: 에쿼티 5억에 월매출 1200만원정도 나오는데 임대수익형으로 갈지, 토지가치형으로 갈지 판단해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 실거래 내역 + 건축물대장 + 공시지가
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [43] 9. 투자전략/포지셔닝형
- 질문: 강남에선 역세권 소형 근생과 대지 큰 이면물건 중 뭐가 더 나아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 실거래 내역 + 공시지가
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [44] 9. 투자전략/포지셔닝형
- 질문: 지금 시장에선 신축 프리미엄을 사는 게 맞아, 구축 리포지셔닝이 맞아?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변(거시판단 한계)
- 필수 데이터 소스: 실거래 내역 + 건축물대장 + 공시지가 + REXA DB
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [45] 9. 투자전략/포지셔닝형
- 질문: 내 투자성향이 보수적이면 어떤 유형의 건물을 봐야 해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(상담형)
- 필수 데이터 소스: REXA DB + 건축물대장 + 실거래 내역 + 사용자 입력
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [46] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 먼저 볼 순서 정해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [47] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 리스크가 가장 낮은 매물부터 정렬해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [48] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 입지 대비 가격이 가장 좋은 매물은 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [49] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 개발여지, 임대안정성, 진입가 기준으로 점수 매겨줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(한계명시)
- 필수 데이터 소스: REXA DB + 건축물대장 + 공시지가 + 실거래 내역 + 상권분석 보고서
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [50] 10. 딜 우선순위/포트폴리오 비교형
- 질문: 이 5개 매물(종로구 삼청동 134-6, 동대문구 용두동 254-14, 용산구 원효로4가 142-6, 관악구 봉천동 698-5, 은평구 응암동 97-24) 중 초보 투자자용 / 공격적 투자자용으로 나눠줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변(상담형)
- 필수 데이터 소스: REXA DB + 건축물대장 + 실거래 내역 + 사용자 성향 입력
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [51] 11. 매물 설명문/브리핑 자동화형
- 질문: 이 매물(종로구 삼청동 134-6번지) 1페이지 브리핑 써줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [52] 11. 매물 설명문/브리핑 자동화형
- 질문: 종로구 삼청동 134-6번지에 대해 대표님 보고용으로 핵심만 정리해줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [53] 11. 매물 설명문/브리핑 자동화형
- 질문: 이 매물(종로구 삼청동 134-6번지) 장점/리스크/확인필요사항 3줄씩 써줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [54] 11. 매물 설명문/브리핑 자동화형
- 질문: (종로구 삼청동 134-6번지) 중개사 미팅용 질문 리스트 만들어줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [55] 11. 매물 설명문/브리핑 자동화형
- 질문: (종로구 삼청동 134-6번지) 고객에게 보낼 소개문으로 바꿔줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [56] 12. 누락정보/추가조사 항목 제안형
- 질문: 이 물건 (종로구 삼청동 134-6번지) 판단하려면 지금 뭐가 더 필요해?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [57] 12. 누락정보/추가조사 항목 제안형
- 질문: (종로구 삼청동 134-6번지) 적정가 평가 전에 추가로 확인할 항목은 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [58] 12. 누락정보/추가조사 항목 제안형
- 질문: 이 건물(종로구 삼청동 134-6번지)에서 가장 위험한 미확인 포인트 3개만 알려줘
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [59] 12. 누락정보/추가조사 항목 제안형
- 질문: (종로구 삼청동 134-6번지) 실사 전에 꼭 확인해야 할 서류는 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [60] 12. 누락정보/추가조사 항목 제안형
- 질문: (종로구 삼청동 134-6번지) 에서 현재 데이터만으로는 판단 어려운 부분이 뭐야?
- 기대 그룹: A
- 실제 그룹: ERROR
- 기대 답변 유형: 정식답변
- 필수 데이터 소스: REXA DB + 상권분석 보고서 + 건축물대장 + 공시지가 + 실거래 내역
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

## 기대 B

### [1] 아파트 일반
- 질문: 요즘 아파트 전세는 얼마 정도 해?
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: (범위 외 핵심) 일반적 수준 답변만
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [2] 아파트 일반
- 질문: 강남 아파트 전세가율은 어떤 수준이야?
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: 일반 시장 통념 수준
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [3] 아파트 일반
- 질문: 이번 분기 강남 아파트 시세 알려줘
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: 일반 수준
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [4] 빌라/오피스텔
- 질문: 천호동 빌라 재개발은 얼마면 투자 가능해?
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: 일반 수준(범위 외 핵심)
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [5] 빌라/오피스텔
- 질문: 오피스텔 수익률은 보통 얼마야?
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: 일반 수준
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [6] 재개발·재건축
- 질문: 재건축 진행되면 시세는 보통 얼마나 올라?
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: 일반 수준
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [7] 시장 개황
- 질문: 요즘 금리가 부동산에 어떤 영향 줘?
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: 일반 시장 개황
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [8] 시장 개황
- 질문: 올해 부동산 시장 분위기 어때?
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: 일반 시장 개황
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [9] 광범위 질문
- 질문: 강남구 땅값 알려줘
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: (범위 과대) 일반 수준
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [10] 광범위 질문
- 질문: 서울 부동산 사면 돼?
- 기대 그룹: B
- 실제 그룹: ERROR
- 기대 답변 유형: 제한답변
- 필수 데이터 소스: (범위 과대) 일반 수준
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

## 기대 C

### [1] 법률·세무
- 질문: 이 건물(강남구 역삼동 683-39) 팔면 양도세 얼마 나와?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [2] 법률·세무
- 질문: 임대사업자 세금 절감 효과 알려줘
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [3] 대출/금융
- 질문: 이 건물(강남구 역삼동 683-39) 담보로 대출 얼마까지 나올까?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [4] 대출/금융
- 질문: 지금 (강남구 역삼동 683-39) 120억이면 LTV 얼마야?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [5] 권리관계
- 질문: 이 건물(강남구 역삼동 683-39) 명도 가능해?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [6] 권리관계
- 질문: (강남구 역삼동 683-39) 임차인 내보낼 수 있어?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [7] 인허가/건축
- 질문: 이 땅(강남구 역삼동 683-39)에 5층 건물 지을 수 있어?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [8] 인허가/건축
- 질문: 이 건물(서울 영등포구 양평동1가 1-25) 위반건축물이야?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [9] 도로·접도
- 질문: 이 (서울 영등포구 양평동1가 1-25) 땅은 사도 접하나? 건축 가능 여부 봐줘
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [10] 재건축 가능성
- 질문: 이 (서울특별시 용산구 한강로3가 40-280) 재건축 가능성 있어?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [11] 담보평가
- 질문: 이 (서울특별시 용산구 한강로3가 40-280) kb부동산으로 시세가 얼마야?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [12] 재개발 수익성
- 질문: 여기 (서울특별시 용산구 한강로3가 40-280) 재개발 들어가면 얼마 벌어?
- 기대 그룹: C
- 실제 그룹: ERROR
- 기대 답변 유형: 상담전환
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

## 기대 D

### [1] 연예
- 질문: BTS 새 앨범 언제 나와?
- 기대 그룹: D
- 실제 그룹: ERROR
- 기대 답변 유형: 범위외
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [2] 정치
- 질문: 다음 지방 선거 누가 이길 것 같아?
- 기대 그룹: D
- 실제 그룹: ERROR
- 기대 답변 유형: 범위외
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [3] 의료
- 질문: 허리가 아픈데 어느 병원 가야 해?
- 기대 그룹: D
- 실제 그룹: ERROR
- 기대 답변 유형: 범위외
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [4] 진로
- 질문: 퇴사하고 창업하려는데 어떻게 해?
- 기대 그룹: D
- 실제 그룹: ERROR
- 기대 답변 유형: 범위외(혹은 부분 연계)
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [5] 쇼핑
- 질문: 노트북 추천해줘
- 기대 그룹: D
- 실제 그룹: ERROR
- 기대 답변 유형: 범위외
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [6] 자유 대화
- 질문: 심심한데 농담 하나 해줘
- 기대 그룹: D
- 실제 그룹: ERROR
- 기대 답변 유형: 범위외
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [7] 상식
- 질문: 오늘 날씨 어때?
- 기대 그룹: D
- 실제 그룹: ERROR
- 기대 답변 유형: 범위외
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open

### [8] 비부동산
- 질문: 주식 추천해줘
- 기대 그룹: D
- 실제 그룹: ERROR
- 기대 답변 유형: 범위외
- 필수 데이터 소스: —
- 오류: RuntimeError: circuit open for provider=gemini operation=preprocess_structured state=open
