"""
A4 Document Image Generator for Korean OCR Training Data.

Generates full A4-page (2480x3508 @ 300DPI) document images
with multi-line Korean text, paired with ground truth text files.
"""

import os
import random as rnd

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageColor

from trdg import background_generator, distorsion_generator
from trdg.utils import load_fonts, get_text_width, get_text_height, make_filename_valid


# A4 at 300 DPI
A4_WIDTH = 2480
A4_HEIGHT = 3508


def _wrap_text_to_lines(text, font, max_width):
    """
    Wrap text to fit within max_width pixels.
    Korean can break at any character boundary.
    Respects existing newlines in the text.
    Returns list of line strings.
    """
    lines = []
    paragraphs = text.split("\n")

    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue

        words = paragraph.split(" ")
        current_line = ""

        for word in words:
            if not word:
                continue

            test_line = current_line + (" " if current_line else "") + word
            test_width = get_text_width(font, test_line)

            if test_width <= max_width:
                current_line = test_line
            else:
                # If current_line has content, save it
                if current_line:
                    lines.append(current_line)
                    current_line = ""

                # Check if the single word fits
                word_width = get_text_width(font, word)
                if word_width <= max_width:
                    current_line = word
                else:
                    # Break word at character level (Korean-style)
                    for char in word:
                        test_line = current_line + char
                        if get_text_width(font, test_line) <= max_width:
                            current_line = test_line
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = char

        if current_line:
            lines.append(current_line)

    return lines


def _render_document_text(
    text,
    font_path,
    font_size,
    text_color,
    page_width,
    page_height,
    margin_top,
    margin_bottom,
    margin_left,
    margin_right,
    line_spacing,
    paragraph_spacing,
    alignment,
    stroke_width=0,
    stroke_fill="#282828",
):
    """
    Render multi-line text onto a transparent RGBA canvas.
    Returns (text_image, rendered_ground_truth).
    """
    image_font = ImageFont.truetype(font=font_path, size=font_size)

    content_width = page_width - margin_left - margin_right
    content_height = page_height - margin_top - margin_bottom

    # Wrap text to lines
    all_lines = _wrap_text_to_lines(text, image_font, content_width)

    # Calculate line height
    sample_height = get_text_height(image_font, "가나다라마바사")
    line_height = int(sample_height * line_spacing)

    # Create canvas
    txt_img = Image.new("RGBA", (page_width, page_height), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)

    # Parse text color
    colors = [ImageColor.getrgb(c) for c in text_color.split(",")]
    c1, c2 = colors[0], colors[-1]
    fill = (
        rnd.randint(min(c1[0], c2[0]), max(c1[0], c2[0])),
        rnd.randint(min(c1[1], c2[1]), max(c1[1], c2[1])),
        rnd.randint(min(c1[2], c2[2]), max(c1[2], c2[2])),
    )

    # Parse stroke color
    stroke_colors = [ImageColor.getrgb(c) for c in stroke_fill.split(",")]
    sc1, sc2 = stroke_colors[0], stroke_colors[-1]
    s_fill = (
        rnd.randint(min(sc1[0], sc2[0]), max(sc1[0], sc2[0])),
        rnd.randint(min(sc1[1], sc2[1]), max(sc1[1], sc2[1])),
        rnd.randint(min(sc1[2], sc2[2]), max(sc1[2], sc2[2])),
    )

    # Render lines
    y = margin_top
    rendered_lines = []
    prev_was_empty = False

    for line in all_lines:
        # Check if we've exceeded the page
        if y + sample_height > page_height - margin_bottom:
            break

        if not line.strip():
            # Empty line = paragraph break
            y += int(paragraph_spacing)
            prev_was_empty = True
            rendered_lines.append("")
            continue

        # Calculate x based on alignment
        line_width = get_text_width(image_font, line)
        if alignment == 0:  # left
            x = margin_left
        elif alignment == 1:  # center
            x = margin_left + (content_width - line_width) // 2
        elif alignment == 2:  # right
            x = margin_left + content_width - line_width
        else:
            x = margin_left

        txt_draw.text(
            (x, y),
            line,
            fill=fill,
            font=image_font,
            stroke_width=stroke_width,
            stroke_fill=s_fill,
        )

        rendered_lines.append(line)
        y += line_height
        prev_was_empty = False

    # Build ground truth from rendered lines
    ground_truth = "\n".join(rendered_lines)

    return txt_img, ground_truth


class DocumentGenerator:
    """Generates A4 document page images with multi-line text."""

    @classmethod
    def generate_from_tuple(cls, t):
        """Same as generate, but takes all parameters as one tuple."""
        cls.generate(*t)

    @classmethod
    def generate(
        cls,
        index,
        text,
        font,
        out_dir,
        extension="png",
        page_width=A4_WIDTH,
        page_height=A4_HEIGHT,
        margins=(200, 200, 200, 200),
        font_size=42,
        line_spacing=1.8,
        paragraph_spacing=60,
        alignment=0,
        text_color="#282828",
        stroke_width=0,
        stroke_fill="#282828",
        background_type=0,
        image_dir="",
        blur=0,
        random_blur=False,
        skewing_angle=0,
        random_skew=False,
        distorsion_type=0,
        distorsion_orientation=0,
        image_mode="RGB",
        name_format=2,
    ):
        """
        Generate a single A4 document page image.

        Pipeline:
        1. Render multi-line text onto transparent canvas
        2. Generate background
        3. Composite text onto background
        4. Apply skew, distortion, blur
        5. Save image + ground truth
        """
        margin_top, margin_left, margin_bottom, margin_right = margins

        # 1. Render text
        text_img, ground_truth = _render_document_text(
            text=text,
            font_path=font,
            font_size=font_size,
            text_color=text_color,
            page_width=page_width,
            page_height=page_height,
            margin_top=margin_top,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right,
            line_spacing=line_spacing,
            paragraph_spacing=paragraph_spacing,
            alignment=alignment,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )

        # 2. Generate background
        if background_type == 0:
            bg_img = background_generator.gaussian_noise(page_height, page_width)
        elif background_type == 1:
            bg_img = background_generator.plain_white(page_height, page_width)
        elif background_type == 2:
            bg_img = background_generator.quasicrystal(page_height, page_width)
        else:
            bg_img = background_generator.image(page_height, page_width, image_dir)

        # 3. Composite text onto background
        bg_img.paste(text_img, (0, 0), text_img)

        # 4. Apply skew
        if skewing_angle > 0:
            angle = rnd.randint(-skewing_angle, skewing_angle) if random_skew else skewing_angle
            if angle != 0:
                bg_img = bg_img.rotate(angle, expand=False, fillcolor=(255, 255, 255))

        # 5. Apply distortion (simplified for full page)
        if distorsion_type != 0:
            mask_img = Image.new("RGB", (page_width, page_height), (0, 0, 0))
            if distorsion_type == 1:
                bg_img, _ = distorsion_generator.sin(
                    bg_img.convert("RGBA"), mask_img,
                    vertical=(distorsion_orientation == 0 or distorsion_orientation == 2),
                    horizontal=(distorsion_orientation == 1 or distorsion_orientation == 2),
                )
            elif distorsion_type == 2:
                bg_img, _ = distorsion_generator.cos(
                    bg_img.convert("RGBA"), mask_img,
                    vertical=(distorsion_orientation == 0 or distorsion_orientation == 2),
                    horizontal=(distorsion_orientation == 1 or distorsion_orientation == 2),
                )
            else:
                bg_img, _ = distorsion_generator.random(
                    bg_img.convert("RGBA"), mask_img,
                    vertical=(distorsion_orientation == 0 or distorsion_orientation == 2),
                    horizontal=(distorsion_orientation == 1 or distorsion_orientation == 2),
                )
            # Crop back to page size after distortion may expand
            bg_img = bg_img.crop((0, 0, page_width, page_height))

        # 6. Convert image mode
        final_image = bg_img.convert(image_mode)

        # 7. Apply blur
        if blur > 0:
            radius = rnd.random() * blur if random_blur else blur
            final_image = final_image.filter(ImageFilter.GaussianBlur(radius=radius))

        # 8. Save
        if name_format == 0:
            name = "{:06d}".format(index)
        elif name_format == 1:
            preview = text[:30].replace("\n", " ")
            name = "{:06d}_{}".format(index, make_filename_valid(preview, allow_unicode=True))
        else:
            name = "{:06d}".format(index)

        image_name = "{}.{}".format(name, extension)
        gt_name = "{}.gt.txt".format(name)

        if out_dir is not None:
            final_image.save(os.path.join(out_dir, image_name))
            with open(os.path.join(out_dir, gt_name), "w", encoding="utf-8") as f:
                f.write(ground_truth)
        else:
            return final_image, ground_truth
