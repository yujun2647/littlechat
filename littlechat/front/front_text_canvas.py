from urwid.canvas import TextCanvas, CanvasError
from urwid.util import (
    apply_target_encoding,
    calc_text_pos,
    calc_width,
    rle_append_modify,
    rle_join_modify,
    rle_len,
    rle_product,
    trim_text_attr_cs,
)

from littlechat.front.front_text_layout import FrontTextLayout


class FrontTextCanvas(TextCanvas):

    def __init__(
            self,
            text,
            attr=None,
            cs=None,
            cursor=None,
            maxcol=None,
            check_width: bool = True,
    ) -> None:
        """
        text -- list of strings, one for each line
        attr -- list of run length encoded attributes for text
        cs -- list of run length encoded character set for text
        cursor -- (x,y) of cursor or None
        maxcol -- screen columns taken by this canvas
        check_width -- check and fix width of all lines in text
        """
        super(TextCanvas, self).__init__()
        if text is None:
            text = []

        if check_width:
            widths = []
            for t in text:
                if not isinstance(t, bytes):
                    raise CanvasError(
                        "Canvas text must be plain strings encoded in the screen's encoding",
                        repr(text))
                widths.append(FrontTextLayout.calc_width(t, 0, len(t)))
        else:
            assert isinstance(maxcol, int)
            widths = [maxcol] * len(text)

        if maxcol is None:
            if widths:
                # find maxcol ourselves
                maxcol = max(widths)
            else:
                maxcol = 0

        if attr is None:
            attr = [[] for _ in range(len(text))]
        if cs is None:
            cs = [[] for _ in range(len(text))]

        # pad text and attr to maxcol
        for i in range(len(text)):
            w = widths[i]
            if w > maxcol:
                raise CanvasError(
                    f"Canvas text is wider than the maxcol specified \n{maxcol!r}\n{widths!r}\n{text!r}")
            if w < maxcol:
                text[i] += b''.rjust(maxcol - w)
            a_gap = len(text[i]) - rle_len(attr[i])
            if a_gap < 0:
                raise CanvasError(
                    f"Attribute extends beyond text \n{text[i]!r}\n{attr[i]!r}: maxcol: {maxcol}\n"
                    f"i: {i}, length text: {len(text[i])}: attr[i]: {attr[i]}")
            if a_gap:
                rle_append_modify(attr[i], (None, a_gap))

            cs_gap = len(text[i]) - rle_len(cs[i])
            if cs_gap < 0:
                raise CanvasError(
                    f"Character Set extends beyond text \n{text[i]!r}\n{cs[i]!r}")
            if cs_gap:
                rle_append_modify(cs[i], (None, cs_gap))

        self._attr = attr
        self._cs = cs
        self.cursor = cursor
        self._text = text
        self._maxcol = maxcol
        #print("debug")
