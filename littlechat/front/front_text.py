import logging

import urwid
from urwid import WHSettings, WrapMode, TextCanvas, Align
from urwid.util import *
from urwid.text_layout import *

from littlechat.front.front_text_layout import FrontTextLayout
from littlechat.front.front_text_canvas import FrontTextCanvas

logger = logging.getLogger("client")


def apply_text_layout(text, attr, ls, maxcol: int, adjusted: bool,
                      add_blank_side=True):
    t = []
    a = []
    c = []

    class AttrWalk:
        pass

    aw = AttrWalk
    aw.k = 0  # counter for moving through elements of a
    aw.off = 0  # current offset into text of attr[ak]

    def arange(start_offs: int, end_offs: int):
        """Return an attribute list for the range of text specified."""
        if start_offs < aw.off:
            aw.k = 0
            aw.off = 0
        o = []
        # the loop should run at least once, the '=' part ensures that
        while aw.off <= end_offs:
            if len(attr) <= aw.k:
                # run out of attributes
                o.append((None, end_offs - max(start_offs, aw.off)))
                break
            at, run = attr[aw.k]
            if aw.off + run <= start_offs:
                # move forward through attr to find start_offs
                aw.k += 1
                aw.off += run
                continue
            if end_offs <= aw.off + run:
                o.append((at, end_offs - max(start_offs, aw.off)))
                break
            o.append((at, aw.off + run - max(start_offs, aw.off)))
            aw.k += 1
            aw.off += run
        return o

    for line_layout in ls:
        # trim the line to fit within maxcol
        line_layout = trim_line(line_layout, text, 0, maxcol)

        line = []
        linea = []
        linec = []

        def attrrange(start_offs: int, end_offs: int, destw: int) -> None:
            """
            Add attributes based on attributes between
            start_offs and end_offs.
            """
            if start_offs == end_offs:
                [(at, run)] = arange(start_offs, end_offs)
                rle_append_modify(linea, (at, destw))
                return
            if destw == end_offs - start_offs:
                for at, run in arange(start_offs, end_offs):
                    rle_append_modify(linea, (at, run))
                return
            # encoded version has different width
            o = start_offs
            for at, run in arange(start_offs, end_offs):
                if o + run == end_offs:
                    rle_append_modify(linea, (at, destw))
                    return
                tseg = text[o:o + run]
                tseg, cs = apply_target_encoding(tseg)
                segw = rle_len(cs)

                rle_append_modify(linea, (at, segw))
                o += run
                destw -= segw

        for seg in line_layout:
            # if seg is None: assert 0, ls
            s = LayoutSegment(seg)
            if s.end:
                tseg, cs = apply_target_encoding(
                    text[s.offs:s.end])
                line.append(tseg)
                attrrange(s.offs, s.end, rle_len(cs))
                rle_join_modify(linec, cs)
            elif s.text:
                tseg, cs = apply_target_encoding(s.text)
                line.append(tseg)
                attrrange(s.offs, s.offs, len(tseg))
                rle_join_modify(linec, cs)
            elif s.offs:
                if s.sc:
                    line.append(b''.rjust(s.sc))
                    attrrange(s.offs, s.offs, s.sc)
            else:
                line.append(b''.rjust(s.sc))
                linea.append((None, s.sc))
                linec.append((None, s.sc))

        # adjust
        if add_blank_side:
            for i in range(len(line)):  # line: [b"test",]
                added = False
                if line[i].strip():
                    line[i] = b" " + line[i] + b" "
                    added = True
                try:  # adjust linea to right width
                    if added and i < len(linea):  # linea: [(None, 4)]
                        linea[i] = (linea[i][0], linea[i][1] + 2)
                    if added and i < len(linec):
                        linec[i] = (linec[i][0], linec[i][1] + 2)
                except Exception as exp:
                    logger.info(f"i: {i}, \n"
                                f"linea: {linea}, \n"
                                f"linec: {linec}")
                    raise

        t.append(b''.join(line))
        a.append(linea)
        c.append(linec)

    # logger.info(f"""inside apply:
    # maxcol: {maxcol}
    # att: {attr},
    # canvas attr: {a}
    # t: {t}
    # """)
    return FrontTextCanvas(t, a, c, maxcol=maxcol)
    # return TextCanvas(t, a, c, maxcol=maxcol)


class FrontText(urwid.Text):

    def __init__(self, markup, align=Align.LEFT, wrap=WrapMode.SPACE,
                 layout=None):
        if layout is None:
            layout = FrontTextLayout()

        # force to transform to bytes
        if isinstance(markup, tuple):
            if not isinstance(markup[1], bytes):
                markup = markup[:-1] + (markup[-1].encode(),)
        elif not isinstance(markup, bytes):
            markup = markup.encode()
        super().__init__(markup, align, wrap=wrap, layout=layout)

    def render(self, size, focus: bool = False,
               add_blank_side=True) -> TextCanvas:
        (maxcol,) = size
        text, attr = self.get_text()

        adjust_max_col, adjusted = self.adjust_max_col(maxcol)
        #logger.info(f"attr before: {attr}")
        trans = self.get_line_translation(adjust_max_col, (text, attr))
        #logger.info(f"attr after: {attr}")
        text_canvas = apply_text_layout(text, attr, trans, maxcol, adjusted,
                                        add_blank_side)
        #logger.info(f"attr after2: {attr}")

        return text_canvas

    @classmethod
    def adjust_max_col(cls, maxcol):
        adjust_max_col = maxcol
        adjusted = False
        if adjust_max_col > 3:
            adjust_max_col -= 2
            adjusted = True
        return adjust_max_col, adjusted

    def pack(self, size=None, focus=False):
        """
        Return the number of screen columns and rows required for
        this Text widget to be displayed without wrapping or
        clipping, as a single element tuple.

        :param size: ``None`` for unlimited screen columns or (*maxcol*,) to
                     specify a maximum column size
        :type size: widget size

        (8, 2)
        """
        text, attr = self.get_text()

        if size is not None:
            if len(size) == 0:
                size = (1, )
            (maxcol,) = size
            if not hasattr(self.layout, "pack"):
                return size

            adjust_max_col, adjusted = self.adjust_max_col(maxcol)
            trans = self.get_line_translation(adjust_max_col, (text, attr))

            if adjusted:
                for tran in trans:
                    adjust_col = tran[0][0] + 2
                    if adjust_col >= maxcol:
                        adjust_col = maxcol
                    tran[0] = (adjust_col,) + tran[0][1:]

            cols = self.layout.pack(maxcol, trans)

            return (cols, len(trans))

        i = 0
        cols = 0
        while i < len(text):
            j = text.find("\n", i)
            if j == -1:
                j = len(text)
            c = calc_width(text, i, j)
            if c > cols:
                cols = c
            i = j + 1

        return (cols, text.count("\n") + 1)


if __name__ == "__main__":
    # urwid.StandardTextLayout()
    t = FrontText("111111222222333333444444555555")

    tt = t.render((4,)).text
    print(tt)
    print(len(tt[-1]))
