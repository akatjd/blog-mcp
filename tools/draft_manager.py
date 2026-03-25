import json
from datetime import datetime
from pathlib import Path

DRAFTS_FILE = Path(__file__).parent.parent / "drafts" / "history.json"


def _load_db() -> dict:
    DRAFTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DRAFTS_FILE.exists():
        return json.loads(DRAFTS_FILE.read_text(encoding="utf-8"))
    return {"drafts": []}


def _save_db(db: dict) -> None:
    DRAFTS_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_title(content: str) -> str:
    """본문 첫 줄에서 제목 추출"""
    for line in content.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:60]
    return "(제목 없음)"


def save_draft_to_history(content: str, category: str = "") -> dict:
    db = _load_db()
    now = datetime.now()
    draft_id = now.strftime("%Y%m%d_%H%M%S") + (f"_{category}" if category else "")
    draft = {
        "id": draft_id,
        "title": _extract_title(content),
        "category": category,
        "created_at": now.isoformat(timespec="seconds"),
        "char_count": len(content),
        "content": content,
    }
    db["drafts"].insert(0, draft)
    _save_db(db)
    return {k: v for k, v in draft.items() if k != "content"}


def list_drafts(category: str = "") -> list[dict]:
    db = _load_db()
    result = []
    for d in db["drafts"]:
        if category and d.get("category") != category:
            continue
        result.append({k: v for k, v in d.items() if k != "content"})
    return result


def load_draft(draft_id: str) -> str:
    db = _load_db()
    for d in db["drafts"]:
        if d["id"] == draft_id:
            return d.get("content", "")
    raise ValueError(f"초안을 찾을 수 없습니다: {draft_id}")


def delete_draft(draft_id: str) -> str:
    db = _load_db()
    before = len(db["drafts"])
    db["drafts"] = [d for d in db["drafts"] if d["id"] != draft_id]
    if len(db["drafts"]) == before:
        raise ValueError(f"초안을 찾을 수 없습니다: {draft_id}")
    _save_db(db)
    return f"삭제 완료: {draft_id}"
