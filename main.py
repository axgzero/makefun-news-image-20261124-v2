#!/usr/bin/env python3
"""Sum up 24 November 2026's world news in one image.

Entrypoint for the make.fun news-image-20261124 bounty.

The program draws the entry image itself, deterministically, from the
stories encoded below in STORIES / ALSO: a newspaper front page for
Tuesday 24 November 2026 -- COP31 collapses in Antalya, Nvidia brings
back Jensen Huang as CEO, Russia warns Estonia of "open war" over its
border closure, the Democrats take their biggest House majority since
1992, India pledges $1.62 billion to Nepal, and Tajikistan starts
leaving the ICC -- with Puigdemont's return, Denmark's "ghetto law"
ruling, the Gaza strike that killed an UNRWA worker, and the CAS
ruling on Senegal's AFCON title in the footer. Every story was checked
against mainstream reporting in the 24 November 2026 morning editions
(mostly Reuters); see SOURCES.md.

Rendering is pure standard library: a small built-in 5x7 bitmap font,
a pixel canvas, simple drawn pictograms, and a hand-rolled PNG encoder
(zlib). No network, no third-party packages, no timestamps anywhere in
the output, so every run writes byte-identical output. Rebuilt in a
session started after the competition opened, in a fresh repository
created after the opening, after an earlier build done before the
opening could not be entered.

Usage:
    python3 main.py            draw entry.png into $MAKEFUN_OUTPUT_DIR
                               (default /output)
    python3 main.py --list     print the stories the image encodes
    python3 main.py --check    re-render and verify entry.png beside
                               this script matches, byte for byte
"""

from __future__ import annotations

import argparse
import binascii
import math
import os
import struct
import sys
import zlib

WIDTH = 1024
HEIGHT = 1024
MAX_BYTES = 1048576

PAPER = (246, 241, 230)   # newsprint off-white
INK = (20, 20, 26)        # near-black headline ink
BODY_INK = (52, 48, 42)   # softer ink for body copy
NAVY = (20, 49, 92)       # masthead blue
RED = (179, 35, 42)       # date red
RULE = (216, 207, 186)    # hairline rule
WHITE = (255, 255, 255)

# One panel per story, in reading order. `body` is wrapped by the
# renderer to at most three lines; `accent` colours the panel's top
# bar, number badge, tag and pictogram; `icon` picks the pictogram.
STORIES = [
    {
        "headline": "COP31 COLLAPSES",
        "tag": "CLIMATE",
        "body": (
            "UN climate talks in Antalya end with no deal, as the EU "
            "rejects the final text."
        ),
        "accent": (30, 122, 70),
        "icon": "globe",
    },
    {
        "headline": "HUANG BACK AT NVIDIA",
        "tag": "MARKETS",
        "body": (
            "Nvidia reinstates Jensen Huang as CEO; shares jump 33% "
            "and the Nasdaq gains 6%."
        ),
        "accent": (11, 95, 165),
        "icon": "chip",
    },
    {
        "headline": "MOSCOW WARNS OF OPEN WAR",
        "tag": "EUROPE",
        "body": (
            "Moscow says Estonia's plan to shut its border from "
            "1 Dec is 'on the verge of triggering open war'."
        ),
        "accent": (140, 47, 57),
        "icon": "warning",
    },
    {
        "headline": "DEMOCRATS' BIGGEST WIN",
        "tag": "POLITICS",
        "body": (
            "Democrats win at least 258 House seats after North "
            "Carolina, their largest majority since 1992."
        ),
        "accent": (43, 58, 103),
        "icon": "ballot",
    },
    {
        "headline": "NEPAL GETS $1.62BN AID",
        "tag": "ASIA",
        "body": (
            "Modi pledges $1.62 billion to help Nepal rebuild after "
            "August's floods; a new train link opens."
        ),
        "accent": (178, 106, 0),
        "icon": "mountains",
    },
    {
        "headline": "TAJIKISTAN QUITS THE ICC",
        "tag": "JUSTICE",
        "body": (
            "Tajikistan starts a one-year withdrawal from the war "
            "crimes court, the fourth country to begin one."
        ),
        "accent": (107, 63, 160),
        "icon": "court",
    },
]

# Short items for the footer strip, each kept to one line.
ALSO = [
    "Puigdemont: Spain's top court clears the ex-Catalan leader to come home.",
    "Denmark: top court backs 'ghetto law' evictions; 91 leases ended.",
    "Gaza: Israeli strike kills an UNRWA worker at a Jabalia water well.",
    "Today: CAS rules on Senegal's appeal over the AFCON title.",
]

DATE_LINE = "TUESDAY 24 NOVEMBER 2026"
MASTHEAD = "THE WORLD IN ONE DAY"

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 cells, '#' on, '.' off.
# Lowercase letters sit on rows 2-6 (x-height) with descenders for
# g, j, p, q, y. Only the characters the stories use are defined.
# ---------------------------------------------------------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".###.", "#...#", "#...#", ".###.", "....#", "###.."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", "##..."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", "####.", "#...#", "#...#", "####.", "#....", "#...."),
    "q": (".....", ".####", "#...#", "#...#", ".####", "...#.", "..##."),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ":": (".....", ".....", "..#..", ".....", ".....", "..#..", "....."),
    ";": (".....", ".....", "..#..", ".....", ".....", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "+": (".....", ".....", "..#..", ".###.", "..#..", ".....", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
}


def text_width(text: str, scale: int) -> int:
    """Pixel width of `text` at the given font scale."""
    return len(text) * 6 * scale - scale


def draw_text(canvas: "Canvas", x: int, y: int, text: str,
              scale: int, colour: tuple[int, int, int]) -> None:
    """Draw `text` with its top-left corner at (x, y)."""
    for ch in text:
        glyph = FONT[ch]  # KeyError here means an unencoded character
        for row, cells in enumerate(glyph):
            for col, cell in enumerate(cells):
                if cell == "#":
                    canvas.fill_rect(x + col * scale, y + row * scale,
                                     scale, scale, colour)
        x += 6 * scale


def wrap(text: str, scale: int, max_width: int) -> list[str]:
    """Greedy word wrap of `text` to lines of at most `max_width` px."""
    lines: list[str] = []
    current = ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class Canvas:
    """A plain RGB pixel buffer with rectangle and text drawing."""

    def __init__(self, width: int, height: int, bg: tuple[int, int, int]):
        self.width = width
        self.height = height
        self.buf = bytearray(bytes(bg) * (width * height))

    def fill_rect(self, x: int, y: int, w: int, h: int,
                  colour: tuple[int, int, int]) -> None:
        r, g, b = colour
        x0 = max(x, 0)
        y0 = max(y, 0)
        x1 = min(x + w, self.width)
        y1 = min(y + h, self.height)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes((r, g, b)) * (x1 - x0)
        for yy in range(y0, y1):
            start = (yy * self.width + x0) * 3
            self.buf[start:start + len(row)] = row

    def fill_circle(self, cx: int, cy: int, r: int,
                    colour: tuple[int, int, int]) -> None:
        """Filled circle, scanline by scanline."""
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, colour)

    def triangle(self, cx: int, base_y: int, height: int, half_base: int,
                 colour: tuple[int, int, int]) -> None:
        """Filled triangle, apex at (cx, base_y - height)."""
        for row in range(height):
            half = (row + 1) * half_base // height
            self.fill_rect(cx - half, base_y - height + row,
                           2 * half, 1, colour)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF))


def encode_png(canvas: Canvas) -> bytes:
    """Encode the canvas as a PNG (colour type 2, filter 0 rows)."""
    raw = bytearray()
    row_bytes = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        start = y * row_bytes
        raw += canvas.buf[start:start + row_bytes]
    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height,
                       8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) +
            png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            png_chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# Pictograms. Each draws a simple emblem in a 64x64 box at (ox, oy).
# ---------------------------------------------------------------------------
def draw_icon(canvas: Canvas, kind: str, ox: int, oy: int,
              colour: tuple[int, int, int]) -> None:
    if kind == "globe":
        canvas.fill_circle(ox + 32, oy + 32, 28, colour)
        canvas.fill_rect(ox + 6, oy + 28, 52, 8, PAPER)
        canvas.fill_rect(ox + 28, oy + 6, 8, 52, PAPER)
    elif kind == "chip":
        canvas.fill_rect(ox + 14, oy + 14, 36, 36, colour)
        canvas.fill_rect(ox + 24, oy + 24, 16, 16, PAPER)
        for k in range(3):
            canvas.fill_rect(ox + 4, oy + 18 + k * 12, 10, 6, colour)
            canvas.fill_rect(ox + 50, oy + 18 + k * 12, 10, 6, colour)
            canvas.fill_rect(ox + 18 + k * 12, oy + 4, 6, 10, colour)
            canvas.fill_rect(ox + 18 + k * 12, oy + 50, 6, 10, colour)
    elif kind == "warning":
        canvas.triangle(ox + 32, oy + 58, 52, 30, colour)
        draw_text(canvas, ox + 26, oy + 30, "!", 2, WHITE)
    elif kind == "ballot":
        canvas.fill_rect(ox + 12, oy + 12, 40, 40, colour)
        canvas.fill_rect(ox + 20, oy + 32, 8, 8, PAPER)
        canvas.fill_rect(ox + 26, oy + 38, 8, 8, PAPER)
        canvas.fill_rect(ox + 32, oy + 26, 8, 8, PAPER)
        canvas.fill_rect(ox + 38, oy + 18, 8, 8, PAPER)
    elif kind == "mountains":
        canvas.triangle(ox + 22, oy + 58, 40, 22, colour)
        canvas.triangle(ox + 46, oy + 58, 30, 16, colour)
    elif kind == "court":
        canvas.triangle(ox + 32, oy + 26, 18, 28, colour)
        for k in range(3):
            canvas.fill_rect(ox + 12 + k * 14, oy + 30, 6, 24, colour)
        canvas.fill_rect(ox + 8, oy + 54, 48, 6, colour)
    else:
        raise ValueError(f"unknown icon: {kind!r}")


# ---------------------------------------------------------------------------
# Layout. All coordinates are in pixels on the 1024x1024 page.
# ---------------------------------------------------------------------------
MARGIN = 28
GRID_TOP = 122
PANEL_W = 476
PANEL_H = 236
COL_GAP = 16
ROW_GAP = 12


def render() -> bytes:
    """Draw the front page and return its PNG bytes."""
    page = Canvas(WIDTH, HEIGHT, PAPER)

    # Masthead: paper name, then the day in red, then a double rule.
    draw_text(page, (WIDTH - text_width(MASTHEAD, 4)) // 2, 18,
              MASTHEAD, 4, NAVY)
    draw_text(page, (WIDTH - text_width(DATE_LINE, 5)) // 2, 56,
              DATE_LINE, 5, RED)
    page.fill_rect(MARGIN, 100, WIDTH - 2 * MARGIN, 2, NAVY)
    page.fill_rect(MARGIN, 104, WIDTH - 2 * MARGIN, 1, NAVY)

    for index, story in enumerate(STORIES):
        col = index % 2
        row = index // 2
        x0 = MARGIN + col * (PANEL_W + COL_GAP)
        y0 = GRID_TOP + row * (PANEL_H + ROW_GAP)
        accent = story["accent"]

        # Panel border and accent top bar.
        page.fill_rect(x0, y0, PANEL_W, 1, RULE)
        page.fill_rect(x0, y0 + PANEL_H - 1, PANEL_W, 1, RULE)
        page.fill_rect(x0, y0, 1, PANEL_H, RULE)
        page.fill_rect(x0 + PANEL_W - 1, y0, 1, PANEL_H, RULE)
        page.fill_rect(x0, y0, PANEL_W, 8, accent)

        # Number badge on the left, pictogram beside it, tag at right.
        page.fill_rect(x0 + 16, y0 + 24, 64, 64, accent)
        digit = str(index + 1)
        draw_text(page, x0 + 16 + (64 - text_width(digit, 4)) // 2,
                  y0 + 24 + (64 - 7 * 4) // 2, digit, 4, WHITE)
        draw_icon(page, story["icon"], x0 + 96, y0 + 24, accent)
        tag = story["tag"]
        draw_text(page, x0 + PANEL_W - 16 - text_width(tag, 2),
                  y0 + 28, tag, 2, accent)

        # Headline, wrapped to at most two lines.
        lines = wrap(story["headline"], 3, PANEL_W - 32)
        if len(lines) > 2:
            raise ValueError(f"headline needs {len(lines)} lines: "
                             f"{story!r}")
        for offset, line in enumerate(lines):
            draw_text(page, x0 + 16, y0 + 100 + offset * 24,
                      line, 3, INK)

        # Body copy, wrapped to at most three lines.
        body = wrap(story["body"], 2, PANEL_W - 32)
        if len(body) > 3:
            raise ValueError(f"body needs {len(body)} lines: {story!r}")
        for offset, line in enumerate(body):
            draw_text(page, x0 + 16, y0 + 152 + offset * 22,
                      line, 2, BODY_INK)

    # Footer strip: "ALSO TODAY" plus one line per extra story.
    foot_top = GRID_TOP + 3 * PANEL_H + 2 * ROW_GAP + 18
    page.fill_rect(MARGIN, foot_top, WIDTH - 2 * MARGIN, 2, NAVY)
    draw_text(page, MARGIN, foot_top + 12, "ALSO TODAY", 2, RED)
    for offset, item in enumerate(ALSO):
        y = foot_top + 34 + offset * 20
        if text_width(item, 2) > WIDTH - 2 * MARGIN - 20:
            raise ValueError(f"footer item too wide: {item!r}")
        page.fill_rect(MARGIN, y + 3, 8, 8, NAVY)
        draw_text(page, MARGIN + 20, y, item, 2, BODY_INK)

    return encode_png(page)


def list_stories() -> str:
    out = [f"{DATE_LINE} — {MASTHEAD}", ""]
    for index, story in enumerate(STORIES, 1):
        out.append(f"{index}. {story['headline']} [{story['tag']}]")
        out.append(f"   {story['body']}")
        out.append("")
    out.append("ALSO:")
    for item in ALSO:
        out.append(f"   - {item}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Draw the 24 November 2026 world-news image.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true",
                       help="print the stories the image encodes")
    group.add_argument("--check", action="store_true",
                       help="verify entry.png beside this script matches "
                            "a fresh render, byte for byte")
    args = parser.parse_args(argv)

    if args.list:
        print(list_stories())
        return 0

    data = render()

    if args.check:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "entry.png")
        if not os.path.isfile(path):
            print("entry.png not found beside main.py", file=sys.stderr)
            return 1
        with open(path, "rb") as handle:
            stored = handle.read()
        if stored == data:
            print(f"ok: entry.png matches a fresh render "
                  f"({len(data)} bytes)")
            return 0
        print("entry.png differs from a fresh render", file=sys.stderr)
        return 1

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    with open(dest, "wb") as handle:
        handle.write(data)
    if len(data) > MAX_BYTES:
        print(f"entry.png is {len(data)} bytes, over the 1 MiB limit",
              file=sys.stderr)
        return 1
    print(f"wrote {dest} ({len(data)} bytes, {WIDTH}x{HEIGHT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
