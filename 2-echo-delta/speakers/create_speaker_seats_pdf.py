#!/usr/bin/env python3
"""Speaker Seats 명패 PDF 생성

A4를 가로로 4등분해서 접어 사용하는 명패
- 섹션 2: 앞면 텍스트 (정방향)
- 섹션 3: 뒷면 텍스트 (뒤집힘)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path

# A4: 210mm x 297mm
WIDTH, HEIGHT = A4
SECTION_HEIGHT = HEIGHT / 4

# 출력 경로
OUTPUT_PATH = Path(__file__).parent / "speaker-seats.pdf"


def create_pdf():
    c = canvas.Canvas(str(OUTPUT_PATH), pagesize=A4)

    # 접는 선 그리기 (점선)
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setDash(3, 3)
    for i in range(1, 4):
        y = i * SECTION_HEIGHT
        c.line(10 * mm, y, WIDTH - 10 * mm, y)

    c.setDash()  # 점선 해제

    # 텍스트 설정
    text = "Speaker Seats"
    font_name = "Helvetica-Bold"
    font_size = 48

    c.setFont(font_name, font_size)
    c.setFillColorRGB(0.1, 0.1, 0.1)

    # 텍스트 너비 계산
    text_width = c.stringWidth(text, font_name, font_size)

    # 섹션 2: 앞면 (정방향) - 아래에서 2번째 섹션
    section2_center_y = SECTION_HEIGHT * 1.5
    c.drawString((WIDTH - text_width) / 2, section2_center_y - font_size / 3, text)

    # 섹션 3: 뒷면 (뒤집힘) - 아래에서 3번째 섹션
    section3_center_y = SECTION_HEIGHT * 2.5
    c.saveState()
    c.translate(WIDTH / 2, section3_center_y)
    c.rotate(180)
    c.drawString(-text_width / 2, -font_size / 3, text)
    c.restoreState()

    # 접는 방법 안내 (맨 위 섹션에 작게)
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(15 * mm, HEIGHT - 15 * mm, "↓ Fold along the dotted lines to create a table tent")

    c.save()
    print(f"PDF 생성 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    create_pdf()
