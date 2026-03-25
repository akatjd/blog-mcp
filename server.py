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
from templates.restaurant import build_restaurant_prompt
from templates.travel import build_travel_prompt
from templates.investment import build_investment_prompt

app = Server("blog-mcp")

CATEGORY_PROMPTS = {
    "restaurant": build_restaurant_prompt,
    "travel": build_travel_prompt,
    "investment": build_investment_prompt,
}


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
                        "enum": ["restaurant", "travel", "investment"],
                        "description": "블로그 카테고리: restaurant(맛집 리뷰), travel(여행기), investment(투자 정보)",
                    },
                    "info": {
                        "type": "object",
                        "description": (
                            "카테고리별 추가 정보:\n"
                            "- restaurant: {name, location, menu, price_range, rating, extra}\n"
                            "- travel: {destination, travel_date, duration, highlights, extra}\n"
                            "- investment: {topic, ticker, purchase_price, current_price, analysis, extra}"
                        ),
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
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_generate_blog(arguments: dict) -> list:
    image_paths = arguments["image_paths"]
    category = arguments["category"]
    info = arguments["info"]
    save_path = arguments.get("save_path", "")

    images, errors = load_images_as_content(image_paths)

    prompt_builder = CATEGORY_PROMPTS.get(category, build_restaurant_prompt)
    prompt = prompt_builder(info)

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


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
