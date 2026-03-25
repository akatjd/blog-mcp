import base64
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image, ImageOps
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE_MB = 20
MAX_DIMENSION = 1280
JPEG_QUALITY = 85


def _collect_paths(path_str: str) -> tuple[list[str], list[str]]:
    """파일 또는 폴더 경로를 받아 이미지 파일 경로 목록으로 확장"""
    p = Path(path_str)
    if p.is_dir():
        files = sorted(
            str(f) for f in p.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
        )
        if not files:
            return [], [f"{path_str} (폴더에 이미지 없음)"]
        return files, []
    return [path_str], []


def _resize_image(path: Path) -> tuple[bytes, str]:
    """Pillow로 이미지를 리사이즈하고 (bytes, media_type)을 반환"""
    with Image.open(path) as img:
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        if max(img.size) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

        # 투명도 채널 처리
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            buf = BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue(), "image/png"
        else:
            img = img.convert("RGB")
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            return buf.getvalue(), "image/jpeg"


def load_images_as_content(image_paths: list[str]) -> tuple[list[dict], list[str]]:
    images = []
    errors = []

    # 폴더 경로 확장
    expanded_paths = []
    for path_str in image_paths:
        paths, errs = _collect_paths(path_str)
        expanded_paths.extend(paths)
        errors.extend(errs)

    for path_str in expanded_paths:
        path = Path(path_str)

        if not path.exists():
            errors.append(f"{path_str} (파일 없음)")
            continue

        if path.suffix.lower() not in SUPPORTED_FORMATS:
            errors.append(f"{path.name} (지원하지 않는 형식: {path.suffix})")
            continue

        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            errors.append(f"{path.name} ({size_mb:.1f}MB, {MAX_FILE_SIZE_MB}MB 초과)")
            continue

        try:
            if HAS_PILLOW:
                raw_data, media_type = _resize_image(path)
            else:
                with open(path, "rb") as f:
                    raw_data = f.read()
                ext = path.suffix.lower().lstrip(".")
                media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

            data = base64.standard_b64encode(raw_data).decode("utf-8")
            images.append({
                "path": path_str,
                "name": path.name,
                "data": data,
                "media_type": media_type,
            })
        except Exception as e:
            errors.append(f"{path.name} (읽기 오류: {e})")

    return images, errors
