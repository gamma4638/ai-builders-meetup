#!/usr/bin/env python3
"""
AI Builders Meetup 이름표 생성 스크립트
Figma 디자인 기반 이름표 56개 생성
"""

import csv
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import urllib.request

# 디렉토리 설정
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent  # 2-echo-delta/
OUTPUT_DIR = BASE_DIR / "nametags"
OUTPUT_DIR.mkdir(exist_ok=True)

# 이미지 에셋
ASSETS_DIR = BASE_DIR / "assets"
QR_CODE_PATH = ASSETS_DIR / "qr_code.png"
SOCAR_LOGO_PATH = ASSETS_DIR / "socar_logo.png"
ROCKET_ICON_PATH = ASSETS_DIR / "rocket_icon.png"

# 참석자 데이터
ATTENDEE_DIR = BASE_DIR / "attendee"

# 이름표 사이즈 (Figma 기준)
WIDTH = 718  # 359 * 2 for high resolution
HEIGHT = 922  # 461 * 2 for high resolution

# 색상
BLUE = (0, 120, 255)
WHITE = (255, 255, 255)
LIGHT_BLUE = (183, 207, 255)
GRAY = (209, 213, 220)

# 폰트 설정 - macOS 시스템 폰트 사용
def get_font(size: int, bold: bool = False):
    """시스템 폰트 로드"""
    font_paths = [
        # macOS 한글 폰트
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        # 기본 폰트
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue

    return ImageFont.load_default()


def get_emoji_font(size: int):
    """Apple Color Emoji 폰트 로드"""
    emoji_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
    if os.path.exists(emoji_path):
        try:
            return ImageFont.truetype(emoji_path, size)
        except:
            pass
    return None


def draw_rounded_rectangle(draw, xy, radius, fill):
    """둥근 모서리 사각형 그리기"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill)
    draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill)


def create_nametag(name: str, organization: str, index: int, qr_img: Image.Image, socar_img: Image.Image, rocket_img: Image.Image = None):
    """이름표 이미지 생성 - Figma 원본 좌표 기준 (2배 스케일)"""
    # Figma 원본: 359 x 461px -> 2배: 718 x 922px
    SCALE = 2

    # 이미지 생성
    img = Image.new('RGB', (WIDTH, HEIGHT), BLUE)
    draw = ImageDraw.Draw(img)

    # 배경 장식 원 (반투명 효과)
    # Figma: 오른쪽 상단 원 left:295, top:-64, size:128
    # Figma: 왼쪽 하단 원 left:-48, top:413, size:96
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.ellipse([590, -128, 590 + 256, -128 + 256], fill=(255, 255, 255, 13))
    overlay_draw.ellipse([-96, 826, -96 + 192, 826 + 192], fill=(255, 255, 255, 13))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    # 폰트 (Figma 원본 크기 * 2)
    title_font = get_font(60)       # Figma: 30px
    subtitle_font = get_font(36)    # Figma: 18px
    label_font = get_font(20)       # Figma: 10px

    # AI Builders Meetup - Figma: top ~40px (29 + 11.5)
    title = "AI Builders Meetup"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((WIDTH - title_width) / 2, 80), title, font=title_font, fill=WHITE)

    # Echo & Delta - Figma: 아래에 바로 이어짐
    subtitle = "Echo & Delta"
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(((WIDTH - subtitle_width) / 2, 154), subtitle, font=subtitle_font, fill=WHITE)

    # by Team Attention - Figma: 같은 텍스트 블록 내 다음 줄
    byline = "by Team Attention"
    byline_bbox = draw.textbbox((0, 0), byline, font=subtitle_font)
    byline_width = byline_bbox[2] - byline_bbox[0]
    draw.text(((WIDTH - byline_width) / 2, 196), byline, font=subtitle_font, fill=(158, 200, 248))

    # QR 코드 박스 - Figma: left:31, top:154, size:66x66
    qr_box_x, qr_box_y = 62, 308
    qr_box_size = 132
    draw_rounded_rectangle(draw, [qr_box_x, qr_box_y, qr_box_x + qr_box_size, qr_box_y + qr_box_size], 20, WHITE)
    # QR 이미지 - Figma: left:36, top:159, size:56.49
    qr_resized = qr_img.resize((113, 113), Image.Resampling.LANCZOS)
    img.paste(qr_resized, (72, 318))

    # "밋업 안내" - Figma: left:63.5 (centered), top:227
    label = "밋업 안내"
    label_bbox = draw.textbbox((0, 0), label, font=label_font)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text((127 - label_width / 2, 454), label, font=label_font, fill=LIGHT_BLUE)

    # Socar 박스 - Figma: left:115, top:154, size:226x66
    socar_box_x, socar_box_y = 230, 308
    socar_box_w, socar_box_h = 452, 132
    draw_rounded_rectangle(draw, [socar_box_x, socar_box_y, socar_box_x + socar_box_w, socar_box_y + socar_box_h], 20, WHITE)
    # Socar 로고 - 박스 내부 padding 12px*2=24px
    socar_resized = socar_img.resize((404, 88), Image.Resampling.LANCZOS)
    img.paste(socar_resized, (254, 330), socar_resized if socar_resized.mode == 'RGBA' else None)

    # "Sponsor" - Figma: left:227.5 (centered), top:228
    sponsor_label = "Sponsor"
    sponsor_bbox = draw.textbbox((0, 0), sponsor_label, font=label_font)
    sponsor_width = sponsor_bbox[2] - sponsor_bbox[0]
    draw.text((455 - sponsor_width / 2, 456), sponsor_label, font=label_font, fill=LIGHT_BLUE)

    # 이름/소속 흰색 박스 - Figma: left:24, top:279, size:311x204 (하단은 캔버스 밖으로 나감)
    name_box_x, name_box_y = 48, 558
    name_box_w, name_box_h = 622, 408
    draw_rounded_rectangle(draw, [name_box_x, name_box_y, name_box_x + name_box_w, name_box_y + name_box_h], 20, WHITE)

    # 이름 텍스트 - 박스 내부 padding-top 24px*2=48px, 첫 영역 높이 70px*2=140px
    name_font = get_font(56)
    name_bbox = draw.textbbox((0, 0), name, font=name_font)
    name_width = name_bbox[2] - name_bbox[0]
    name_height = name_bbox[3] - name_bbox[1]
    name_x = (WIDTH - name_width) / 2
    # 이름을 밑줄 바로 위에 배치
    name_underline_y = 558 + 48 + 130  # 736
    draw.text((name_x, name_underline_y - name_height - 20), name, font=name_font, fill=(0, 0, 0))

    # 이름 아래 밑줄 - Figma: 박스 padding 24px 내부, 첫 영역 밑줄
    draw.line([96, name_underline_y, 622, name_underline_y], fill=GRAY, width=4)

    # 소속 텍스트 - gap 20px*2=40px 후
    org_font = get_font(32)
    org_underline_y = name_underline_y + 40 + 76  # 852
    if organization:
        # 로켓 아이콘이 포함된 경우 (🚀Stealth) 별도 처리
        if organization.startswith("🚀") and rocket_img:
            text = organization[1:]  # "Stealth"

            # 아이콘과 텍스트 크기 계산
            icon_size = 28
            rocket_resized = rocket_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            text_bbox = draw.textbbox((0, 0), text, font=org_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            total_width = icon_size + 8 + text_width  # 8px gap
            start_x = (WIDTH - total_width) / 2
            text_y = org_underline_y - text_height - 16

            # 로켓 아이콘 렌더링
            icon_y = int(text_y + (text_height - icon_size) / 2)
            img.paste(rocket_resized, (int(start_x), icon_y), rocket_resized)

            # 텍스트 렌더링
            draw.text((start_x + icon_size + 8, text_y), text, font=org_font, fill=(100, 100, 100))
        else:
            org_bbox = draw.textbbox((0, 0), organization, font=org_font)
            org_width = org_bbox[2] - org_bbox[0]
            org_height = org_bbox[3] - org_bbox[1]
            org_x = (WIDTH - org_width) / 2
            draw.text((org_x, org_underline_y - org_height - 16), organization, font=org_font, fill=(100, 100, 100))

    # 소속 아래 밑줄
    draw.line([96, org_underline_y, 622, org_underline_y], fill=GRAY, width=4)

    # 파일 저장
    filename = f"{index:02d}_{name.replace(' ', '_')}.png"
    filepath = OUTPUT_DIR / filename
    img.save(filepath, "PNG", quality=95)
    print(f"생성됨: {filename}")
    return filepath


def load_attendees(csv_path: str) -> list:
    """CSV에서 참석자 목록 로드"""
    attendees = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('이름', '').strip()
            org = row.get('소속', '').strip()
            role = row.get('종류', '').strip()

            if name:
                # 호스트/스피커는 이름 앞에 태그 추가
                if role == '호스트':
                    name = f"[Host] {name}"
                elif role == '스피커':
                    name = f"[Speaker] {name}"

                # 소속이 비어있으면 🚀Stealth
                if not org:
                    org = "🚀Stealth"

                attendees.append({'name': name, 'organization': org})
    return attendees


def main():
    csv_path = ATTENDEE_DIR / "attendees.csv"

    print(f"CSV 파일 로드: {csv_path}")
    attendees = load_attendees(csv_path)
    print(f"총 {len(attendees)}명의 참석자 발견")

    # 에셋 이미지 로드
    print("\n에셋 이미지 로드 중...")
    qr_img = Image.open(QR_CODE_PATH).convert('RGB')
    socar_img = Image.open(SOCAR_LOGO_PATH).convert('RGBA')
    rocket_img = Image.open(ROCKET_ICON_PATH).convert('RGBA') if ROCKET_ICON_PATH.exists() else None
    print(f"  - QR 코드: {QR_CODE_PATH}")
    print(f"  - Socar 로고: {SOCAR_LOGO_PATH}")
    print(f"  - 로켓 아이콘: {ROCKET_ICON_PATH}")

    print(f"\n이름표 생성 시작... (저장 위치: {OUTPUT_DIR})")

    for i, attendee in enumerate(attendees, 1):
        create_nametag(attendee['name'], attendee['organization'], i, qr_img, socar_img, rocket_img)

    print(f"\n✅ 완료! {len(attendees)}개의 이름표가 생성되었습니다.")
    print(f"📁 저장 위치: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
