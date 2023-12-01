import urwid
from urwid import CompositeCanvas

from littlechat.front.front_text import FrontText, apply_text_layout
from littlechat.front import front_text_layout as text_layout


class FrontEdit(urwid.Edit):

    @classmethod
    def adjust_max_col(cls, maxcol):
        return maxcol, False

    def get_line_translation(self, maxcol: int, ta=None):
        trans = FrontText.get_line_translation(self, maxcol, ta)
        if not self._shift_view_to_cursor:
            return trans

        text, ignore = self.get_text()
        x, y = self._layout.calc_coords(text, trans, self.edit_pos + len(self.caption))
        if x < 0:
            return [
                *trans[:y],
                *[self._layout.shift_line(trans[y], -x)],
                *trans[y + 1 :],
            ]

        if x >= maxcol:
            return [
                *trans[:y],
                *[self._layout.shift_line(trans[y], -(x - maxcol + 1))],
                *trans[y + 1 :],
            ]

        return trans

    def position_coords(self, maxcol: int, pos):
        """
        Return (*x*, *y*) coordinates for an offset into self.edit_text.
        """

        p = pos + len(self.caption)
        trans = self.get_line_translation(maxcol)
        x, y = self._layout.calc_coords(self.get_text()[0], trans, p)
        return x, y

    def render_canvas(self, size, focus: bool = False, add_blank_side=False):
        (maxcol,) = size
        text, attr = self.get_text()

        adjust_max_col, adjusted = self.adjust_max_col(maxcol)
        trans = self.get_line_translation(adjust_max_col, (text, attr))
        text_canvas = apply_text_layout(text, attr, trans, maxcol, adjusted,
                                        add_blank_side)

        return text_canvas

    def move_cursor_to_coords(
            self,
            size,
            x: int,
            y: int,
    ) -> bool:
        """
        """
        (maxcol,) = size
        trans = self.get_line_translation(maxcol)
        top_x, top_y = self.position_coords(maxcol, 0)
        if y < top_y or y >= len(trans):
            return False

        pos = self._layout.calc_pos(self.get_text()[0], trans, x, y)
        e_pos = pos - len(self.caption)
        if e_pos < 0:
            e_pos = 0
        if e_pos > len(self.edit_text):
            e_pos = len(self.edit_text)
        self.edit_pos = e_pos
        self.pref_col_maxcol = x, maxcol
        self._invalidate()
        return True

    def render(self, size, focus: bool = False):
        (maxcol,) = size
        self._shift_view_to_cursor = bool(focus)

        canv = self.render_canvas((maxcol,), add_blank_side=False)
        if focus:
            canv = CompositeCanvas(canv)
            canv.cursor = self.get_cursor_coords((maxcol,))

        return canv
