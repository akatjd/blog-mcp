import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

PROFILE_PATH = Path(__file__).parent.parent / "style_profile.json"


# ── URL 감지 & 네이버 블로그 크롤링 ──────────────────────────────────────────

class _TextExtractor(HTMLParser):
    """HTML에서 텍스트만 추출하는 간단한 파서"""
    SKIP_TAGS = {"script", "style", "head", "nav", "footer", "iframe"}

    def __init__(self):
        super().__init__()
        self._skip = 0
        self.texts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data):
        if self._skip == 0:
            text = data.strip()
            if text:
                self.texts.append(text)


def _to_mobile_url(url: str) -> str:
    """네이버 블로그 PC URL → 모바일 URL 변환"""
    # https://blog.naver.com/blogId/logNo
    m = re.match(r"https?://blog\.naver\.com/([^/?]+)/(\d+)", url)
    if m:
        return f"https://m.blog.naver.com/{m.group(1)}/{m.group(2)}"

    # PostView.naver?blogId=...&logNo=...
    m = re.search(r"blogId=([^&]+).*logNo=(\d+)", url)
    if m:
        return f"https://m.blog.naver.com/{m.group(1)}/{m.group(2)}"

    # 이미 모바일 URL이면 그대로
    if "m.blog.naver.com" in url:
        return url

    return url


def fetch_blog_content(url: str) -> str:
    """네이버 블로그 URL에서 본문 텍스트 추출"""
    mobile_url = _to_mobile_url(url)
    req = urllib.request.Request(
        mobile_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; blog-mcp/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    parser = _TextExtractor()
    parser.feed(html)
    text = "\n".join(parser.texts)

    # 너무 길면 앞 5000자만 사용
    return text[:5000]


def is_url(text: str) -> bool:
    return text.strip().startswith("http://") or text.strip().startswith("https://")


def resolve_posts(posts: list[str]) -> tuple[list[str], list[str]]:
    """URL이면 크롤링, 텍스트면 그대로. (resolved, errors) 반환"""
    resolved = []
    errors = []
    for item in posts:
        if is_url(item):
            try:
                content = fetch_blog_content(item.strip())
                if len(content) < 100:
                    errors.append(f"{item} (내용을 가져오지 못했습니다)")
                else:
                    resolved.append(content)
            except Exception as e:
                errors.append(f"{item} (오류: {e})")
        else:
            resolved.append(item)
    return resolved, errors


# ── 스타일 분석 프롬프트 ──────────────────────────────────────────────────────

def build_analysis_prompt(posts: list[str]) -> str:
    numbered = "\n\n".join(
        f"=== 글 {i+1} ===\n{post.strip()}" for i, post in enumerate(posts)
    )
    return f"""아래 네이버 블로그 글 {len(posts)}편을 분석해서 작성자의 고유한 글쓰기 스타일을 파악해주세요.

{numbered}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
분석 후 반드시 save_style_profile 툴을 호출해서 아래 항목을 저장해주세요:

- tone: 전반적인 어조와 성격 (예: "담백하고 솔직한 일상 기록체")
- ending_style: 주로 쓰는 문장 종결 방식 (예: "~했다/~였다 위주, 간혹 ~네 혼용")
- avg_sentence_length: 문장 평균 길이 (짧음/중간/김 + 특징)
- common_expressions: 자주 등장하는 표현이나 단어 (배열, 최대 10개)
- paragraph_structure: 단락 전개 방식 (예: "결론 먼저 → 근거 → 마무리")
- emoji_usage: 이모지 사용 빈도와 패턴 (예: "없음", "음식 관련만 가끔")
- hashtag_count: 해시태그 평균 개수
- hashtag_style: 해시태그 스타일 (예: "긴 문장형", "짧은 키워드형")
- special_patterns: 카테고리별 특이점이나 반복 패턴 (자유 서술)
- do_list: 반드시 지켜야 할 규칙 (배열)
- dont_list: 절대 쓰지 않는 표현/패턴 (배열)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


# ── 스타일 프로필 저장/로드 ───────────────────────────────────────────────────

def save_style_profile(profile: dict) -> dict:
    profile["updated_at"] = datetime.now().strftime("%Y-%m-%d")
    PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return profile


def load_style_profile() -> dict | None:
    if not PROFILE_PATH.exists():
        return None
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_style_instruction(profile: dict) -> str:
    """저장된 스타일 프로필을 템플릿에 주입할 지침 문자열로 변환"""
    do_list = "\n".join(f"   ✅ {item}" for item in profile.get("do_list", []))
    dont_list = "\n".join(f"   ❌ {item}" for item in profile.get("dont_list", []))
    common_expr = ", ".join(f'"{e}"' for e in profile.get("common_expressions", []))

    return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[⚠️ 작성자 개인 스타일 프로필 - 아래 규칙을 최우선으로 준수할 것]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

어조: {profile.get("tone", "")}

【종결체 규칙 - 절대 원칙】
{profile.get("ending_style", "")}
→ 예시 O: "맛있었다", "주문했다", "나왔다", "좋았다"
→ 예시 X: "맛있어요", "주문했어요", "나왔답니다", "좋았네요"

문장 길이: {profile.get("avg_sentence_length", "")}
자주 쓰는 표현: {common_expr}
단락 구조: {profile.get("paragraph_structure", "")}
이모지 규칙: {profile.get("emoji_usage", "")}
해시태그: {profile.get("hashtag_count", "")}개, {profile.get("hashtag_style", "")}
특이 패턴: {profile.get("special_patterns", "")}

반드시 할 것:
{do_list}

절대 하지 말 것:
{dont_list}

(프로필 최종 업데이트: {profile.get("updated_at", "")})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
