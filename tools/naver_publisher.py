import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "naver_config.json"
NAVER_BLOG_API = "https://openapi.naver.com/blog/writePost.json"
NAVER_TOKEN_API = "https://nid.naver.com/oauth2.0/token"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise ValueError(
            f"naver_config.json이 없습니다. {CONFIG_PATH} 파일을 생성하고 "
            "client_id, client_secret, access_token, refresh_token, blog_id를 입력하세요."
        )
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    required = ["client_id", "client_secret", "access_token", "blog_id"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        raise ValueError(f"naver_config.json에 다음 항목이 비어 있습니다: {', '.join(missing)}")
    return config


def _save_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def _refresh_access_token(config: dict) -> str:
    refresh_token = config.get("refresh_token", "")
    if not refresh_token:
        raise ValueError("naver_config.json에 refresh_token이 없습니다. 재로그인이 필요합니다.")

    params = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "refresh_token": refresh_token,
    }).encode("utf-8")

    req = urllib.request.Request(NAVER_TOKEN_API, data=params, method="POST")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    new_token = data.get("access_token")
    if not new_token:
        raise ValueError(f"토큰 갱신 실패: {data}")

    config["access_token"] = new_token
    _save_config(config)
    return new_token


def _post_to_naver(config: dict, title: str, content: str, category_no: int) -> dict:
    params = urllib.parse.urlencode({
        "blogId": config["blog_id"],
        "title": title,
        "contents": content,
        "categoryNo": str(category_no),
        "isPublic": "1",
    }).encode("utf-8")

    req = urllib.request.Request(NAVER_BLOG_API, data=params, method="POST")
    req.add_header("Authorization", f"Bearer {config['access_token']}")
    req.add_header("X-Naver-Client-Id", config["client_id"])
    req.add_header("X-Naver-Client-Secret", config["client_secret"])

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def publish_to_naver(title: str, content: str, category_no: int = 0) -> dict:
    config = _load_config()

    try:
        result = _post_to_naver(config, title, content, category_no)
        return {"success": True, "result": result}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            # 토큰 만료 → 갱신 후 재시도
            _refresh_access_token(config)
            try:
                result = _post_to_naver(config, title, content, category_no)
                return {"success": True, "result": result}
            except urllib.error.HTTPError as e2:
                body = e2.read().decode("utf-8")
                return {"success": False, "error": body, "status_code": e2.code}
        body = e.read().decode("utf-8")
        return {"success": False, "error": body, "status_code": e.code}
