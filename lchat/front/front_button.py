import urwid
from urwid import Button, Columns, SelectableIcon, WHSettings, Align, WrapMode, \
    Sizing
from urwid.signals import connect_signal
from urwid.canvas import CompositeCanvas

from lchat.front.front_emojis import get_all_emojis
from lchat.front.front_text_layout import FrontTextLayout
from lchat.front.front_text import FrontText, apply_text_layout


class FixSelectableIcon(FrontText):
    ignore_focus = False
    _selectable = True

    def __init__(
            self,
            text,
            cursor_position: int = 0,
            align=Align.LEFT,
            wrap=WrapMode.SPACE,
            layout=None,
    ) -> None:
        """
        :param text: markup for this widget; see :class:`Text` for
                     description of text markup
        :param cursor_position: position the cursor will appear in the
                                text when this widget is in focus
        :param align: typically ``'left'``, ``'center'`` or ``'right'``
        :type align: text alignment mode
        :param wrap: typically ``'space'``, ``'any'``, ``'clip'`` or ``'ellipsis'``
        :type wrap: text wrapping mode
        :param layout: defaults to a shared :class:`StandardTextLayout` instance
        :type layout: text layout instance

        This is a text widget that is selectable.  A cursor
        displayed at a fixed location in the text when in focus.
        This widget has no special handling of keyboard or mouse input.
        """
        super().__init__(text, align=align, wrap=wrap, layout=layout)
        self._cursor_position = cursor_position

    def render_canvas(self, size, focus: bool = False, add_blank_side=False):
        (maxcol,) = size
        text, attr = self.get_text()

        adjust_max_col, adjusted = self.adjust_max_col(maxcol)
        trans = self.get_line_translation(adjust_max_col, (text, attr))
        text_canvas = apply_text_layout(text, attr, trans, maxcol, adjusted,
                                        add_blank_side)

        return text_canvas

    def render(self, size, focus: bool = False):

        c = self.render_canvas(size, focus, add_blank_side=False)
        if focus:
            # create a new canvas so we can add a cursor
            c = CompositeCanvas(c)
            c.cursor = self.get_cursor_coords(size)
        return c

    def get_cursor_coords(self, size):
        """
        Return the position of the cursor if visible.  This method
        is required for widgets that display a cursor.
        """
        if self._cursor_position > len(self.text):
            return None
        # find out where the cursor will be displayed based on
        # the text layout
        (maxcol,) = size
        trans = self.get_line_translation(maxcol)
        x, y = self._layout.calc_coords(self.text, trans, self._cursor_position)
        if maxcol <= x:
            return None
        return x, y

    def keypress(self, size, key: str) -> str:
        """
        No keys are handled by this widget.  This method is
        required for selectable widgets.
        """
        return key


class FrontButton(Button):

    def __init__(self, label, on_press=None, user_data=None, *,
                 align=Align.CENTER, wrap=WrapMode.SPACE,
                 layout=FrontTextLayout()):
        self._label = FixSelectableIcon(label, 0, align=align, wrap=wrap,
                                        layout=layout)

        super(Button, self).__init__(self._label)

        # The old way of listening for a change was to pass the callback
        # in to the constructor.  Just convert it to the new way:
        if on_press:
            connect_signal(self, "click", on_press, user_data)
