import select
import logging
import pickle
import socket
import traceback

from queue import Queue, Empty

from lchat.stuff.msg_boxes import *
from lchat.stuff.errors import *
from lchat.stuff.config import MsgConfig
from lchat.front.main_page import MainPage
from lchat.front.front_config import Palette
from lchat.utils.util_thread import new_thread

import urwid

logger = logging.getLogger("client")


class Client(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.username = None
        # socket.SOCK_DGRAM - udp
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sending_msg_q = Queue()
        self.receiving_msg_q = Queue()

        self.front_main_page: Optional[MainPage] = None
        self.page_loop: Optional[urwid.MainLoop] = None
        self.is_closed = False

    def _init_front_main_page(self):
        self.front_main_page = MainPage(
            self.username,
            send_msg_callback=self.send_user_msg,
            flush_page_callback=self.flush_page_draw)
        self.page_loop = urwid.MainLoop(self.front_main_page, Palette.PALETTE)
        self.page_loop.screen.set_terminal_properties(colors=256)

    def flush_page_draw(self):
        self.page_loop.draw_screen()

    def start_page_loop(self):
        self.page_loop.run()

    def send_user_msg(self, msg_text: str):
        self.send_msg(UserMsg(username=self.username, msg=msg_text))

    def send_msg(self, msg: MsgBox, direct=False):
        if not msg.msg:
            return
        msg_byte = pickle.dumps(msg)
        if len(msg_byte) > MsgConfig.MSG_LENGTH:
            raise MsgTooLong(len(msg_byte))
        if direct:
            self.udp_socket.sendto(msg_byte, (self.host, self.port))
            return
        self.sending_msg_q.put((msg_byte, (self.host, self.port)))
        if not isinstance(msg, UserHeartbeat):
            logger.info(f"msg length2: {len(msg_byte)}")

    def recv_server_msg(self, timeout=0.5):
        self.udp_socket.settimeout(timeout)
        response, addr = self.udp_socket.recvfrom(MsgConfig.MSG_LENGTH)
        rsp: MsgBox = pickle.loads(response)

        return rsp

    @new_thread
    def receiving_server_msg(self):

        while True:
            if self.is_closed:
                return
            # noinspection PyBroadException
            try:
                self.udp_socket.settimeout(0.5)
                response, addr = self.udp_socket.recvfrom(MsgConfig.MSG_LENGTH)
                recv_msg_box: MsgBox = pickle.loads(response)
                self.front_main_page.show_msg(recv_msg_box, is_self=False)
                self.flush_page_draw()
            except Exception as exp:
                if self.is_closed:
                    return

    @new_thread
    def sending_msg_proxy(self):
        while True:
            if self.is_closed:
                break
            # noinspection PyBroadException
            try:
                logger.info("tset in sending_msg_proxy")
                msg, addr = self.sending_msg_q.get(timeout=0.5)
                # logger.info(f"send msg proxy, msg length: {len(msg)}")
                if not msg:
                    continue
                self.udp_socket.sendto(msg, addr)
                # if not isinstance(msg, UserHeartbeat):
                #     logger.info(f"send msg: {msg.__dict__}")
            except Empty:
                continue
            except Exception as exp:
                logger.error(f"sending_msg_proxy error: {exp} "
                             f"\n{traceback.format_exc()}")
                if self.is_closed:
                    break

    @new_thread
    def keep_sending_heartbeat(self):
        while True:
            if self.is_closed:
                return
            # noinspection PyBroadException
            try:
                time.sleep(1)
                self.send_msg(UserHeartbeat(username=self.username))
            except Exception:
                if self.is_closed:
                    return

    def login(self):
        while True:
            username = input("请输入用户名：")
            username = username.strip()
            if not username:
                continue
            self.send_msg(NewUser(username=username), direct=True)
            rsp: MsgBox = self.recv_server_msg()
            print(rsp.msg)
            if not isinstance(rsp, ExceptionMsg):
                self.username = username
                self._init_front_main_page()
                break

    def check_con(self):
        self.send_msg(ConCheck(), direct=True)
        # expect socket.timeout exception if no response
        self.recv_server_msg(timeout=1)

    def contact(self):
        self.sending_msg_proxy()
        try:
            self.check_con()
            self.login()
            self.receiving_server_msg()
            self.keep_sending_heartbeat()
            self.start_page_loop()
        except socket.timeout:
            print(f"server: {self.host}:{self.port} is not reachable !!!")
        except KeyboardInterrupt:
            self.close()
        finally:
            self.close()

    def close(self):
        if not self.is_closed and self.username:
            self.send_msg(UserOffline(username=self.username), direct=True)
            if self.front_main_page:
                self.front_main_page.close()
            if self.page_loop:
                self.page_loop.stop()
            self.udp_socket.close()
            print(F"\nBYE BYE, {self.username}")

        self.is_closed = True

    def __del__(self):
        self.close()


if __name__ == '__main__':
    from lchat.utils.util_log import set_scripts_logging

    set_scripts_logging(__file__, logger=logger, level=logging.DEBUG,
                        console_log=False, file_mode="w")
    Client("0.0.0.0", 12345).contact()
