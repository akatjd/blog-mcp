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

1. 분량: 1000자 이상 (공백 포함)

2. 톤/문체:
   - 30대 중반 남성, 담담하면서도 감성적인 여행 기록 스타일
   - 여행 중 느낀 감정과 관찰을 솔직하게
   - 여행 팁은 자연스럽게 본문에 녹여서 (리스트 과도 사용 X)
   - "~했다", "~였다" 체 사용

3. 이미지 캡션:
   - 각 사진 분석 후 [📷 {destination} - 설명] 형식으로 본문에 삽입
   - 장소/상황을 구체적으로 설명

4. SEO 최적화 제목:
   - 여행지 + 기간 + 키워드 포함
   - 예: "일본 오사카 {duration} - 혼자 떠난 {travel_date} 여행 루트 총정리"

5. 해시태그: 7~10개 (여행지명여행, 기간여행, 여행스타그램, 혼행 등)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
블로그 구조 (이 순서로 작성):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

제목: (SEO 최적화된 제목)

도입부 (약 150자)
  └ 여행 동기, 출발 전 마음 상태

여행 이야기 (약 500자 이상)
  └ 날짜별 또는 장소별로 전개
  └ 각 장소마다 📷 캡션 삽입
  └ 인상적인 순간이나 에피소드 포함

음식 & 숙소 (약 200자)
  └ 기억에 남는 식사, 숙소 솔직 평가 + 📷 캡션

여행 팁 (약 100자)
  └ 실용적인 꿀팁 2~3가지 (자연스럽게)

총평 (약 100자)
  └ 여행 소감, 다음에 또 올 것인지

해시태그
"""
