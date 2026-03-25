import json
from datetime import datetime
from pathlib import Path

PROFILE_PATH = Path(__file__).parent.parent / "style_profile.json"


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
    do_list = "\n".join(f"   - {item}" for item in profile.get("do_list", []))
    dont_list = "\n".join(f"   - {item}" for item in profile.get("dont_list", []))
    common_expr = ", ".join(f'"{e}"' for e in profile.get("common_expressions", []))

    return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[작성자 개인 스타일 프로필 - 반드시 준수]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

어조: {profile.get("tone", "")}
문장 종결: {profile.get("ending_style", "")}
문장 길이: {profile.get("avg_sentence_length", "")}
자주 쓰는 표현: {common_expr}
단락 구조: {profile.get("paragraph_structure", "")}
이모지: {profile.get("emoji_usage", "")}
해시태그: {profile.get("hashtag_count", "")}개, {profile.get("hashtag_style", "")}
특이 패턴: {profile.get("special_patterns", "")}

반드시 할 것:
{do_list}

절대 하지 말 것:
{dont_list}

(프로필 최종 업데이트: {profile.get("updated_at", "")})"""
