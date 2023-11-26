from urwid import text_layout
from urwid.text_layout import StandardTextLayout
from urwid.util import within_double_byte


class CanNotDisplayText(Exception):
    pass


_byte_encoding = "utf8"

import re
import typing

if typing.TYPE_CHECKING:
    from typing_extensions import Literal

SAFE_ASCII_RE = re.compile("^[ -~]*$")
SAFE_ASCII_BYTES_RE = re.compile(b"^[ -~]*$")

# GENERATED DATA
# generated from
# http://www.unicode.org/Public/4.0-Update/EastAsianWidth-4.0.0.txt

widths = [
    (126, 1),
    (159, 0),
    (687, 1),
    (710, 0),
    (711, 1),
    (727, 0),
    (733, 1),
    (879, 0),
    (1154, 1),
    (1161, 0),
    (4347, 1),
    (4447, 2),
    (7467, 1),
    (7521, 0),
    (8369, 1),
    (8426, 0),
    (9996, 2),  # a emoji- victory
    (9000, 1),
    (9002, 2),
    (11021, 1),
    (12350, 2),
    (12351, 1),
    (12438, 2),
    (12442, 0),
    (19893, 2),
    (19967, 1),
    (55203, 2),
    (63743, 1),
    (64106, 2),
    (65039, 1),
    (65059, 0),
    (65131, 2),
    (65279, 1),
    (65376, 2),
    (65500, 1),
    (65510, 2),
    (120831, 1),
    (130047, 2),  # adjust 1 to 2, I found the size of emojis are in this area,
    # so made this adjustment
    (262141, 2),
    (1114109, 1),
]


# ACCESSOR FUNCTIONS
def get_width(o: int):
    """Return the screen column width for unicode ordinal o."""
    global widths
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1


def decode_one(text, pos: int):
    """
    Return (ordinal at pos, next position) for UTF-8 encoded text.
    """
    lt = len(text) - pos

    b2 = 0  # Fallback, not changing anything
    b3 = 0  # Fallback, not changing anything
    b4 = 0  # Fallback, not changing anything

    try:
        if isinstance(text, str):
            b1 = ord(text[pos])
            if lt > 1:
                b2 = ord(text[pos + 1])
            if lt > 2:
                b3 = ord(text[pos + 2])
            if lt > 3:
                b4 = ord(text[pos + 3])
        else:
            b1 = text[pos]
            if lt > 1:
                b2 = text[pos + 1]
            if lt > 2:
                b3 = text[pos + 2]
            if lt > 3:
                b4 = text[pos + 3]
    except Exception as e:
        raise ValueError(f"{e}: {text=!r}, {pos=!r}, {lt=}").with_traceback(
            e.__traceback__) from e

    if not b1 & 0x80:
        return b1, pos + 1
    error = ord("?"), pos + 1

    if lt < 2:
        return error
    if b1 & 0xe0 == 0xc0:
        if b2 & 0xc0 != 0x80:
            return error
        o = ((b1 & 0x1f) << 6) | (b2 & 0x3f)
        if o < 0x80:
            return error
        return o, pos + 2
    if lt < 3:
        return error
    if b1 & 0xf0 == 0xe0:
        if b2 & 0xc0 != 0x80:
            return error
        if b3 & 0xc0 != 0x80:
            return error
        o = ((b1 & 0x0f) << 12) | ((b2 & 0x3f) << 6) | (b3 & 0x3f)
        if o < 0x800:
            return error
        return o, pos + 3
    if lt < 4:
        return error
    if b1 & 0xf8 == 0xf0:
        if b2 & 0xc0 != 0x80:
            return error
        if b3 & 0xc0 != 0x80:
            return error
        if b4 & 0xc0 != 0x80:
            return error
        o = ((b1 & 0x07) << 18) | ((b2 & 0x3f) << 12) | ((b3 & 0x3f) << 6) | (
                b4 & 0x3f)
        if o < 0x10000:
            return error
        return o, pos + 4
    return error


def decode_one_uni(text: str, i: int):
    """
    decode_one implementation for unicode strings
    """
    return ord(text[i]), i + 1


def is_wide_char(text, offs: int) -> bool:
    """
    Test if the character at offs within text is wide.

    text may be unicode or a byte string in the target _byte_encoding
    """
    if isinstance(text, str):
        o = ord(text[offs])
        return get_width(o) == 2
    assert isinstance(text, bytes)
    if _byte_encoding == "utf8":
        o, n = decode_one(text, offs)
        return get_width(o) == 2
    if _byte_encoding == "wide":
        return within_double_byte(text, offs, offs) == 1
    return False


def move_prev_char(text, start_offs: int, end_offs: int):
    """
    Return the position of the character before end_offs.
    """
    assert start_offs < end_offs
    if isinstance(text, str):
        return end_offs - 1
    assert isinstance(text, bytes)
    if _byte_encoding == "utf8":
        o = end_offs - 1
        while text[o] & 0xc0 == 0x80:
            o -= 1
        return o
    if _byte_encoding == "wide" and within_double_byte(text,
                                                       start_offs,
                                                       end_offs - 1) == 2:
        return end_offs - 2
    return end_offs - 1


def move_next_char(text, start_offs: int, end_offs: int) -> int:
    """
    Return the position of the character after start_offs.
    """
    assert start_offs < end_offs
    if isinstance(text, str):
        return start_offs + 1
    assert isinstance(text, bytes)
    if _byte_encoding == "utf8":
        o = start_offs + 1
        while o < end_offs and text[o] & 0xc0 == 0x80:
            o += 1
        return o
    if _byte_encoding == "wide" and within_double_byte(text, start_offs,
                                                       start_offs) == 1:
        return start_offs + 2
    return start_offs + 1


class TextLayoutCommon(StandardTextLayout):
    class LayoutSegment:
        def __init__(self, seg) -> None:
            """Create object from line layout segment structure"""

            assert isinstance(seg, tuple), repr(seg)
            assert len(seg) in (2, 3), repr(seg)

            self.sc, self.offs = seg[:2]

            assert isinstance(self.sc, int), repr(self.sc)

            if len(seg) == 3:
                assert isinstance(self.offs, int), repr(self.offs)
                assert self.sc > 0, repr(seg)
                t = seg[2]
                if isinstance(t, bytes):
                    self.text = t
                    self.end = None
                else:
                    assert isinstance(t, int), repr(t)
                    self.text = None
                    self.end = t
            else:
                assert len(seg) == 2, repr(seg)
                if self.offs is not None:
                    assert self.sc >= 0, repr(seg)
                    assert isinstance(self.offs, int)
                self.text = self.end = None

        def subseg(self, text, start: int, end: int):
            """
            Return a "sub-segment" list containing segment structures
            that make up a portion of this segment.

            A list is returned to handle cases where wide characters
            need to be replaced with a space character at either edge
            so two or three segments will be returned.
            """
            if start < 0:
                start = 0
            if end > self.sc:
                end = self.sc
            if start >= end:
                return []  # completely gone
            if self.text:
                # use text stored in segment (self.text)
                spos, epos, pad_left, pad_right = TextLayoutCommon.calc_trim_text(
                    self.text, 0,
                    len(self.text),
                    start, end)
                return [(end - start, self.offs,
                         b''.ljust(pad_left) + self.text[spos:epos] + b''.ljust(
                             pad_right))]
            elif self.end:
                # use text passed as parameter (text)
                spos, epos, pad_left, pad_right = TextLayoutCommon.calc_trim_text(
                    text,
                    self.offs,
                    self.end,
                    start, end)
                l = []
                if pad_left:
                    l.append((1, spos - 1))
                l.append((end - start - pad_left - pad_right, spos, epos))
                if pad_right:
                    l.append((1, epos))
                return l
            else:
                # simple padding adjustment
                return [(end - start, self.offs)]

    @classmethod
    def calc_trim_text(cls, text, start_offs: int, end_offs: int,
                       start_col: int,
                       end_col: int):
        """
        Calculate the result of trimming text.
        start_offs -- offset into text to treat as screen column 0
        end_offs -- offset into text to treat as the end of the line
        start_col -- screen column to trim at the left
        end_col -- screen column to trim at the right

        Returns (start, end, pad_left, pad_right), where:
        start -- resulting start offset
        end -- resulting end offset
        pad_left -- 0 for no pad or 1 for one space to be added
        pad_right -- 0 for no pad or 1 for one space to be added
        """
        spos = start_offs
        pad_left = pad_right = 0
        if start_col > 0:
            spos, sc = cls.calc_text_pos(text, spos, end_offs, start_col)
            if sc < start_col:
                pad_left = 1
                spos, sc = cls.calc_text_pos(text, start_offs,
                                             end_offs, start_col + 1)
        run = end_col - start_col - pad_left
        pos, sc = cls.calc_text_pos(text, spos, end_offs, run)
        if sc < run:
            pad_right = 1
        return (spos, pos, pad_left, pad_right)

    @classmethod
    def shift_line(cls, segs, amount: int):
        """
        Return a shifted line from a layout structure to the left or right.
        segs -- line of a layout structure
        amount -- screen columns to shift right (+ve) or left (-ve)
        """
        assert isinstance(amount, int), repr(amount)

        if segs and len(segs[0]) == 2 and segs[0][1] is None:
            # existing shift
            amount += segs[0][0]
            if amount:
                return [(amount, None)] + segs[1:]
            return segs[1:]

        if amount:
            return [(amount, None)] + segs
        return segs

    @classmethod
    def calc_coords(cls, text, layout, pos, clamp: int = 1):
        """
        Calculate the coordinates closest to position pos in text with layout.

        text -- raw string or unicode string
        layout -- layout structure applied to text
        pos -- integer position into text
        clamp -- ignored right now
        """
        closest = None
        y = 0
        for line_layout in layout:
            x = 0
            for seg in line_layout:
                s = cls.LayoutSegment(seg)
                if s.offs is None:
                    x += s.sc
                    continue
                if s.offs == pos:
                    return x, y
                if s.end is not None and s.offs <= pos < s.end:
                    x += cls.calc_width(text, s.offs, pos)
                    return x, y
                distance = abs(s.offs - pos)
                if s.end is not None and s.end < pos:
                    distance = pos - (s.end - 1)
                if closest is None or distance < closest[0]:
                    closest = distance, (x, y)
                x += s.sc
            y += 1

        if closest:
            return closest[1]
        return 0, 0

    @classmethod
    def calc_text_pos(cls, text, start_offs: int, end_offs: int,
                      pref_col: int):
        """
        Calculate the closest position to the screen column pref_col in text
        where start_offs is the offset into text assumed to be screen column 0
        and end_offs is the end of the range to search.

        text may be unicode or a byte string in the target _byte_encoding

        Returns (position, actual_col).
        """
        assert start_offs <= end_offs, repr((start_offs, end_offs))
        utfs = isinstance(text, bytes) and _byte_encoding == "utf8"
        unis = isinstance(text, str)
        if unis or utfs:
            decode = [decode_one, decode_one_uni][unis]
            i = start_offs
            sc = 0
            n = 1  # number to advance by
            while i < end_offs:
                o, n = decode(text, i)
                w = get_width(o)
                if w + sc > pref_col:
                    return i, sc
                i = n
                sc += w
            return i, sc

        assert isinstance(text, bytes), repr(text)
        # "wide" and "narrow"
        i = start_offs + pref_col
        if i >= end_offs:
            return end_offs, end_offs - start_offs
        if _byte_encoding == "wide":
            if within_double_byte(text, start_offs, i) == 2:
                i -= 1
        return i, i - start_offs

    @classmethod
    def calc_width(cls, text, start_offs: int, end_offs: int):
        assert start_offs <= end_offs, repr((start_offs, end_offs))

        utfs = isinstance(text, bytes) and _byte_encoding == "utf8"
        unis = not isinstance(text, bytes)
        if (unis and not SAFE_ASCII_RE.match(text)) or (
                utfs and not SAFE_ASCII_BYTES_RE.match(text)):
            decode = [decode_one, decode_one_uni][unis]
            i = start_offs
            sc = 0
            n = 1  # number to advance by
            while i < end_offs:
                o, n = decode(text, i)
                w = get_width(o)
                i = n
                sc += w
            return sc
        # "wide", "narrow" or all printable ASCII, just return the character count
        return end_offs - start_offs

    @classmethod
    def calc_pos(cls, text, layout, pref_col, row: int) -> int:
        """
        Calculate the closest linear position to pref_col and row given a
        layout structure.
        """

        if row < 0 or row >= len(layout):
            raise ValueError("calculate_pos: out of layout row range")

        pos = cls.calc_line_pos(text, layout[row], pref_col)
        if pos is not None:
            return pos

        rows_above = list(range(row - 1, -1, -1))
        rows_below = list(range(row + 1, len(layout)))
        while rows_above and rows_below:
            if rows_above:
                r = rows_above.pop(0)
                pos = cls.calc_line_pos(text, layout[r], pref_col)
                if pos is not None:
                    return pos
            if rows_below:
                r = rows_below.pop(0)
                pos = cls.calc_line_pos(text, layout[r], pref_col)
                if pos is not None:
                    return pos
        return 0

    @classmethod
    def calc_line_pos(cls, text, line_layout, pref_col):
        """
        Calculate the closest linear position to pref_col given a
        line layout structure.  Returns None if no position found.
        """
        closest_sc = None
        closest_pos = None
        current_sc = 0

        if pref_col == 'left':
            for seg in line_layout:
                s = cls.LayoutSegment(seg)
                if s.offs is not None:
                    return s.offs
            return
        elif pref_col == 'right':
            for seg in line_layout:
                s = cls.LayoutSegment(seg)
                if s.offs is not None:
                    closest_pos = s
            s = closest_pos
            if s is None:
                return
            if s.end is None:
                return s.offs
            return cls.calc_text_pos(text, s.offs, s.end, s.sc - 1)[0]

        for seg in line_layout:
            s = cls.LayoutSegment(seg)
            if s.offs is not None:
                if s.end is not None:
                    if current_sc <= pref_col < current_sc + s.sc:
                        # exact match within this segment
                        return cls.calc_text_pos(text, s.offs, s.end,
                                                 pref_col - current_sc)[0]
                    elif current_sc <= pref_col:
                        closest_sc = current_sc + s.sc - 1
                        closest_pos = s

                if closest_sc is None or (abs(pref_col - current_sc) < abs(
                        pref_col - closest_sc)):
                    # this screen column is closer
                    closest_sc = current_sc
                    closest_pos = s.offs
                if current_sc > closest_sc:
                    # we're moving past
                    break
            current_sc += s.sc

        if closest_pos is None or isinstance(closest_pos, int):
            return closest_pos

        # return the last positions in the segment "closest_pos"
        s = closest_pos
        return cls.calc_text_pos(text, s.offs, s.end, s.sc - 1)[0]


class FrontTextLayout(TextLayoutCommon):

    def calculate_text_segments(self, text, width: int, wrap):
        nl, nl_o, sp_o = "\n", "\n", " "
        if isinstance(text, bytes):
            nl = nl.encode(
                'iso8859-1')  # can only find bytes in python3 bytestrings
            nl_o = ord(nl_o)  # + an item of a bytestring is the ordinal value
            sp_o = ord(sp_o)
        b = []
        p = 0
        if wrap in ('clip', 'ellipsis'):
            # no wrapping to calculate, so it's easy.
            while p <= len(text):
                n_cr = text.find(nl, p)
                if n_cr == -1:
                    n_cr = len(text)
                sc = self.calc_width(text, p, n_cr)

                # trim line to max width if needed, add ellipsis if trimmed
                if wrap == 'ellipsis' and sc > width:
                    trimmed = True
                    spos, n_end, pad_left, pad_right = self.calc_trim_text(
                        text,
                        p,
                        n_cr,
                        0,
                        width - 1)
                    # pad_left should be 0, because the start_col parameter was 0 (no trimming on the left)
                    # similarly spos should not be changed from p
                    assert pad_left == 0
                    assert spos == p
                    sc = width - 1 - pad_right
                else:
                    trimmed = False
                    n_end = n_cr
                    pad_right = 0

                l = []
                if p != n_end:
                    l += [(sc, p, n_end)]
                if trimmed:
                    l += [(1, n_end, '…'.encode())]
                l += [(pad_right, n_end)]
                b.append(l)
                p = n_cr + 1
            return b

        while p <= len(text):
            # look for next eligible line break
            n_cr = text.find(nl, p)
            if n_cr == -1:
                n_cr = len(text)
            sc = self.calc_width(text, p, n_cr)
            if sc == 0:
                # removed character hint
                b.append([(0, n_cr)])
                p = n_cr + 1
                continue
            if sc <= width:
                # this segment fits
                b.append([(sc, p, n_cr), (0, n_cr)])
                # removed character hint

                p = n_cr + 1
                continue
            pos, sc = self.calc_text_pos(text, p, n_cr, width)
            if pos == p:  # pathological width=1 double-byte case
                raise CanNotDisplayText(
                    "Wide character will not fit in 1-column width")
            if wrap == 'any':
                b.append([(sc, p, pos)])
                p = pos
                continue
            assert wrap == 'space'
            if text[pos] == sp_o:
                # perfect space wrap
                b.append([(sc, p, pos), (0, pos)])
                # removed character hint

                p = pos + 1
                continue
            if is_wide_char(text, pos):
                # perfect next wide
                b.append([(sc, p, pos)])
                p = pos
                continue
            prev = pos
            while prev > p:
                prev = move_prev_char(text, p, prev)
                if text[prev] == sp_o:
                    sc = self.calc_width(text, p, prev)
                    l = [(0, prev)]
                    if p != prev:
                        l = [(sc, p, prev)] + l
                    b.append(l)
                    p = prev + 1
                    break
                if is_wide_char(text, prev):
                    # wrap after wide char
                    next = move_next_char(text, prev, pos)
                    sc = self.calc_width(text, p, next)
                    b.append([(sc, p, next)])
                    p = next
                    break
            else:
                # unwrap previous line space if possible to
                # fit more text (we're breaking a word anyway)
                if b and (len(b[-1]) == 2 or (
                        len(b[-1]) == 1 and len(b[-1][0]) == 2)):
                    # look for removed space above
                    if len(b[-1]) == 1:
                        [(h_sc, h_off)] = b[-1]
                        p_sc = 0
                        p_off = p_end = h_off
                    else:
                        [(p_sc, p_off, p_end), (h_sc, h_off)] = b[-1]
                    if p_sc < width and h_sc == 0 and text[h_off] == sp_o:
                        # combine with previous line
                        del b[-1]
                        p = p_off
                        pos, sc = self.calc_text_pos(
                            text, p, n_cr, width)
                        b.append([(sc, p, pos)])
                        # check for trailing " " or "\n"
                        p = pos
                        if p < len(text) and (text[p] in (sp_o, nl_o)):
                            # removed character hint
                            b[-1].append((0, p))
                            p += 1
                        continue

                # force any char wrap
                b.append([(sc, p, pos)])
                p = pos
        return b

    def layout(
            self,
            text,
            width: int,
            align,
            wrap,
    ):
        """Return a layout structure for text."""
        try:
            segs = self.calculate_text_segments(text, width, wrap)
            test = self.align_layout(text, width, segs, wrap, align)
            return test
        except CanNotDisplayText:
            return [[]]
