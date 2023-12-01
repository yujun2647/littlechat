import urwid
from urwid import WHSettings

from littlechat.stuff.msg_boxes import MsgBox, ServerMsg, UserDict
from littlechat.front.front_config import Palette
from littlechat.front.front_text import FrontText


class FrontMsg(object):

    @staticmethod
    def get_user_list_widgets(msg_box: UserDict) -> list:
        users = msg_box.user_dict.keys()
        user_list_widgets = []
        for user in users:
            user_list_widgets.append(
                urwid.Padding(
                    urwid.AttrMap(
                        FrontText((Palette.USER_LIST, user)),
                        Palette.MSG_PURPLE
                    ), "left", "pack"))
            user_list_widgets.append(urwid.Divider())
        return user_list_widgets

    @staticmethod
    def get_msg_widget(msg_box: MsgBox) -> urwid.Columns:
        if isinstance(msg_box, ServerMsg):
            cols = [
                ("weight", 0.1, urwid.Divider()),
                ("weight", 9.8, urwid.Padding(
                    urwid.AttrMap(
                        FrontText((Palette.SERVER_MSG, msg_box.msg)),
                        Palette.MSG_PURPLE
                    ), "center", "pack")),
                ("weight", 0.1, urwid.Divider()),
            ]
            return urwid.Columns(cols)

        align = "left"
        display_attr = Palette.MSG_GREEN
        msg_box.msg = f"{msg_box.msg}"
        if not msg_box.is_self:
            align = "right"
            display_attr = Palette.MSG_PURPLE

        col1_list = [
            (WHSettings.PACK,
             urwid.Text((Palette.WHITE, f"{msg_box.username}"))),
            (WHSettings.PACK, urwid.Text((Palette.ORANGE, " "))),
            urwid.Padding(
                urwid.AttrMap(
                    FrontText((display_attr, msg_box.msg)),
                    display_attr
                ), align, "pack"),

        ]

        if not msg_box.is_self:
            col1_list.reverse()

        basic_msg_wid = urwid.Columns(col1_list)

        cols2_list = [
            ("weight", 7, urwid.Padding(basic_msg_wid, align, "pack")),
            ("weight", 3, urwid.Divider()),
        ]
        if not msg_box.is_self:
            cols2_list.reverse()

        return urwid.Columns(cols2_list)


if __name__ == "__main__":
    from littlechat.stuff.msg_boxes import UserMsg
    from urwid import raw_display

    body = [urwid.Divider()]

    test_list = urwid.LineBox(urwid.ListBox(urwid.SimpleFocusListWalker(body)))

    # msg = UserMsg(username="我我", msg="这是一条测试消息")
    # msg.is_self = True
    #
    # test_list.base_widget.body.append(FrontMsg.get_msg_widget(
    #     msg
    # ))
    #
    # test_list.base_widget.body.append(FrontMsg.get_msg_widget(
    #     UserMsg(username="自我", msg="这是一条测试长消息, 思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #                                  "思考的基辅罗斯肯定激发理解"
    #             )
    # ))
    #test_list.base_widget.body.append(urwid.Divider())
    test_list.base_widget.body.append(FrontMsg.get_msg_widget(
        UserMsg(username="self", msg="this is a test message 测测😊😊😊😊😊"
                )
    ))

    screen = raw_display.Screen()
    screen._started = True
    screen.set_terminal_properties(colors=256)
    screen_size = screen.get_cols_rows()

    canvas = test_list.render(screen_size, focus=True)
    screen.draw_screen(screen_size, canvas)

    # loop = urwid.MainLoop(test_list, Palette.PALETTE)
    # loop.screen.set_terminal_properties(colors=256)
    # loop.run()
