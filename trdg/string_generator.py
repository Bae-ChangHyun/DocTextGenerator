import random as rnd
import string
from typing import List, Tuple

import wikipedia


def create_strings_from_file(filename: str, count: int) -> List[str]:
    """
    Create all strings by reading lines in specified files
    """

    strings = []

    with open(filename, "r", encoding="utf8") as f:
        lines = [l[0:200] for l in f.read().splitlines() if len(l) > 0]
        if len(lines) == 0:
            raise Exception("No lines could be read in file")
        while len(strings) < count:
            if len(lines) >= count - len(strings):
                strings.extend(lines[0 : count - len(strings)])
            else:
                strings.extend(lines)

    return strings


def create_strings_from_dict(
    length: int, allow_variable: bool, count: int, lang_dict: List[str]
) -> List[str]:
    """
    Create all strings by picking X random word in the dictionary
    """

    dict_len = len(lang_dict)
    strings = []
    for _ in range(0, count):
        current_string = ""
        for _ in range(0, rnd.randint(1, length) if allow_variable else length):
            current_string += lang_dict[rnd.randrange(dict_len)]
            current_string += " "
        strings.append(current_string[:-1])
    return strings


def get_random_page_content() -> str:
    page_title = wikipedia.random(1)
    try:
        page_content = wikipedia.page(page_title).summary
    except (wikipedia.DisambiguationError, wikipedia.PageError):
        return get_random_page_content()
    return page_content


def create_strings_from_wikipedia(
    minimum_length: int, count: int, lang: str
) -> List[str]:
    """
    Create all string by randomly picking Wikipedia articles and taking sentences from them.
    """
    wikipedia.set_lang(lang)
    sentences = []

    while len(sentences) < count:
        page_content = get_random_page_content()
        processed_content = page_content.replace("\n", " ").split(". ")
        sentence_candidates = [
            s.strip() for s in processed_content if len(s.split()) > minimum_length
        ]
        sentences.extend(sentence_candidates)

    return sentences[0:count]


def create_strings_randomly(
    length: int,
    allow_variable: bool,
    count: int,
    let: bool,
    num: bool,
    sym: bool,
    lang: str,
) -> List[str]:
    """
    Create all strings by randomly sampling from a pool of characters.
    """

    # If none specified, use all three
    if True not in (let, num, sym):
        let, num, sym = True, True, True

    pool = ""
    if let:
        if lang == "cn":
            pool += "".join(
                [chr(i) for i in range(19968, 40908)]
            )  # Unicode range of CHK characters
        elif lang == "ja":
            pool += "".join(
                [chr(i) for i in range(12288, 12351)]
            )  # unicode range for japanese-style punctuation
            pool += "".join(
                [chr(i) for i in range(12352, 12447)]
            )  # unicode range for Hiragana
            pool += "".join(
                [chr(i) for i in range(12448, 12543)]
            )  # unicode range for Katakana
            pool += "".join(
                [chr(i) for i in range(65280, 65519)]
            )  # unicode range for Full-width roman characters and half-width katakana
            pool += "".join(
                [chr(i) for i in range(19968, 40908)]
            )  # unicode range for common and uncommon kanji
            # https://stackoverflow.com/questions/19899554/unicode-range-for-japanese
        else:
            pool += string.ascii_letters
    if num:
        pool += "0123456789"
    if sym:
        pool += "!\"#$%&'()*+,-./:;?@[\\]^_`{|}~"

    if lang == "cn":
        min_seq_len = 1
        max_seq_len = 2
    elif lang == "ja":
        min_seq_len = 1
        max_seq_len = 2
    else:
        min_seq_len = 2
        max_seq_len = 10

    strings = []
    for _ in range(0, count):
        current_string = ""
        for _ in range(0, rnd.randint(1, length) if allow_variable else length):
            seq_len = rnd.randint(min_seq_len, max_seq_len)
            current_string += "".join([rnd.choice(pool) for _ in range(seq_len)])
            current_string += " "
        strings.append(current_string[:-1])
    return strings


# ============================================================
# Document-level text generators (for A4 page generation)
# ============================================================

def create_document_from_dict(
    lang_dict: List[str],
    num_paragraphs: int = 5,
    lines_per_paragraph: Tuple[int, int] = (3, 8),
    words_per_line: Tuple[int, int] = (5, 15),
) -> str:
    """
    Create a multi-paragraph document text by sampling words from a dictionary.
    Returns text with paragraph breaks (double newlines).
    """
    dict_len = len(lang_dict)
    paragraphs = []

    for _ in range(num_paragraphs):
        num_lines = rnd.randint(lines_per_paragraph[0], lines_per_paragraph[1])
        lines = []
        for _ in range(num_lines):
            num_words = rnd.randint(words_per_line[0], words_per_line[1])
            line_words = [lang_dict[rnd.randrange(dict_len)] for _ in range(num_words)]
            lines.append(" ".join(line_words))
        paragraphs.append(" ".join(lines))

    return "\n\n".join(paragraphs)


def create_document_from_file(filename: str, max_chars: int = 5000) -> str:
    """
    Read text from a file for document-level rendering.
    Preserves paragraph structure (double newlines).
    """
    with open(filename, "r", encoding="utf8") as f:
        content = f.read()

    if max_chars and len(content) > max_chars:
        # Truncate at paragraph boundary
        truncated = content[:max_chars]
        last_para = truncated.rfind("\n\n")
        if last_para > 0:
            content = truncated[:last_para]
        else:
            last_newline = truncated.rfind("\n")
            content = truncated[:last_newline] if last_newline > 0 else truncated

    return content.strip()


def create_document_from_wikipedia(lang: str = "ko", min_length: int = 200) -> str:
    """
    Fetch a random Wikipedia article and return multi-paragraph text.
    """
    wikipedia.set_lang(lang)

    for _ in range(10):  # retry up to 10 times
        try:
            page_title = wikipedia.random(1)
            page = wikipedia.page(page_title)
            content = page.content

            # Clean up Wikipedia formatting
            lines = []
            for line in content.split("\n"):
                line = line.strip()
                # Skip section headers (== Header ==)
                if line.startswith("=="):
                    continue
                if line:
                    lines.append(line)

            text = "\n\n".join(lines)
            if len(text) >= min_length:
                return text

        except (wikipedia.DisambiguationError, wikipedia.PageError):
            continue

    # Fallback: return whatever we have
    return text if text else "위키피디아에서 텍스트를 가져오지 못했습니다."


def create_document_randomly(
    num_chars: int = 3000,
    lang: str = "ko",
) -> str:
    """
    Generate random Korean text for document rendering.
    Creates realistic-looking paragraphs with random Hangul syllables.
    """
    # Hangul syllables range: 가(0xAC00) - 힣(0xD7A3)
    HANGUL_START = 0xAC00
    HANGUL_END = 0xD7A3

    pool = [chr(i) for i in range(HANGUL_START, HANGUL_END + 1)]
    numbers = "0123456789"
    punctuation = ".,!?"

    paragraphs = []
    chars_generated = 0

    while chars_generated < num_chars:
        # Generate a paragraph
        num_sentences = rnd.randint(3, 8)
        sentences = []

        for _ in range(num_sentences):
            if chars_generated >= num_chars:
                break
            # Generate a sentence
            num_words = rnd.randint(3, 12)
            words = []
            for _ in range(num_words):
                word_len = rnd.randint(1, 5)
                word = "".join(rnd.choice(pool) for _ in range(word_len))
                # Occasionally add a number
                if rnd.random() < 0.05:
                    word += rnd.choice(numbers)
                words.append(word)

            sentence = " ".join(words)
            # Add punctuation at end
            sentence += rnd.choice(punctuation)
            sentences.append(sentence)
            chars_generated += len(sentence)

        paragraph = " ".join(sentences)
        paragraphs.append(paragraph)

    return "\n\n".join(paragraphs)
