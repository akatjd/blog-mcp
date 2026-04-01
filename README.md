# blog-mcp

네이버 블로그 포스팅을 자동 생성·발행하는 **MCP(Model Context Protocol) 서버**입니다.
Claude Desktop에 연결하면 사진과 간단한 정보만으로 SEO 최적화된 블로그 글을 즉시 작성할 수 있습니다.

---

## 기능

| 툴 | 설명 |
|---|---|
| `generate_blog` | 이미지 + 정보 → 블로그 초안 자동 생성 |
| `save_draft` | 생성된 글을 파일로 저장 + 히스토리 기록 |
| `list_drafts` | 저장된 초안 목록 조회 |
| `load_draft` | 초안 ID로 내용 불러오기 |
| `delete_draft` | 초안 삭제 |
| `publish_to_naver` | 블로그 글을 클립보드에 복사 (네이버 에디터에 Ctrl+V로 발행) |
| `analyze_style` | 기존 블로그 글(URL 또는 텍스트)로 개인 스타일 분석 및 학습 |
| `save_style_profile` | 분석된 스타일 프로필 저장 (analyze_style 후 자동 호출) |
| `revise_blog` | 작성된 블로그 글을 수정 지시사항에 따라 재작성 |
| `suggest_titles` | SEO 최적화 제목 후보 3개 제안 |

**지원 카테고리**: 맛집 리뷰(`restaurant`) · 여행기(`travel`) · 투자 정보(`investment`)

---

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/akatjd/blog-mcp.git
cd blog-mcp
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

---

## Claude Desktop 연결

### 설정 파일 경로

| 설치 방식 | 경로 |
|---|---|
| Windows Store | `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json` |
| 일반 설치 | `%APPDATA%\Claude\claude_desktop_config.json` |

### 설정 내용 추가

```json
{
  "mcpServers": {
    "blog-mcp": {
      "command": "C:\\Users\\{사용자명}\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\Users\\{사용자명}\\blog-mcp\\server.py"]
    }
  }
}
```

> `{사용자명}`을 실제 Windows 사용자명으로 바꾸세요.
> Python 경로는 `where python` 명령으로 확인할 수 있습니다.

설정 저장 후 **Claude Desktop을 완전히 종료했다가 재시작**하면 커넥터 목록에 `blog-mcp`가 나타납니다.

---

## 사용 예시

### 맛집 리뷰

```
generate_blog 툴로 블로그 써줘:
- 이미지: C:/photos/ramen/   ← 폴더 지정 시 내부 이미지 전체 자동 로드
- 카테고리: restaurant
- 정보: 식당명=멘야무사시, 위치=홍대, 메뉴=라멘/차슈덮밥, 가격대=12000~15000원, 별점=4.5
```

### 여행기

```
generate_blog 툴로 여행 블로그 작성해줘:
- 이미지: C:/photos/osaka1.jpg, C:/photos/osaka2.jpg
- 카테고리: travel
- 정보: 여행지=일본 오사카, 여행날짜=2025년 11월, 기간=3박4일, 주요활동=도톤보리/유니버셜스튜디오/구로몬시장
```

### 투자 정보

```
generate_blog 툴로 투자 일지 써줘:
- 이미지: C:/photos/chart1.png
- 카테고리: investment
- 정보: 종목=삼성전자, 티커=005930, 매수가=58000원, 현재가=62000원, 분석=반도체 사이클 회복 기대
```

### 초안 히스토리 관리

```
list_drafts 툴로 저장된 초안 목록 보여줘

load_draft 툴로 20260325_153012_restaurant 불러와줘

delete_draft 툴로 20260325_153012_restaurant 삭제해줘
```

### 개인 스타일 학습 (최초 1회)

기존에 작성한 블로그 글의 URL 또는 텍스트를 넣으면 스타일을 분석해 이후 모든 글에 자동 반영합니다.

```
analyze_style 툴로 내 블로그 스타일 분석해줘:
- https://blog.naver.com/내아이디/포스팅번호1
- https://blog.naver.com/내아이디/포스팅번호2
- https://blog.naver.com/내아이디/포스팅번호3
```

> URL과 텍스트 직접 붙여넣기를 혼합해서 입력해도 됩니다. 2편 이상 권장.

분석이 완료되면 `save_style_profile` 툴이 자동 호출되어 `style_profile.json`에 저장됩니다.
이후 `generate_blog` 호출 시 저장된 스타일이 자동으로 반영됩니다.
스타일을 업데이트하고 싶을 때는 `analyze_style`을 다시 실행하면 덮어씌워집니다.

### 블로그 글 수정

생성된 글이 마음에 들지 않는 부분이 있을 때 수정 지시만 하면 됩니다.

```
revise_blog 툴로 글 수정해줘:
- 현재 글: (생성된 블로그 내용 붙여넣기)
- 수정 지시: "도입부를 좀 더 자연스럽게 바꿔줘"
```

```
revise_blog 툴로 글 수정해줘:
- 현재 글: (생성된 블로그 내용 붙여넣기)
- 수정 지시: "분량을 500자 더 늘려줘"
```

수정 지시 예시:
- `"도입부를 좀 더 자연스럽게"` — 특정 단락만 수정
- `"분량 늘려줘"` — 전체 분량 증가
- `"마무리 부분 다시 써줘"` — 특정 섹션 재작성
- `"좀 더 담백하게"` — 전체 톤 조정

### 제목 후보 3개 제안

```
suggest_titles 툴로 제목 후보 제안해줘:
- 카테고리: restaurant
- 식당명: 아라참치, 위치: 왕십리, 메뉴: 스페셜
```

맛집은 `[위치] 식당명 - 메뉴` 형식으로 고정 제안됩니다.

### 네이버 블로그 발행

```
publish_to_naver 툴로 방금 작성한 글 클립보드에 복사해줘
- 제목: 홍대 멘야무사시 솔직 후기
- 내용: (생성된 블로그 본문)
```

복사 완료 후:
1. [네이버 블로그 글쓰기](https://blog.naver.com/PostWriteForm.naver) 접속
2. 제목 입력 후 본문 영역에 `Ctrl+V`
3. 발행 클릭

> 네이버 블로그 쓰기 API는 일반 개발자에게 제공되지 않아 클립보드 복사 방식을 사용합니다.

---

## 파일 구조

```
blog-mcp/
├── server.py                 # MCP 서버 진입점
├── requirements.txt
├── naver_config.json         # 네이버 API 인증 정보 (gitignore)
├── tools/
│   ├── image_reader.py       # 이미지 로드 + 리사이즈 (Pillow)
│   ├── draft_manager.py      # 초안 히스토리 관리
│   ├── naver_publisher.py    # 클립보드 복사 (pyperclip)
│   └── style_analyzer.py     # 스타일 분석 + URL 크롤링
├── templates/
│   ├── restaurant.py         # 맛집 리뷰 프롬프트
│   ├── travel.py             # 여행기 프롬프트
│   └── investment.py         # 투자 정보 프롬프트
├── drafts/
│   └── history.json          # 초안 히스토리 (자동 생성)
└── style_profile.json        # 개인 스타일 프로필 (analyze_style 후 자동 생성)
```

---

## 이미지 처리 스펙

- 지원 형식: JPG, PNG, GIF, WebP
- 최대 파일 크기: 20MB
- 자동 리사이즈: 최대 1280px (비율 유지)
- JPEG 품질: 85 (용량 최적화)
- EXIF 회전 자동 보정

---

## License

MIT
