# TextRecognitionDataGenerator [![CircleCI](https://circleci.com/gh/Belval/TextRecognitionDataGenerator/tree/master.svg?style=svg)](https://circleci.com/gh/Belval/TextRecognitionDataGenerator/tree/master) [![PyPI version](https://badge.fury.io/py/trdg.svg)](https://badge.fury.io/py/trdg) [![codecov](https://codecov.io/gh/Belval/TextRecognitionDataGenerator/branch/master/graph/badge.svg)](https://codecov.io/gh/Belval/TextRecognitionDataGenerator)

OCR 학습용 합성 텍스트 데이터 생성기 — **한 줄 텍스트 이미지**와 **A4 문서 페이지 이미지** 모두 지원합니다.

[English](README.md) | **한국어**

---

## 목차

- [설치](#설치)
- [텍스트 모드](#텍스트-모드) — 한 줄 텍스트 이미지
- [문서 모드](#문서-모드) — A4 문서 페이지 이미지
- [공통 옵션](#공통-옵션) — 언어, 배경, 효과 (두 모드 공용)
- [폰트](#폰트)
- [벤치마크](#벤치마크)
- [기여하기](#기여하기)

---

## 설치

```bash
pip install trdg
```

또는 소스에서 직접 설치:

```bash
git clone https://github.com/Bae-ChangHyun/DocTextGenerator.git
cd DocTextGenerator
pip install -r requirements.txt
```

<details>
<summary>Docker</summary>

```bash
docker pull belval/trdg:latest
docker run -v /output/path/:/app/out/ -t belval/trdg:latest trdg [args]
```

경로(`/output/path/`)는 절대 경로여야 합니다.

</details>

---

## 텍스트 모드

OCR 학습을 위한 **한 줄 텍스트 이미지**를 생성합니다. 자세한 튜토리얼은 [공식 문서](https://textrecognitiondatagenerator.readthedocs.io/en/latest/index.html)를 참고하세요.

### 빠른 시작

```bash
trdg -c 1000 -w 5 -f 64
```

![1](samples/1.jpg "1") ![2](samples/2.jpg "2") ![3](samples/3.jpg "3") ![4](samples/4.jpg "4") ![5](samples/5.jpg "5")

결과물은 기본적으로 `out/` 디렉토리에 저장됩니다.

<details>
<summary>Python 모듈</summary>

```python
from trdg.generators import (
    GeneratorFromDict,
    GeneratorFromRandom,
    GeneratorFromStrings,
    GeneratorFromWikipedia,
)

generator = GeneratorFromStrings(
    ['Test1', 'Test2', 'Test3'],
    blur=2,
    random_blur=True
)

for img, lbl in generator:
    # Pillow 이미지 활용
    pass
```

전체 클래스 정의:
[`GeneratorFromDict`](trdg/generators/from_dict.py) | [`GeneratorFromRandom`](trdg/generators/from_random.py) | [`GeneratorFromStrings`](trdg/generators/from_strings.py) | [`GeneratorFromWikipedia`](trdg/generators/from_wikipedia.py)

</details>

<details>
<summary>손글씨 텍스트 (실험적)</summary>

```bash
trdg -c 1000 -w 5 -hw
```

![18](samples/18.jpg "0") ![19](samples/19.jpg "1") ![20](samples/20.jpg "2") ![21](samples/21.jpg "3") ![22](samples/22.jpg "4")

[handwriting-generation](https://github.com/Grzego/handwriting-generation)으로 학습된 TensorFlow 모델을 사용합니다. **이 기능을 사용하지 않는 한 TensorFlow는 필요하지 않습니다.**

</details>

<details>
<summary>텍스트 모드 전용 옵션</summary>

| 플래그 | 설명 | 기본값 |
|--------|------|--------|
| `-w` | 이미지당 단어 수 | 1 |
| `-f` | 폰트 높이 (픽셀) | 32 |
| `-hw` | 손글씨 모드 | False |
| `-or` | 텍스트 방향 (0=가로, 1=세로) | 0 |
| `--fit` | 텍스트 크기에 맞춰 이미지 자르기 | False |
| `--margins` | 이미지 여백 (픽셀) | 5,5,5,5 |
| `--output_mask` | 글자별 마스크 출력 | False |
| `--character_spacing` | 글자 간격 (픽셀) | 0 |
| `--word_split` | 글자 단위 대신 단어 단위로 분리 | False |

전체 옵션: `trdg -h`

</details>

---

## 문서 모드

**A4 크기 문서 페이지 이미지** (2480x3508 픽셀, 300 DPI)를 여러 줄 텍스트로 생성합니다. 각 이미지에는 `.gt.txt` 정답 텍스트 파일이 함께 생성되어, 문서 수준 OCR 학습에 적합합니다.

### 빠른 시작

```bash
trdg --document -c 10 -l ko

# 단일 텍스트 파일에서 생성
trdg --document -i /path/to/text.txt

# 텍스트 파일 폴더에서 생성 (파일당 1페이지)
trdg --document -i /path/to/folder/
```

### 샘플

| 한국어 (흰 배경) | 한국어 (노이즈) | 한국어 (노이즈 + 블러 + 기울기) |
|:---:|:---:|:---:|
| ![ko_white](samples/doc/ko_white.jpg) | ![ko_noise](samples/doc/ko_noise.jpg) | ![ko_effects](samples/doc/ko_effects.jpg) |

| 영어 | 중국어 | 일본어 |
|:---:|:---:|:---:|
| ![en](samples/doc/en_white.jpg) | ![cn](samples/doc/cn_white.jpg) | ![ja](samples/doc/ja_white.jpg) |

### 출력 형식

```
out/
├── 000000.png        # A4 문서 이미지
├── 000000.gt.txt     # 정답 텍스트 (UTF-8)
├── 000001.png
├── 000001.gt.txt
├── ...
└── labels.txt        # 이미지-정답 매핑
```

<details>
<summary>텍스트 소스</summary>

| 소스 | 명령어 |
|------|--------|
| 사전 (기본) | `trdg --document -c 10 -l ko` |
| 위키피디아 문서 | `trdg --document -c 10 -l ko -wk` |
| 단일 텍스트 파일 | `trdg --document -i my_text.txt` |
| 텍스트 파일 폴더 | `trdg --document -i /path/to/folder/` |
| 랜덤 문자열 | `trdg --document -c 10 -l ko -rs` |
| 사용자 지정 사전 | `trdg --document -c 10 -dt my_dict.txt` |

`-i` 사용 시 `-c`를 생략하면 입력 텍스트 파일당 1페이지가 생성됩니다.

</details>

<details>
<summary>멀티 변형 생성 (-i + -c)</summary>

`-i` (입력 텍스트)와 `-c` (개수)를 조합하면, 동일한 텍스트에서 **다양한 시각적 변형을 랜덤으로 생성**합니다. 사용자가 명시한 옵션은 고정되고, 나머지는 페이지마다 랜덤화됩니다.

```bash
# 1개 텍스트 파일 x 20개 랜덤 변형 = 20페이지
trdg --document -i novel.txt -c 20

# 배경만 흰색으로 고정, 나머지 전부 랜덤
trdg --document -i novel.txt -c 20 -b 1

# 폰트 크기와 배경 고정, 나머지 랜덤
trdg --document -i novel.txt -c 20 -b 1 --font_size 42

# 폴더: 3개 파일 x 10개 변형 = 30페이지
trdg --document -i texts/ -c 10
```

**랜덤화 파라미터** (명시하지 않은 경우):

| 파라미터 | 랜덤 범위 |
|----------|-----------|
| `--font_size` | 28~64 px |
| `--line_spacing` | 1.4~2.8 |
| `--paragraph_spacing` | 30~100 px |
| `-al` (정렬) | 0=좌측 (70%), 1=중앙 (20%), 2=우측 (10%) |
| `-tc` (텍스트 색상) | #282828, #000000, #333333, #1a1a1a, #444444 |
| `-sw` (외곽선 두께) | 0 (80%), 1 (20%) |
| `-b` (배경) | 0=노이즈 (40%), 1=흰색 (40%), 2=준결정 (20%) |
| `-bl` (블러) | 0~3, random_blur=True |
| `-k` (기울기) | 0~5도, random_skew=True |
| `-d` (왜곡) | 0=없음 (60%), 1=사인 (20%), 2=코사인 (10%), 3=랜덤 (10%) |
| `-m` (여백) | 150~350 px (균일) |
| `--font_size_variation` | 0 (50%), 3/5/8 px (50%) |

</details>

<details>
<summary>페이지 레이아웃 옵션</summary>

```bash
# 폰트 크기 (42px = 300DPI에서 약 10pt)
trdg --document -c 10 -l ko --font_size 50

# 페이지별 랜덤 폰트 크기
trdg --document -c 10 -l ko --font_size_min 36 --font_size_max 52

# 글자별 폰트 크기 변형 (+-픽셀, 손글씨/노이즈 효과)
trdg --document -c 10 -l ko --font_size 42 --font_size_variation 8

# 여백 (위,왼쪽,아래,오른쪽 픽셀)
trdg --document -c 10 -l ko -m 300,200,300,200

# 줄 간격 / 문단 간격
trdg --document -c 10 -l ko --line_spacing 2.0 --paragraph_spacing 80

# 정렬 (0=좌측, 1=중앙, 2=우측)
trdg --document -c 10 -l ko -al 1

# 페이지 크기 지정
trdg --document -c 10 -l ko --page_width 2480 --page_height 3508
```

</details>

<details>
<summary>문서 모드 전용 옵션</summary>

| 플래그 | 설명 | 기본값 |
|--------|------|--------|
| `-i` | 입력 텍스트 파일 또는 디렉토리 경로 | - |
| `-wk` | 위키피디아를 텍스트 소스로 사용 | False |
| `-rs` | 랜덤 문자열 생성 | False |
| `-dt` | 사용자 지정 사전 파일 경로 | - |
| `-na` | 파일명 형식: 0=ID, 1=ID_미리보기 | 0 |
| `--page_width` | 페이지 너비 (픽셀) | 2480 |
| `--page_height` | 페이지 높이 (픽셀) | 3508 |
| `-m` | 여백: 위,왼쪽,아래,오른쪽 (px) | 200,200,200,200 |
| `--font_size` | 폰트 크기 (픽셀) | 42 |
| `--font_size_min` | 최소 폰트 크기 (랜덤 범위) | - |
| `--font_size_max` | 최대 폰트 크기 (랜덤 범위) | - |
| `--font_size_variation` | 글자별 폰트 크기 변형 +-px | 0 |
| `--line_spacing` | 줄 간격 배율 | 1.8 |
| `--paragraph_spacing` | 문단 사이 추가 픽셀 | 60 |
| `-al` | 정렬 (0=좌측, 1=중앙, 2=우측) | 0 |
| `--num_paragraphs` | 페이지당 문단 수 | 5 |
| `--lines_per_paragraph` | 문단당 줄 수 (최소,최대) | 3,8 |
| `--words_per_line` | 줄당 단어 수 (최소,최대) | 5,15 |

전체 옵션: `trdg --document -h`

</details>

---

## 공통 옵션

아래 옵션은 텍스트 모드와 문서 모드 모두에서 사용할 수 있습니다.

### 지원 언어

```bash
# 텍스트 모드                          # 문서 모드
trdg -c 100 -l en                    trdg --document -c 10 -l en      # 영어
trdg -c 100 -l ko                    trdg --document -c 10 -l ko      # 한국어
trdg -c 100 -l cn                    trdg --document -c 10 -l cn      # 중국어
trdg -c 100 -l ja                    trdg --document -c 10 -l ja      # 일본어
trdg -c 100 -l fr                    trdg --document -c 10 -l fr      # 프랑스어
trdg -c 100 -l de                    trdg --document -c 10 -l de      # 독일어
trdg -c 100 -l es                    trdg --document -c 10 -l es      # 스페인어
trdg -c 100 -l ar                    trdg --document -c 10 -l ar      # 아랍어
trdg -c 100 -l hi                    trdg --document -c 10 -l hi      # 힌디어
trdg -c 100 -l th                    trdg --document -c 10 -l th      # 태국어
```

### 배경

`-b` 옵션으로 배경 유형을 선택합니다.

| 값 | 유형 | 예시 |
|:---:|:-----|:-----|
| 0 | 가우시안 노이즈 (기본) | ![15](samples/15.jpg "noise") |
| 1 | 흰색 | ![16](samples/16.jpg "white") |
| 2 | 준결정(Quasicrystal) | ![17](samples/17.jpg "quasicrystal") |
| 3 | 이미지 (`images/` 폴더에서) | ![23](samples/23.jpg "image") |

```bash
# 텍스트 모드
trdg -c 100 -b 1

# 문서 모드
trdg --document -c 10 -l ko -b 1
```

### 효과

<details>
<summary>기울기(Skewing)</summary>

`-k` (각도)와 `-rk` (랜덤) 옵션 사용:

```bash
# 텍스트 모드
trdg -c 100 -k 5 -rk

# 문서 모드
trdg --document -c 10 -l ko -k 3 -rk
```

![6](samples/6.jpg) ![7](samples/7.jpg) ![8](samples/8.jpg)

</details>

<details>
<summary>왜곡(Distortion)</summary>

`-d` (유형: 1=사인, 2=코사인, 3=랜덤)와 `-do` (방향: 0=수직, 1=수평, 2=양방향) 옵션 사용:

```bash
# 텍스트 모드
trdg -c 100 -d 1

# 문서 모드
trdg --document -c 10 -l ko -d 1
```

![23](samples/24.jpg) ![24](samples/25.jpg) ![25](samples/26.jpg)

</details>

<details>
<summary>가우시안 블러</summary>

`-bl` (반지름)과 `-rbl` (랜덤) 옵션 사용:

```bash
# 텍스트 모드
trdg -c 100 -bl 2 -rbl

# 문서 모드
trdg --document -c 10 -l ko -bl 2 -rbl
```

![11](samples/11.jpg) ![12](samples/12.jpg) ![13](samples/13.jpg) ![14](samples/14.jpg)

</details>

<details>
<summary>효과 조합</summary>

```bash
# 텍스트 모드: 노이즈 배경 + 블러 + 기울기 + 왜곡
trdg -c 100 -b 0 -bl 1 -rbl -k 5 -rk -d 1

# 문서 모드: 노이즈 배경 + 블러 + 기울기 + 왜곡
trdg --document -c 10 -l ko -b 0 -bl 1 -rbl -k 2 -rk -d 1
```

</details>

### 공용 플래그 참조

| 플래그 | 설명 | 기본값 |
|--------|------|--------|
| `-c` | 생성할 이미지/페이지 수 | - |
| `-l` | 언어 코드 | en / ko |
| `-e` | 출력 형식 (png, jpg, tiff) | jpg / png |
| `-b` | 배경 (0=노이즈, 1=흰색, 2=준결정, 3=이미지) | 0 |
| `-id` | 배경 이미지 디렉토리 (`-b 3` 사용 시) | images/ |
| `-k` | 기울기 각도 (도) | 0 |
| `-rk` | 랜덤 기울기 | False |
| `-bl` | 가우시안 블러 반지름 | 0 |
| `-rbl` | 랜덤 블러 | False |
| `-d` | 왜곡 (0=없음, 1=사인, 2=코사인, 3=랜덤) | 0 |
| `-do` | 왜곡 방향 (0=수직, 1=수평, 2=양방향) | 0 |
| `-tc` | 텍스트 색상 (hex 또는 범위 `'#000,#FFF'`) | #282828 |
| `-sw` | 외곽선 두께 | 0 |
| `-sf` | 외곽선 색상 | #282828 |
| `-ft` | 특정 폰트 파일 경로 | - |
| `-fd` | 폰트 디렉토리 | - |
| `-im` | 이미지 모드 (RGB 또는 L=그레이스케일) | RGB |
| `-t` | 워커 프로세스 수 | 1 |
| `--output_dir` | 출력 디렉토리 | out/ |
| `--seed` | 재현성을 위한 랜덤 시드 | - |

---

## 폰트

스크립트는 `fonts/` 디렉토리에서 랜덤으로 폰트를 선택합니다.

| 디렉토리 | 언어 |
|:---------|:-----|
| fonts/latin | 영어, 프랑스어, 스페인어, 독일어 |
| fonts/cn | 중국어 |
| fonts/ko | 한국어 |
| fonts/ja | 일본어 |
| fonts/th | 태국어 |

<details>
<summary>새 언어 추가하기</summary>

1. 새 폴더 생성: `fonts/<두 글자 코드>/`
2. `.ttf` 또는 `.otf` 폰트 파일 추가
3. `run.py`의 `load_fonts()`에 조건문 추가
4. 사전 파일 추가: `dicts/<두 글자 코드>.txt`
5. 실행: `trdg -l <코드>` 또는 `trdg --document -l <코드>`

</details>

---

## 벤치마크

<details>
<summary>텍스트 모드 — 초당 이미지 수</summary>

- Intel Core i7-4710HQ @ 2.50Ghz + SSD (`-c 1000 -w 1`)
    - `-t 1` : 363 img/s
    - `-t 2` : 694 img/s
    - `-t 4` : 1300 img/s
    - `-t 8` : 1500 img/s
- AMD Ryzen 7 1700 @ 4.0Ghz + SSD (`-c 1000 -w 1`)
    - `-t 1` : 558 img/s
    - `-t 2` : 1045 img/s
    - `-t 4` : 2107 img/s
    - `-t 8` : 3297 img/s

</details>

---

## 기여하기

1. 작업할 기능을 설명하는 이슈를 생성합니다
2. 해당 기능을 구현합니다
3. Pull Request를 생성합니다

누락되거나, 불명확하거나, 동작하지 않는 부분이 있다면 리포지토리에 이슈를 열어주세요.
