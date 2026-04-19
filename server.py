import asyncio
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from tools.image_reader import load_images_as_content
from tools.draft_manager import (
    save_draft_to_history,
    list_drafts,
    load_draft,
    delete_draft,
)
from tools.naver_publisher import copy_to_clipboard
from tools.style_analyzer import build_analysis_prompt, save_style_profile, resolve_posts, load_style_profile
from tools import template_loader, info_validator

app = Server("blog-mcp")

CATEGORIES = template_loader.get_categories()


def _build_category_description() -> str:
    parts = []
    for name in CATEGORIES:
        tpl = template_loader.get_template(name)
        parts.append(f"{name}({tpl.get('display_name', name)})")
    return "블로그 카테고리: " + ", ".join(parts)


def _build_info_description() -> str:
    lines = ["카테고리별 추가 정보:"]
    for name in CATEGORIES:
        fields = template_loader.get_fields(name)
        field_strs = []
        for f in fields:
            mark = "" if f.get("required") else "?"
            field_strs.append(f"{f['name']}{mark}")
        lines.append(f"- {name}: {{{', '.join(field_strs)}}}")
    return "\n".join(lines)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_blog",
            description=(
                "사진과 정보를 기반으로 네이버 블로그 포스팅을 자동 생성합니다. "
                "맛집 리뷰, 여행기, 투자 정보 카테고리를 지원하며 "
                "1000자 이상, 30대 중반 남성 톤, SEO 최적화, 이미지 캡션을 포함합니다."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "이미지 파일 경로 또는 폴더 경로 목록. "
                            "폴더를 지정하면 내부 이미지를 자동으로 모두 로드합니다. "
                            "(예: ['C:/photos/food1.jpg'] 또는 ['C:/photos/ramen/'])"
                        ),
                    },
                    "category": {
                        "type": "string",
                        "enum": CATEGORIES,
                        "description": _build_category_description(),
                    },
                    "info": {
                        "type": "object",
                        "description": _build_info_description(),
                    },
                    "save_path": {
                        "type": "string",
                        "description": "저장할 파일 경로 (선택, 예: C:/Users/minsung/blog/post.txt)",
                    },
                },
                "required": ["image_paths", "category", "info"],
            },
        ),
        types.Tool(
            name="save_draft",
            description="생성된 블로그 글을 파일로 저장하고 히스토리에 기록합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "저장할 블로그 내용",
                    },
                    "save_path": {
                        "type": "string",
                        "description": "저장 경로 (예: C:/Users/minsung/blog/post.txt)",
                    },
                    "category": {
                        "type": "string",
                        "description": "블로그 카테고리 (히스토리 분류용, 선택)",
                    },
                },
                "required": ["content", "save_path"],
            },
        ),
        types.Tool(
            name="list_drafts",
            description="저장된 블로그 초안 목록을 조회합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "필터링할 카테고리 (선택, 비우면 전체 조회)",
                    },
                },
            },
        ),
        types.Tool(
            name="load_draft",
            description="초안 ID로 저장된 블로그 글 내용을 불러옵니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {
                        "type": "string",
                        "description": "초안 ID (list_drafts에서 확인 가능)",
                    },
                },
                "required": ["draft_id"],
            },
        ),
        types.Tool(
            name="delete_draft",
            description="초안 ID로 저장된 블로그 초안을 삭제합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {
                        "type": "string",
                        "description": "삭제할 초안 ID",
                    },
                },
                "required": ["draft_id"],
            },
        ),
        types.Tool(
            name="publish_to_naver",
            description=(
                "블로그 제목과 본문을 클립보드에 복사합니다. "
                "복사 후 네이버 블로그 에디터에서 Ctrl+V로 붙여넣기하면 바로 발행할 수 있습니다."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "블로그 포스팅 제목",
                    },
                    "content": {
                        "type": "string",
                        "description": "블로그 본문",
                    },
                },
                "required": ["title", "content"],
            },
        ),
        types.Tool(
            name="analyze_style",
            description=(
                "기존 블로그 글 여러 편을 분석해서 작성자의 고유한 글쓰기 스타일 프로필을 추출합니다. "
                "분석 결과는 이후 generate_blog 호출 시 자동으로 반영됩니다."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "posts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "분석할 기존 블로그 글 텍스트 목록 (2편 이상 권장)",
                    },
                },
                "required": ["posts"],
            },
        ),
        types.Tool(
            name="revise_blog",
            description=(
                "작성된 블로그 글을 수정 지시사항에 따라 재작성합니다. "
                "도입부 다시 쓰기, 분량 늘리기, 특정 단락 수정 등 자유롭게 지시할 수 있습니다."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "현재 블로그 글 내용",
                    },
                    "instruction": {
                        "type": "string",
                        "description": (
                            "수정 지시사항 (예: '도입부를 좀 더 자연스럽게', "
                            "'분량을 500자 더 늘려줘', '마무리 부분을 다시 써줘')"
                        ),
                    },
                    "category": {
                        "type": "string",
                        "description": "블로그 카테고리 (선택)",
                    },
                },
                "required": ["content", "instruction"],
            },
        ),
        types.Tool(
            name="suggest_titles",
            description=(
                "블로그 정보를 기반으로 SEO 최적화된 제목 후보 3개를 제안합니다. "
                "마음에 드는 제목을 선택해서 사용하세요."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": CATEGORIES,
                        "description": "블로그 카테고리",
                    },
                    "info": {
                        "type": "object",
                        "description": "카테고리별 정보 (generate_blog와 동일한 info 형식)",
                    },
                },
                "required": ["category", "info"],
            },
        ),
        types.Tool(
            name="save_style_profile",
            description="analyze_style 분석 결과를 스타일 프로필로 저장합니다. analyze_style 툴 호출 후 Claude가 자동으로 호출합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tone": {"type": "string", "description": "전반적인 어조와 성격"},
                    "ending_style": {"type": "string", "description": "문장 종결 방식"},
                    "avg_sentence_length": {"type": "string", "description": "문장 평균 길이 특징"},
                    "common_expressions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "자주 쓰는 표현/단어 목록",
                    },
                    "paragraph_structure": {"type": "string", "description": "단락 전개 방식"},
                    "emoji_usage": {"type": "string", "description": "이모지 사용 패턴"},
                    "hashtag_count": {"type": "string", "description": "해시태그 평균 개수"},
                    "hashtag_style": {"type": "string", "description": "해시태그 스타일"},
                    "special_patterns": {"type": "string", "description": "특이점이나 반복 패턴"},
                    "do_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "반드시 지켜야 할 규칙",
                    },
                    "dont_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "절대 쓰지 않는 표현/패턴",
                    },
                },
                "required": ["tone", "ending_style", "do_list", "dont_list"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list:
    if name == "generate_blog":
        return await handle_generate_blog(arguments)
    elif name == "save_draft":
        return handle_save_draft(arguments)
    elif name == "list_drafts":
        return handle_list_drafts(arguments)
    elif name == "load_draft":
        return handle_load_draft(arguments)
    elif name == "delete_draft":
        return handle_delete_draft(arguments)
    elif name == "publish_to_naver":
        return handle_publish_to_naver(arguments)
    elif name == "revise_blog":
        return handle_revise_blog(arguments)
    elif name == "suggest_titles":
        return handle_suggest_titles(arguments)
    elif name == "analyze_style":
        return handle_analyze_style(arguments)
    elif name == "save_style_profile":
        return handle_save_style_profile(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_generate_blog(arguments: dict) -> list:
    image_paths = arguments["image_paths"]
    category = arguments["category"]
    info = arguments["info"]
    save_path = arguments.get("save_path", "")

    validated, err = info_validator.validate(category, info)
    if err:
        return [types.TextContent(type="text", text=err)]

    images, errors = load_images_as_content(image_paths)

    try:
        prompt = template_loader.build_prompt(category, validated)
    except ValueError as e:
        return [types.TextContent(type="text", text=f"❌ {e}")]

    error_text = ""
    if errors:
        error_text = "\n⚠️ 로드 실패한 이미지:\n" + "\n".join(f"  - {e}" for e in errors)

    instruction = f"""📸 이미지 {len(images)}장을 분석하여 아래 지침에 따라 네이버 블로그 글을 작성해주세요.{error_text}

{prompt}
{"" if not save_path else f"{chr(10)}💾 작성 완료 후 save_draft 툴로 다음 경로에 저장해주세요: {save_path}"}"""

    content: list = [types.TextContent(type="text", text=instruction)]
    for img in images:
        content.append(
            types.ImageContent(type="image", data=img["data"], mimeType=img["media_type"])
        )

    return content


def handle_save_draft(arguments: dict) -> list[types.TextContent]:
    content = arguments["content"]
    save_path = arguments["save_path"]
    category = arguments.get("category", "")

    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    meta = save_draft_to_history(content, category)

    char_count = len(content)
    status = "✅" if char_count >= 1000 else "⚠️ (1000자 미만)"

    return [
        types.TextContent(
            type="text",
            text=(
                f"{status} 저장 완료: {save_path}\n"
                f"📄 글자 수: {char_count:,}자\n"
                f"🗂️ 히스토리 ID: {meta['id']}"
            ),
        )
    ]


def handle_list_drafts(arguments: dict) -> list[types.TextContent]:
    category = arguments.get("category", "")
    drafts = list_drafts(category)

    if not drafts:
        msg = "저장된 초안이 없습니다."
    else:
        lines = [f"📋 초안 목록 ({len(drafts)}개)\n"]
        for d in drafts:
            cat = f"[{d['category']}] " if d.get("category") else ""
            lines.append(
                f"• {d['id']}\n"
                f"  {cat}{d['title']}\n"
                f"  {d['created_at']} · {d['char_count']:,}자"
            )
        msg = "\n".join(lines)

    return [types.TextContent(type="text", text=msg)]


def handle_load_draft(arguments: dict) -> list[types.TextContent]:
    draft_id = arguments["draft_id"]
    try:
        content = load_draft(draft_id)
        return [types.TextContent(type="text", text=content)]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"❌ {e}")]


def handle_delete_draft(arguments: dict) -> list[types.TextContent]:
    draft_id = arguments["draft_id"]
    try:
        msg = delete_draft(draft_id)
        return [types.TextContent(type="text", text=f"🗑️ {msg}")]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"❌ {e}")]


def handle_publish_to_naver(arguments: dict) -> list[types.TextContent]:
    title = arguments["title"]
    content = arguments["content"]

    result = copy_to_clipboard(title, content)
    return [
        types.TextContent(
            type="text",
            text=(
                f"📋 클립보드에 복사 완료! ({result['char_count']:,}자)\n\n"
                f"아래 순서로 붙여넣기 하세요:\n"
                f"1. {result['blog_url']} 접속\n"
                f"2. 제목 입력란에 제목 붙여넣기\n"
                f"3. 본문 영역에 내용 붙여넣기\n"
                f"4. 발행 클릭"
            ),
        )
    ]


def handle_revise_blog(arguments: dict) -> list[types.TextContent]:
    content = arguments["content"]
    instruction = arguments["instruction"]
    category = arguments.get("category", "")

    profile = load_style_profile()
    style_note = ""
    if profile:
        style_note = (
            f"\n\n[스타일 규칙 준수]\n"
            f"- 종결체: {profile.get('ending_style', '')}\n"
            f"- 이모지: {profile.get('emoji_usage', '')}\n"
            f"- 마크다운 절대 금지 (##헤더, **굵은글씨**, 불릿 등)"
        )

    prompt = f"""아래 블로그 글을 수정 지시사항에 따라 재작성해주세요.

[수정 지시사항]
{instruction}

[현재 블로그 글]
{content}

[재작성 규칙]
- 수정 지시한 부분만 변경하고 나머지는 최대한 유지
- 마크다운 문법 절대 사용 금지 (네이버 블로그 미지원)
- 일반 텍스트와 줄바꿈만 사용
- 1500자 이상 유지{style_note}

수정된 전체 글을 출력해주세요."""

    return [types.TextContent(type="text", text=prompt)]


def handle_suggest_titles(arguments: dict) -> list[types.TextContent]:
    category = arguments["category"]
    info = arguments["info"]

    validated, err = info_validator.validate(category, info)
    if err:
        return [types.TextContent(type="text", text=err)]
    info = validated

    if category == "restaurant":
        name = info.get("name", "")
        location = info.get("location", "")
        menu = info.get("menu", "")
        prompt = f"""맛집 블로그 제목 후보 3개를 제안해주세요.

정보:
- 식당명: {name}
- 위치: {location}
- 메뉴: {menu}

제목 형식 (반드시 준수):
- 국내: [{location}] {name} - 메뉴명
- 해외: [나라/도시] {name} - 메뉴명
- 예시: [왕십리/상왕십리] 아라참치 - 스페셜
- 예시: [일본/나고야] 야바톤 센트라이즈점 - 미소카츠

3개의 제목을 번호로 나열해주세요. 각 제목마다 한 줄 설명(어떤 포인트를 강조했는지)도 추가해주세요."""

    elif category == "travel":
        destination = info.get("destination", "")
        duration = info.get("duration", "")
        travel_date = info.get("travel_date", "")
        highlights = info.get("highlights", "")
        prompt = f"""여행 블로그 제목 후보 3개를 제안해주세요.

정보:
- 여행지: {destination}
- 기간: {duration}
- 날짜: {travel_date}
- 주요 방문지: {highlights}

조건:
- 실제 검색어 기반 (예: "{destination} 여행", "{destination} 맛집")
- 여행지 + 기간 + 핵심 키워드 포함
- 느낌표, 마침표 없이 담백하게

3개의 제목을 번호로 나열하고 각 제목의 SEO 포인트를 한 줄로 설명해주세요."""

    else:  # investment
        topic = info.get("topic", "")
        ticker = info.get("ticker", "")
        ticker_str = f" ({ticker})" if ticker else ""
        prompt = f"""투자 블로그 제목 후보 3개를 제안해주세요.

정보:
- 종목/자산: {topic}{ticker_str}

조건:
- 실제 검색어 기반 (예: "{topic} 주가", "{topic} 매수")
- 종목명 + 투자 액션 + 키워드 포함
- 과장 없이 분석적인 톤

3개의 제목을 번호로 나열하고 각 제목의 SEO 포인트를 한 줄로 설명해주세요."""

    return [types.TextContent(type="text", text=prompt)]


def handle_analyze_style(arguments: dict) -> list[types.TextContent]:
    posts = arguments["posts"]
    if not posts:
        return [types.TextContent(type="text", text="❌ 분석할 글이 없습니다.")]

    resolved, errors = resolve_posts(posts)

    error_text = ""
    if errors:
        error_text = "\n⚠️ 가져오지 못한 항목:\n" + "\n".join(f"  - {e}" for e in errors)

    if not resolved:
        return [types.TextContent(type="text", text=f"❌ 분석 가능한 글이 없습니다.{error_text}")]

    prompt = build_analysis_prompt(resolved)
    return [types.TextContent(type="text", text=prompt + error_text)]


def handle_save_style_profile(arguments: dict) -> list[types.TextContent]:
    profile = save_style_profile(arguments)
    do_list = "\n".join(f"  ✅ {item}" for item in profile.get("do_list", []))
    dont_list = "\n".join(f"  ❌ {item}" for item in profile.get("dont_list", []))
    return [
        types.TextContent(
            type="text",
            text=(
                f"✨ 스타일 프로필 저장 완료! (업데이트: {profile.get('updated_at')})\n\n"
                f"어조: {profile.get('tone')}\n"
                f"종결체: {profile.get('ending_style')}\n"
                f"문장 길이: {profile.get('avg_sentence_length')}\n"
                f"단락 구조: {profile.get('paragraph_structure')}\n"
                f"이모지: {profile.get('emoji_usage')}\n"
                f"해시태그: {profile.get('hashtag_count')}개 / {profile.get('hashtag_style')}\n\n"
                f"반드시 할 것:\n{do_list}\n\n"
                f"절대 하지 말 것:\n{dont_list}\n\n"
                f"이제 generate_blog 호출 시 이 스타일이 자동으로 반영됩니다."
            ),
        )
    ]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
