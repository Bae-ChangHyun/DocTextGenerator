"""
CLI for generating A4 document images with multi-line text.

Usage:
    # Standalone
    python -m trdg.run_doc -c 10 -l ko
    python -m trdg.run_doc -c 5 -i /path/to/file.txt
    python -m trdg.run_doc -i /path/to/folder/

    # Via trdg command
    trdg --document -c 10 -l ko
    trdg --document -i /path/to/folder/

    # Multi-variant generation (same text, random parameters)
    trdg --document -i novel.txt -c 20
    trdg --document -i novel.txt -c 20 -b 1   # fix background, randomize rest
    trdg --document -i texts/ -c 10            # 3 files × 10 = 30 pages
"""

import argparse
import errno
import glob
import os
import sys
import random as rnd

from multiprocessing import Pool
from tqdm import tqdm

from trdg.document_generator import DocumentGenerator, A4_WIDTH, A4_HEIGHT
from trdg.string_generator import (
    create_document_from_dict,
    create_document_from_file,
    create_document_from_wikipedia,
    create_document_randomly,
)
from trdg.utils import load_dict, load_fonts


def _detect_user_specified(parser):
    """Scan sys.argv to find which options the user explicitly provided."""
    specified = set()
    argv = sys.argv[1:]
    for action in parser._actions:
        if not action.option_strings:
            continue
        for opt in action.option_strings:
            if opt in argv:
                specified.add(action.dest)
                break
    return specified


_TEXT_COLORS = ['#282828', '#000000', '#333333', '#1a1a1a', '#444444']


def _build_page_params(args, user_specified, fonts, doc_margins):
    """
    Build a randomized parameter dict for one page.
    Parameters explicitly set by the user are kept fixed.
    """
    p = {}

    # font (always randomized per page)
    p['font'] = fonts[rnd.randrange(len(fonts))]

    # font_size
    if 'font_size' not in user_specified and 'font_size_min' not in user_specified:
        p['font_size'] = rnd.randint(28, 64)
    else:
        if args.font_size_min is not None and args.font_size_max is not None:
            p['font_size'] = rnd.randint(args.font_size_min, args.font_size_max)
        else:
            p['font_size'] = args.font_size

    # line_spacing
    if 'line_spacing' not in user_specified:
        p['line_spacing'] = round(rnd.uniform(1.4, 2.8), 2)
    else:
        p['line_spacing'] = args.line_spacing

    # paragraph_spacing
    if 'paragraph_spacing' not in user_specified:
        p['paragraph_spacing'] = rnd.randint(30, 100)
    else:
        p['paragraph_spacing'] = args.paragraph_spacing

    # alignment
    if 'alignment' not in user_specified:
        p['alignment'] = rnd.choices([0, 1, 2], weights=[70, 20, 10])[0]
    else:
        p['alignment'] = args.alignment

    # text_color
    if 'text_color' not in user_specified:
        p['text_color'] = rnd.choice(_TEXT_COLORS)
    else:
        p['text_color'] = args.text_color

    # stroke_width
    if 'stroke_width' not in user_specified:
        p['stroke_width'] = rnd.choices([0, 1], weights=[80, 20])[0]
    else:
        p['stroke_width'] = args.stroke_width

    # background
    if 'background' not in user_specified:
        p['background'] = rnd.choices([0, 1, 2], weights=[40, 40, 20])[0]
    else:
        p['background'] = args.background

    # blur
    if 'blur' not in user_specified:
        p['blur'] = rnd.randint(0, 3)
        p['random_blur'] = True
    else:
        p['blur'] = args.blur
        p['random_blur'] = args.random_blur

    # skew_angle
    if 'skew_angle' not in user_specified:
        p['skew_angle'] = rnd.randint(0, 5)
        p['random_skew'] = True
    else:
        p['skew_angle'] = args.skew_angle
        p['random_skew'] = args.random_skew

    # distorsion
    if 'distorsion' not in user_specified:
        p['distorsion'] = rnd.choices([0, 1, 2, 3], weights=[60, 20, 10, 10])[0]
    else:
        p['distorsion'] = args.distorsion

    # margins
    if 'margins' not in user_specified:
        m = rnd.randint(150, 350)
        p['margins'] = (m, m, m, m)
    else:
        p['margins'] = doc_margins

    # font_size_variation
    # If user explicitly fixed font_size, don't randomize variation either
    if 'font_size_variation' not in user_specified:
        if 'font_size' in user_specified:
            p['font_size_variation'] = 0
        else:
            p['font_size_variation'] = rnd.choices([0, 3, 5, 8], weights=[50, 20, 20, 10])[0]
    else:
        p['font_size_variation'] = args.font_size_variation

    return p


def margins(margin):
    parts = margin.split(",")
    if len(parts) == 1:
        return [int(parts[0])] * 4
    return [int(m) for m in parts]


def _collect_input_texts(input_path):
    """
    Collect texts from input path.
    - If path is a .txt file: read and return [text]
    - If path is a directory: read all .txt files, return [text, text, ...]
    Each file becomes one document page.
    """
    texts = []

    if os.path.isfile(input_path):
        text = create_document_from_file(input_path)
        texts.append(text)
    elif os.path.isdir(input_path):
        txt_files = sorted(glob.glob(os.path.join(input_path, "*.txt")))
        if not txt_files:
            sys.exit("No .txt files found in directory: {}".format(input_path))
        for f in txt_files:
            text = create_document_from_file(f)
            texts.append(text)
        print("Found {} text file(s) in {}".format(len(txt_files), input_path))
    else:
        sys.exit("Input path does not exist: {}".format(input_path))

    return texts


def _run_document_mode(args):
    """
    Run document generation from parsed args (called from run.py --document).
    """
    # Create output directory
    try:
        os.makedirs(args.output_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Load dictionary
    lang_dict = _load_dictionary(args)

    # Load fonts
    fonts = _load_font_list(args)
    if not fonts:
        sys.exit("No fonts found for language: {}".format(args.language))

    print("Found {} font(s)".format(len(fonts)))

    # Parse paragraph config
    lpp = [int(x) for x in args.lines_per_paragraph.split(",")]
    wpl = [int(x) for x in args.words_per_line.split(",")]

    # Collect texts
    texts = _collect_texts(args, lang_dict, lpp, wpl)

    # Detect user-specified options
    user_specified = getattr(args, '_user_specified', set())

    # Multi-variant mode: -i with -c > 0
    input_file = getattr(args, 'input_file', '') or ''
    multi_variant = bool(input_file) and args.count > 0

    if multi_variant:
        base_texts = texts
        texts = []
        for t in base_texts:
            texts.extend([t] * args.count)
        print("Multi-variant mode: {} text(s) x {} variants = {} pages".format(
            len(base_texts), args.count, len(texts)))

    count = len(texts)
    print("Generating {} document page(s)...".format(count))

    # Build generation tuples
    doc_margins = args.margins if isinstance(args.margins, (list, tuple)) else (200, 200, 200, 200)

    if multi_variant:
        # Per-page randomized parameters
        gen_args = []
        for i in range(count):
            p = _build_page_params(args, user_specified, fonts, doc_margins)
            gen_args.append((
                i,
                texts[i],
                p['font'],
                args.output_dir,
                args.extension,
                args.page_width,
                args.page_height,
                p['margins'],
                p['font_size'],
                p['line_spacing'],
                p['paragraph_spacing'],
                p['alignment'],
                p['text_color'],
                p['stroke_width'],
                args.stroke_fill,
                p['background'],
                args.image_dir,
                p['blur'],
                p['random_blur'],
                p['skew_angle'],
                p['random_skew'],
                p['distorsion'],
                args.distorsion_orientation,
                args.image_mode,
                getattr(args, 'name_format', 0),
                p['font_size_variation'],
            ))
    else:
        # Uniform parameters (existing behavior)
        font_sizes = []
        for _ in range(count):
            if args.font_size_min is not None and args.font_size_max is not None:
                font_sizes.append(rnd.randint(args.font_size_min, args.font_size_max))
            else:
                font_sizes.append(args.font_size)

        gen_args = list(zip(
            range(count),
            texts,
            [fonts[rnd.randrange(len(fonts))] for _ in range(count)],
            [args.output_dir] * count,
            [args.extension] * count,
            [args.page_width] * count,
            [args.page_height] * count,
            [doc_margins] * count,
            font_sizes,
            [args.line_spacing] * count,
            [args.paragraph_spacing] * count,
            [args.alignment] * count,
            [args.text_color] * count,
            [args.stroke_width] * count,
            [args.stroke_fill] * count,
            [args.background] * count,
            [args.image_dir] * count,
            [args.blur] * count,
            [args.random_blur] * count,
            [args.skew_angle] * count,
            [args.random_skew] * count,
            [args.distorsion] * count,
            [args.distorsion_orientation] * count,
            [args.image_mode] * count,
            [getattr(args, 'name_format', 0)] * count,
            [getattr(args, 'font_size_variation', 0)] * count,
        ))

    # Generate
    if args.thread_count > 1:
        p = Pool(args.thread_count)
        for _ in tqdm(
            p.imap_unordered(DocumentGenerator.generate_from_tuple, gen_args),
            total=count,
        ):
            pass
        p.terminate()
    else:
        for t in tqdm(gen_args, total=count):
            DocumentGenerator.generate_from_tuple(t)

    # Create labels file
    labels_path = os.path.join(args.output_dir, "labels.txt")
    with open(labels_path, "w", encoding="utf-8") as f:
        for i in range(count):
            img_name = "{:06d}.{}".format(i, args.extension)
            gt_name = "{:06d}.gt.txt".format(i)
            f.write("{} {}\n".format(img_name, gt_name))

    print("Done! Output saved to: {}".format(args.output_dir))


def _load_dictionary(args):
    """Load dictionary based on args."""
    dict_attr = getattr(args, 'dict', None)
    if dict_attr:
        if os.path.isfile(dict_attr):
            with open(dict_attr, "r", encoding="utf8", errors="ignore") as d:
                return [l for l in d.read().splitlines() if len(l) > 0]
        else:
            sys.exit("Cannot open dict: {}".format(dict_attr))
    else:
        dict_path = os.path.join(
            os.path.dirname(__file__), "dicts", args.language + ".txt"
        )
        if os.path.isfile(dict_path):
            with open(dict_path, "r", encoding="utf8", errors="ignore") as d:
                return [l for l in d.read().splitlines() if len(l) > 0]
    return None


def _load_font_list(args):
    """Load font list based on args."""
    font_dir = getattr(args, 'font_dir', None)
    font = getattr(args, 'font', None)

    if font_dir:
        return [
            os.path.join(font_dir, p)
            for p in os.listdir(font_dir)
            if os.path.splitext(p)[1].lower() in (".ttf", ".otf")
        ]
    elif font:
        if os.path.isfile(font):
            return [font]
        else:
            sys.exit("Cannot open font: {}".format(font))
    else:
        return load_fonts(args.language)


def _collect_texts(args, lang_dict, lpp, wpl):
    """Collect texts based on source type."""
    input_file = getattr(args, 'input_file', '') or ''

    # Input file/directory mode: count is determined by input
    if input_file:
        texts = _collect_input_texts(input_file)
        return texts

    # For other modes, use -c count
    count = args.count
    texts = []

    use_wiki = getattr(args, 'use_wikipedia', False)
    use_random = getattr(args, 'random_sequences', False)

    for _ in range(count):
        if use_wiki:
            text = create_document_from_wikipedia(lang=args.language)
        elif use_random:
            text = create_document_randomly(num_chars=3000, lang=args.language)
        elif lang_dict:
            text = create_document_from_dict(
                lang_dict,
                num_paragraphs=getattr(args, 'num_paragraphs', 5),
                lines_per_paragraph=(lpp[0], lpp[1] if len(lpp) > 1 else lpp[0]),
                words_per_line=(wpl[0], wpl[1] if len(wpl) > 1 else wpl[0]),
            )
        else:
            text = create_document_randomly(num_chars=3000, lang=args.language)
        texts.append(text)

    return texts


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate A4 document images with text for OCR training."
    )

    # Count
    parser.add_argument(
        "-c", "--count", type=int, default=0,
        help="Number of document pages to generate. "
             "With -i: number of random variants per input text. "
             "Without -i: total pages to generate from dictionary/wiki.",
    )

    # Text source
    parser.add_argument(
        "-l", "--language", type=str, default="ko",
        help="Language for dictionary and fonts (default: ko)",
    )
    parser.add_argument(
        "-i", "--input_file", type=str, default="",
        help="Path to a .txt file or a directory of .txt files. "
             "With -c N: generates N random variants per input text. "
             "Without -c: one page per input text.",
    )
    parser.add_argument(
        "-wk", "--use_wikipedia", action="store_true", default=False,
        help="Use Wikipedia articles as text source",
    )
    parser.add_argument(
        "-rs", "--random_sequences", action="store_true", default=False,
        help="Generate random character sequences",
    )
    parser.add_argument(
        "-dt", "--dict", type=str, default=None,
        help="Path to custom dictionary file",
    )

    # Output
    parser.add_argument(
        "--output_dir", type=str, default="out/",
        help="Output directory (default: out/)",
    )
    parser.add_argument(
        "-e", "--extension", type=str, default="png",
        choices=["png", "jpg", "tiff"],
        help="Output image format (default: png)",
    )
    parser.add_argument(
        "-na", "--name_format", type=int, default=0,
        help="Naming: 0=[ID] (default), 1=[ID]_[preview]",
    )

    # Page layout
    parser.add_argument(
        "--page_width", type=int, default=A4_WIDTH,
        help="Page width in pixels (default: 2480 for A4@300DPI)",
    )
    parser.add_argument(
        "--page_height", type=int, default=A4_HEIGHT,
        help="Page height in pixels (default: 3508 for A4@300DPI)",
    )
    parser.add_argument(
        "-m", "--margins", type=margins, default=(200, 200, 200, 200),
        help="Margins: top,left,bottom,right in pixels (default: 200,200,200,200)",
    )
    parser.add_argument(
        "--font_size", type=int, default=42,
        help="Font size in pixels (42px = 10pt@300DPI, default: 42)",
    )
    parser.add_argument(
        "--font_size_min", type=int, default=None,
        help="Min font size for random variation (optional)",
    )
    parser.add_argument(
        "--font_size_max", type=int, default=None,
        help="Max font size for random variation (optional)",
    )
    parser.add_argument(
        "--font_size_variation", type=int, default=0,
        help="Per-character font size variation range in ±pixels (default: 0). "
             "E.g., --font_size 42 --font_size_variation 5 → each char 37~47px",
    )
    parser.add_argument(
        "--line_spacing", type=float, default=1.8,
        help="Line spacing multiplier (default: 1.8)",
    )
    parser.add_argument(
        "--paragraph_spacing", type=int, default=60,
        help="Extra pixels between paragraphs (default: 60)",
    )
    parser.add_argument(
        "-al", "--alignment", type=int, default=0,
        choices=[0, 1, 2],
        help="Text alignment: 0=left (default), 1=center, 2=right",
    )

    # Font
    parser.add_argument(
        "-ft", "--font", type=str, default=None,
        help="Specific font file path",
    )
    parser.add_argument(
        "-fd", "--font_dir", type=str, default=None,
        help="Directory of font files to randomly select from",
    )

    # Text rendering
    parser.add_argument(
        "-tc", "--text_color", type=str, default="#282828",
        help="Text color (hex) or range '#000000,#444444' (default: #282828)",
    )
    parser.add_argument(
        "-sw", "--stroke_width", type=int, default=0,
        help="Text stroke width (default: 0)",
    )
    parser.add_argument(
        "-sf", "--stroke_fill", type=str, default="#282828",
        help="Stroke color (default: #282828)",
    )

    # Background
    parser.add_argument(
        "-b", "--background", type=int, default=0,
        choices=[0, 1, 2, 3],
        help="Background: 0=noise (default), 1=white, 2=quasicrystal, 3=image",
    )
    parser.add_argument(
        "-id", "--image_dir", type=str,
        default=os.path.join(os.path.split(os.path.realpath(__file__))[0], "images"),
        help="Directory of background images (for -b 3)",
    )

    # Effects
    parser.add_argument(
        "-bl", "--blur", type=int, default=0,
        help="Gaussian blur radius (default: 0)",
    )
    parser.add_argument(
        "-rbl", "--random_blur", action="store_true", default=False,
        help="Randomize blur from 0 to -bl value",
    )
    parser.add_argument(
        "-k", "--skew_angle", type=int, default=0,
        help="Page skew angle in degrees (default: 0)",
    )
    parser.add_argument(
        "-rk", "--random_skew", action="store_true", default=False,
        help="Randomize skew angle",
    )
    parser.add_argument(
        "-d", "--distorsion", type=int, default=0,
        choices=[0, 1, 2, 3],
        help="Distortion: 0=none (default), 1=sin, 2=cos, 3=random",
    )
    parser.add_argument(
        "-do", "--distorsion_orientation", type=int, default=0,
        choices=[0, 1, 2],
        help="Distortion axis: 0=vertical, 1=horizontal, 2=both",
    )

    # Image mode
    parser.add_argument(
        "-im", "--image_mode", type=str, default="RGB",
        choices=["RGB", "L"],
        help="Image mode: RGB (default) or L (grayscale)",
    )

    # Processing
    parser.add_argument(
        "-t", "--thread_count", type=int, default=1,
        help="Number of worker processes (default: 1)",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility",
    )

    # Document text generation params
    parser.add_argument(
        "--num_paragraphs", type=int, default=5,
        help="Number of paragraphs per page (default: 5)",
    )
    parser.add_argument(
        "--lines_per_paragraph", type=str, default="3,8",
        help="Lines per paragraph range: min,max (default: 3,8)",
    )
    parser.add_argument(
        "--words_per_line", type=str, default="5,15",
        help="Words per line range: min,max (default: 5,15)",
    )

    args = parser.parse_args()
    args._user_specified = _detect_user_specified(parser)
    return args


def main():
    args = parse_arguments()

    if args.seed is not None:
        rnd.seed(args.seed)

    # Validate: need either -c or -i
    if args.count <= 0 and not args.input_file:
        sys.exit("Error: must specify -c COUNT or -i INPUT_PATH")

    _run_document_mode(args)


if __name__ == "__main__":
    main()
