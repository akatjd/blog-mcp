from tools.style_analyzer import load_style_profile, build_style_instruction


def build_investment_prompt(info: dict) -> str:
    topic = info.get("topic", "")
    ticker = info.get("ticker", "")
    purchase_price = info.get("purchase_price", "")
    current_price = info.get("current_price", "")
    analysis = info.get("analysis", "")
    extra = info.get("extra", "")

    ticker_str = f" ({ticker})" if ticker else ""

    profile = load_style_profile()
    style_section = f"\n{build_style_instruction(profile)}\n" if profile else ""

    return f"""[카테고리: 투자 정보]

투자 정보:
- 종목/자산: {topic}{ticker_str}
- 매수 가격: {purchase_price}
- 현재 가격: {current_price}
- 투자 분석: {analysis}
{f"- 추가 메모: {extra}" if extra else ""}
{style_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
블로그 작성 규칙:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 분량: 1500자 이상 (공백 포함) — 체류시간 확보를 위해 충분한 분량 필수

2. 톤/문체:
   - 30대 중반 남성, 냉정하고 분석적인 투자 일지 스타일
   - 감정적 흥분 없이 사실과 판단 근거 중심
   - 투자 권유가 아닌 개인 기록 관점 유지
   - "~했다", "~봤다", "~판단했다" 체 사용

3. 이미지 캡션:
   - 각 사진(차트, 스크린샷 등) 분석 후 [📷 {topic} - 설명] 형식으로 삽입
   - 차트의 핵심 포인트를 캡션에서 짚어줄 것

4. SEO 최적화 제목 (C-Rank·DIA 대응):
   - 실제 검색어 기준으로 작성 (예: "{topic} 주가", "{topic} 매수 후기")
   - 종목명 + 투자 액션 + 키워드 포함
   - 예: "{topic} 매수 후기 — 지금 들어가도 될까 솔직 분석"

5. 키워드 전략 (DIA 점수 향상):
   - 핵심 키워드("{topic}", "{topic} 주가" 등)를 제목·도입부·중반·마무리에 자연스럽게 2~3회 반복
   - 관련 키워드(주식투자, 매수, 분석 등)도 자연스럽게 활용
   - 키워드 억지 반복 금지

6. 신뢰도 확보 요소 (체류시간 향상):
   - 매수 근거를 구체적인 수치·데이터와 함께 서술
   - 리스크도 솔직하게 언급 (독자 신뢰 = 체류시간 증가)

7. 면책 조항 필수 포함:
   "※ 본 글은 개인 투자 기록이며, 투자 권유가 아닙니다. 모든 투자 판단은 본인 책임입니다."

8. 해시태그 (5~7개, 짧은 키워드형):
   - 필수: {topic}, 주식투자, 투자일기
   - 예: #{topic} #주식투자 #투자일기 #매수후기

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
블로그 구조 (이 순서로 작성):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

제목: (SEO 최적화된 제목)

매수 배경 (약 250자)
  └ 왜 이 종목을, 왜 이 시점에 선택했는지
  └ 핵심 키워드 자연스럽게 포함

분석 내용 (약 600자 이상)
  └ 차트/기술적 분석, 펀더멘털, 관련 뉴스
  └ 구체적인 수치·데이터 포함
  └ 📷 차트 캡션 삽입

리스크 (약 200자)
  └ 예상되는 리스크와 나의 대응 전략
  └ 솔직한 단점 언급 (신뢰도 향상)

목표가 & 전략 (약 200자)
  └ 목표 수익률, 손절 기준, 추가 매수 계획
  └ 핵심 키워드 재등장

총평 (약 150자)
  └ 현재 심리 상태, 이 투자에 대한 확신도

면책 조항

해시태그
"""
