import pyperclip

NAVER_BLOG_WRITE_URL = "https://blog.naver.com/PostWriteForm.naver"


def copy_to_clipboard(title: str, content: str) -> dict:
    text = f"{title}\n\n{content}"
    pyperclip.copy(text)
    char_count = len(text)
    return {
        "success": True,
        "char_count": char_count,
        "blog_url": NAVER_BLOG_WRITE_URL,
    }
