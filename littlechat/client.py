import json
import os
import logging
import pickle
import socket
import traceback

from queue import Queue, Empty

from littlechat.stuff.msg_boxes import *
from littlechat.stuff.errors import *
from littlechat.stuff.config import MsgConfig
from littlechat.front.main_page import MainPage
from littlechat.front.front_config import Palette
from littlechat.utils.util_thread import new_thread
from littlechat.utils.util_path import get_cache_data_filepath

import urwid

logger = logging.getLogger("client")


class Client(object):
    _LAST_CLIENT_FILE = get_cache_data_filepath(filename="last_client.json")
    _LAST_CLIENT = {}

    def _load_last_client(self):
        if not os.path.exists(self._LAST_CLIENT_FILE):
            return
        with open(self._LAST_CLIENT_FILE, "r") as fp:
            self._LAST_CLIENT = json.load(fp)

    def _check_last_client(self):
        if not self._LAST_CLIENT:
            pass
        if not self.host:
            self.host = self._LAST_CLIENT["host"]
        if not self.port:
            self.port = self._LAST_CLIENT["port"]

        self._LAST_CLIENT["host"] = self.host
        self._LAST_CLIENT["port"] = self.port

    def _cache_this_client(self):
        with open(self._LAST_CLIENT_FILE, "w") as fp:
            json.dump(self._LAST_CLIENT, fp)

    def __init__(self, host, port):
        self._load_last_client()
        self.host = host
        self.port = port
        self._check_last_client()
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
                self._cache_this_client()
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


def client(host, port):
    from littlechat.utils.util_log import set_scripts_logging

    set_scripts_logging(__file__, logger=logger, level=logging.DEBUG,
                        console_log=False, file_mode="a")
    Client(host, port).contact()


if __name__ == '__main__':
    client("0.0.0,0", port=12345)
