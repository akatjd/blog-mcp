# Blog MCP - Claude Desktop 설정 가이드

## 1. 패키지 설치

```bash
cd C:\Users\minsung\blog-mcp
pip install -r requirements.txt
```

## 2. Claude Desktop 설정 파일 수정

설정 파일 경로:
`C:\Users\minsung\AppData\Roaming\Claude\claude_desktop_config.json`

아래 내용을 추가하세요:

```json
{
  "mcpServers": {
    "blog-mcp": {
      "command": "python",
      "args": ["C:\\Users\\minsung\\blog-mcp\\server.py"]
    }
  }
}
```

> ⚠️ 기존에 다른 MCP 서버가 있다면 `mcpServers` 안에 추가만 하면 됩니다.

## 3. Claude Desktop 재시작

설정 저장 후 Claude Desktop을 완전히 종료했다가 다시 실행하세요.

## 4. 사용 예시

### 맛집 리뷰
```
generate_blog 툴을 사용해서 블로그 써줘:
- 이미지: C:/Users/minsung/photos/ramen1.jpg, C:/Users/minsung/photos/ramen2.jpg
- 카테고리: restaurant
- 정보: 식당명=멘야무사시, 위치=홍대, 메뉴=라멘/차슈덮밥, 가격대=12000~15000원, 별점=4.5
```

### 여행기
```
generate_blog 툴로 여행 블로그 작성해줘:
- 이미지: C:/Users/minsung/photos/osaka1.jpg, C:/Users/minsung/photos/osaka2.jpg
- 카테고리: travel
- 정보: 여행지=일본 오사카, 여행날짜=2025년 11월, 기간=3박4일, 주요활동=도톤보리/유니버셜스튜디오/구로몬시장
```

### 투자 정보
```
generate_blog 툴로 투자 일지 써줘:
- 이미지: C:/Users/minsung/photos/chart1.png
- 카테고리: investment
- 정보: 종목=삼성전자, 티커=005930, 매수가=58000원, 현재가=62000원, 분석=반도체 사이클 회복 기대
```
