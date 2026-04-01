from tools.style_analyzer import load_style_profile, build_style_instruction


def build_travel_prompt(info: dict) -> str:
    destination = info.get("destination", "")
    travel_date = info.get("travel_date", "")
    duration = info.get("duration", "")
    highlights = info.get("highlights", "")
    extra = info.get("extra", "")

    profile = load_style_profile()
    style_section = f"\n{build_style_instruction(profile)}\n" if profile else ""

    return f"""[카테고리: 여행기]

여행 정보:
- 여행지: {destination}
- 여행 날짜: {travel_date}
- 여행 기간: {duration}
- 주요 방문지/활동: {highlights}
{f"- 추가 메모: {extra}" if extra else ""}
{style_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
블로그 작성 규칙:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 분량: 1500자 이상 (공백 포함) — 체류시간 확보를 위해 충분한 분량 필수

2. 톤/문체:
   - 30대 중반 남성, 담담하면서도 감성적인 여행 기록 스타일
   - 여행 중 느낀 감정과 관찰을 솔직하게
   - 여행 팁은 자연스럽게 본문에 녹여서 (리스트 과도 사용 X)
   - "~했다", "~였다" 체 사용

3. 이미지 캡션:
   - 각 사진 분석 후 [📷 {destination} - 설명] 형식으로 본문에 삽입
   - 장소/상황을 구체적으로 설명
   - 사진은 최소 5장 이상 활용 권장

4. SEO 최적화 제목 (C-Rank·DIA 대응):
   - 실제 검색어 기준으로 작성 (예: "{destination} 여행", "{destination} 맛집")
   - 여행지 + 기간 + 핵심 키워드 포함
   - 예: "{destination} {duration} 여행 — {travel_date} 솔직 후기 및 루트 총정리"

5. 키워드 전략 (DIA 점수 향상):
   - 핵심 키워드("{destination} 여행", "{destination} 맛집" 등)를 제목·도입부·중반·마무리에 자연스럽게 2~3회 반복
   - 방문한 장소명도 키워드로 활용
   - 키워드 억지 반복 금지 — 자연스럽게 녹여야 함

6. 실용 정보 포함 (체류시간 향상):
   - 교통편, 이동 시간, 입장료, 영업시간 등 실용적인 정보 1~2가지 포함
   - 독자가 참고할 수 있는 팁이 있으면 체류시간 증가

7. 해시태그 (5~7개, 짧은 키워드형):
   - 필수: {destination}여행, {destination}맛집, 여행스타그램
   - 예: #{destination}여행 #{duration}여행 #여행스타그램 #여행일기

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
블로그 구조 (이 순서로 작성):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

제목: (SEO 최적화된 제목)

도입부 (약 200자)
  └ 여행 동기, 출발 전 마음 상태
  └ 핵심 키워드 자연스럽게 포함

여행 이야기 (약 700자 이상)
  └ 날짜별 또는 장소별로 전개
  └ 각 장소마다 📷 캡션 삽입
  └ 인상적인 순간이나 에피소드 포함
  └ 중간에 실용 정보(교통·입장료 등) 자연스럽게 삽입

음식 & 숙소 (약 250자)
  └ 기억에 남는 식사, 숙소 솔직 평가 + 📷 캡션
  └ 가격 구체적으로 언급

여행 팁 (약 150자)
  └ 실용적인 꿀팁 2~3가지 (검색 유입 증가 효과)
  └ 핵심 키워드 재등장

총평 (약 150자)
  └ 여행 소감, 다음에 또 올 것인지
  └ 재방문 의향 언급

해시태그
"""
