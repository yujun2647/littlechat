import traceback
from typing import *

import time
import logging
from queue import Empty, Queue
from threading import Lock

import urwid
from urwid import WHSettings

from lchat.stuff.msg_boxes import MsgBox, UserMsg, UserDict, TimeStamp
from lchat.utils.util_thread import new_thread
from lchat.stuff.errors import *
from lchat.front.front_config import Palette
from lchat.front.front_msg import FrontMsg
from lchat.front.front_text_layout import FrontTextLayout
from lchat.front.front_edit import FrontEdit
from lchat.front.front_button import FrontButton
from lchat.front.front_emojis import get_all_emojis, FavoriteEmoji


class _EmojiColumn(urwid.Columns):
    pass


class _EditBoxCaption(object):

    def __init__(self, edit_box: FrontEdit, username, attr_name="title",
                 is_locked=False):
        self.edit_box = edit_box
        self.username = username
        self.attr_name = attr_name
        self._is_locked = is_locked

    def update_caption(self):
        c_username = f" {self.username} | "
        c_is_locked = f"| LOCKED " if self._is_locked else ""
        caption = (self.attr_name, f"{c_username}INPUT BOX: {c_is_locked}\n")
        self.edit_box.set_caption(caption)

    @property
    def is_locked(self):
        return self._is_locked

    @is_locked.setter
    def is_locked(self, flag: bool):
        self._is_locked = flag
        self.update_caption()


class MainPage(urwid.Columns):

    def __init__(self, username=None,
                 send_msg_callback: Optional[Callable] = None,
                 flush_page_callback: Optional[Callable] = None):
        msg_box = [urwid.Text(("title", "Message box\n"))]
        user_box = [urwid.Text(("title", "User box\n"))]
        self.is_close = False
        self.username = username
        self.msg_list = urwid.ListBox(urwid.SimpleFocusListWalker(msg_box))
        self.u_list = urwid.ListBox(urwid.SimpleFocusListWalker(user_box))
        self.msg_list_line = urwid.LineBox(self.msg_list)
        self.user_list_line = urwid.LineBox(self.u_list)

        self.edit_box = FrontEdit(allow_tab=True,
                                  layout=FrontTextLayout())

        self._edit_box_caption = _EditBoxCaption(self.edit_box, username)
        self._edit_box_caption.update_caption()

        self.edit_pile_line = urwid.LineBox(
            urwid.Pile([
                self.edit_box,
                urwid.Divider(),
                urwid.Divider(),
                urwid.Divider(),
                urwid.Divider(),
            ]))
        self.emoji_button = FrontButton(
            " 😀", on_press=self._on_click_emoji_box)

        tools = [
            (WHSettings.PACK, self.emoji_button),
            (WHSettings.PACK, urwid.Text("|")),
        ]

        self.tool_boxes = urwid.Columns(tools, dividechars=1)

        self.footer = urwid.Pile([
            self.tool_boxes,
            self.edit_pile_line
        ])

        self.main_frame = urwid.Frame(body=self.msg_list_line,
                                      footer=self.footer,
                                      focus_part="footer")

        self.last_msg_time: Optional[int] = 0

        super().__init__([
            ("weight", 1.5, self.user_list_line),
            ("weight", 8, self.main_frame)],
            focus_column=1)

        self.focus_on_edit_box()

        self.msg = None
        self.send_msg_callback = send_msg_callback
        self.flush_page_callback = flush_page_callback
        self.lock_sig = Queue()
        self._keep_focus_on_edit_box()
        self._show_msg_lock = Lock()
        self._emoji_lock = Lock()
        self._favorite_emoji = FavoriteEmoji(self.username)
        self._emojis_box_expanded = False
        self._all_emoji_buttons = None
        self._show_favorite_emojis()
        self._pre_update_fav_emojis = {}
        self._last_enter_time_ns = time.time_ns()
        self._last_keypress_time_ns = time.time_ns()

    @property
    def all_emoji_buttons(self):
        if self._all_emoji_buttons is None:
            self._all_emoji_buttons = [
                FrontButton(emoji, on_press=self.onclick_select_emoji)
                for emoji in get_all_emojis()]
        return self._all_emoji_buttons

    def _show_favorite_emojis(self):
        favorite_emoji_widgets = [
            (FrontButton(emoji, on_press=self.onclick_select_emoji),
             (WHSettings.PACK, None, False)
             )
            for emoji in self._favorite_emoji.favorite_emojis]

        fnum = FavoriteEmoji.FAVORITE_NUM
        if favorite_emoji_widgets:
            self.tool_boxes.contents[2:fnum + 2] = favorite_emoji_widgets[:fnum]

    def _note_fav_emoji_selected(self, emoji: str):
        if emoji not in self._pre_update_fav_emojis:
            self._pre_update_fav_emojis[emoji] = 0
        self._pre_update_fav_emojis[emoji] += 1

    def _update_fav_emojis(self):
        self._favorite_emoji.update_favorites(self._pre_update_fav_emojis)
        self._pre_update_fav_emojis.clear()
        self._show_favorite_emojis()

    def _handle_hotkey_favorite_emoji(self, keypress_judge):
        emoji_index = int(keypress_judge[-1]) - 1
        fnum = FavoriteEmoji.FAVORITE_NUM
        favorite_emojis = self.tool_boxes.contents[2:fnum + 2]
        if len(favorite_emojis) <= emoji_index:
            return

        select_emoji = favorite_emojis[emoji_index]
        select_emoji_button: FrontButton = select_emoji[0]
        self.onclick_select_emoji(select_emoji_button)

    def _expend_emoji_box(self):
        emoji_grid = urwid.LineBox(
            urwid.GridFlow(self.all_emoji_buttons,
                           cell_width=3, h_sep=0, v_sep=1,
                           align="left"))

        emojis_column = _EmojiColumn([
            ("weight", 0.01, urwid.Divider()),
            ("weight", 9, emoji_grid),
            ("weight", 0.99, urwid.Divider())
        ])

        self.footer.contents.insert(0, (emojis_column, (WHSettings.WEIGHT, 1)))
        self._emojis_box_expanded = True

    def _fold_emoji_box(self):
        for i, item in enumerate(self.footer.contents):
            widget, _ = item
            if isinstance(widget, _EmojiColumn):
                self.footer.contents.pop(i)
                break
        self._emojis_box_expanded = False

    def _on_click_emoji_box(self, button=None):
        with self._emoji_lock:
            if self._emojis_box_expanded:
                self._fold_emoji_box()

                self.focus_on_edit_box()
                return

            self._expend_emoji_box()

            self.focus_on_edit_box()

    def onclick_select_emoji(self, button: FrontButton):
        text = button.label.decode().strip()
        self.edit_box.insert_text(text)
        self._note_fav_emoji_selected(text)
        self.focus_on_edit_box()

    def refresh_page(self):
        if self.flush_page_callback is not None:
            self.flush_page_callback()

    def focus_on_edit_box(self):
        self.focus_position = 1
        self.footer.focus_position = len(self.footer.contents) - 1
        self.main_frame.focus_position = "footer"

    @new_thread
    def _keep_focus_on_edit_box(self):
        lock_focus = False
        while True:
            if self.is_close:
                return
            try:
                self.lock_sig.get(timeout=0.5)
                if not lock_focus:
                    self.focus_on_edit_box()
                    lock_focus = True
                    self._edit_box_caption.is_locked = True
                    self.refresh_page()

                else:
                    lock_focus = False
                    self._edit_box_caption.is_locked = False
                    self.refresh_page()
            except Empty:
                if lock_focus:
                    self.focus_on_edit_box()

    def send_msg(self, msg):
        # noinspection PyBroadException
        try:
            if self.send_msg_callback is not None:
                self.send_msg_callback(msg)
        except MsgTooLong:
            raise
        except Exception as exp:
            logger.error(f"send msg failed, {traceback.format_exc()}")
        return msg

    def show_msg(self, msg_box: MsgBox, is_self=True):
        with self._show_msg_lock:
            if isinstance(msg_box, UserDict):
                self.u_list.body[1:] = FrontMsg.get_user_list_widgets(msg_box)
                return

            msg_box.is_self = is_self
            if time.time() - self.last_msg_time > 60:
                time_widget = FrontMsg.get_msg_widget(
                    TimeStamp(msg_box.get_msg_time_str()))
                self.msg_list.body.append(time_widget)
                self.msg_list.body.append(urwid.Divider())

            msg_widget = FrontMsg.get_msg_widget(msg_box)

            self.msg_list.body.append(msg_widget)
            self.msg_list.body.append(urwid.Divider())
            self.msg_list.focus_position = len(self.msg_list.body) - 1
            self.last_msg_time = time.time()

    def keypress(self, size, key):
        # print(f"\n\nmain_page keypress: {key} cost: {cost} ns")
        this_keypress_time = time.time_ns()
        keypress_gap = this_keypress_time - self._last_keypress_time_ns
        self._last_keypress_time_ns = this_keypress_time
        keypress_judge = key.lower()
        # print(f"main_page edit size: {size} key: {key}")
        emoji_hotkeys = [f"meta {i + 1}" for i in
                         range(FavoriteEmoji.FAVORITE_NUM)]
        if keypress_judge in emoji_hotkeys:
            self._handle_hotkey_favorite_emoji(keypress_judge)
            return

        if keypress_judge == "meta l":
            # lock/unlock focus in edit box
            self.lock_sig.put(1)
            return

        key = super().keypress(size, key)

        if keypress_judge == "meta enter":
            self.edit_box.insert_text("\n")
            return key

        if keypress_judge == "meta e":
            self._on_click_emoji_box()
            return

        if keypress_judge != 'enter':
            return key

        this_enter_time = time.time_ns()
        enter_gap = time.time_ns() - self._last_enter_time_ns
        self._last_enter_time_ns = this_enter_time
        if keypress_gap < 9000000 or enter_gap < 9000000:
            self.edit_box.insert_text("\n")
            return key

        msg = self.edit_box.edit_text.rstrip()
        if not msg:
            return

        self._fold_emoji_box()
        try:
            self.send_msg(msg)
        except MsgTooLong:
            self.edit_box.insert_text("[Msg is too long]")
            return key

        username = "Me" if self.username is None else self.username

        self.show_msg(UserMsg(username=username, msg=msg))

        self.edit_box.edit_text = ""
        self._update_fav_emojis()

    def close(self):
        self.is_close = True

    def __del__(self):
        self.close()


if __name__ == "__main__":
    from lchat.utils.util_log import set_scripts_logging

    logger = logging.getLogger("client")

    import atexit

    atexit.register(lambda: logger.info("test atexitatexitatexit"))

    set_scripts_logging(__file__, logger=logger, level=logging.DEBUG,
                        console_log=False, file_mode="w")


    def test_handled_input(key):
        logger.info(key)


    def flush():
        loop.draw_screen()


    msg_page = MainPage(flush_page_callback=flush)

    loop = urwid.MainLoop(msg_page, Palette.PALETTE)

    loop.screen.set_terminal_properties(colors=256)
    try:
        loop.run()
    except KeyboardInterrupt:
        logger.info(f"KeyboardInterrupt stop")
        loop.stop()
