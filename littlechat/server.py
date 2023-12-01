import os
import json
import logging
import pickle
import socket as soc
from queue import Queue, Empty

from littlechat.stuff.msg_boxes import *
from littlechat.utils.util_thread import new_thread
from littlechat.stuff.config import MsgConfig
from littlechat.utils.util_path import get_cache_data_filepath

logger = logging.getLogger("server")


class Server(object):
    _LAST_SERVER_FILE = get_cache_data_filepath(filename="last_server.json")
    _LAST_SERVER = {}
    DEFAULT_PORT = 12345

    def __init__(self, port=""):
        self._load_last_server()
        self.port = port
        self._check_last_server()
        self.local_addr = ("0.0.0.0", self.port)

        self.udp_socket = soc.socket(soc.AF_INET, soc.SOCK_DGRAM)
        self.udp_socket.bind(self.local_addr)
        self.client_heartbeat_q = Queue()
        self.sending_msg_queue = Queue()
        self.is_close = False

    def _load_last_server(self):
        if not os.path.exists(self._LAST_SERVER_FILE):
            return
        with open(self._LAST_SERVER_FILE, "r") as fp:
            self._LAST_SERVER = json.load(fp)

    def _check_last_server(self):
        last_port = self._LAST_SERVER.get("port", self.DEFAULT_PORT)
        if not self.port:
            self.port = last_port
            return

    def _update_last_server(self):
        with open(self._LAST_SERVER_FILE, "w") as fp:
            self._LAST_SERVER["port"] = self.port
            json.dump(self._LAST_SERVER, fp)

    def broadcast_expired_users(self, expired_users):
        if not expired_users:
            return

        for user in NewUser.USER_DICT.values():
            for expired_user in expired_users:
                self.sending_msg_queue.put(
                    (UserOfflineServer(expired_user.username),
                     (user.ip, user.port)
                     )
                )

    def broadcast_online_users(self):
        user_dict = UserDict(NewUser.USER_DICT)
        for user in NewUser.USER_DICT.values():
            self.sending_msg_queue.put(
                (user_dict, (user.ip, user.port))
            )

    @new_thread
    def client_alive_check(self):
        while True:
            if self.is_close:
                return
            try:
                uhb: UserHeartbeat = self.client_heartbeat_q.get(timeout=0.5)
                NewUser.update_user_heartbeat_time(uhb)
            except Empty:
                pass
            expired_users = NewUser.check_and_clear_expired_users()
            for user in expired_users:
                logger.info(f"user: {user.username} exit")

            if expired_users:
                self.broadcast_expired_users(expired_users)
                self.broadcast_online_users()

    @new_thread
    def sending_msg_proxy(self):
        while True:
            if self.is_close:
                return
            try:
                msg, addr = self.sending_msg_queue.get(timeout=0.5)
                self.udp_socket.sendto(pickle.dumps(msg), addr)
            except Empty:
                continue

    def serve(self):
        self.client_alive_check()
        self.sending_msg_proxy()
        self._update_last_server()
        # self.keep_check_user_dict()
        logger.info(f"-----server in {self.local_addr}---------")
        while True:
            recv_data, addr = self.udp_socket.recvfrom(MsgConfig.MSG_LENGTH)
            # noinspection PyBroadException
            try:
                msg_box: UserMsg = pickle.loads(recv_data)
                msg_box.ip, msg_box.port = addr
                if not isinstance(msg_box, ClientMsg):
                    raise
                if not msg_box.check_valid():
                    raise

                if isinstance(msg_box, UserHeartbeat):
                    self.client_heartbeat_q.put(msg_box)
                    continue

                rsp_msg = msg_box.get_response_msg()
                broadcast_msg = msg_box.get_broadcast_msg()
                self._send_responses(addr, msg_box.username, rsp_msg,
                                     broadcast_msg)

            except KeyboardInterrupt:
                self.close()
                return
            except Exception as exp:
                # not allow msg
                rsp_msg = ExceptionMsg(msg=f"not allow msg format: {recv_data},"
                                           f"exp: {exp}")
                self._send_responses(addr, None, rsp_msg, None)
                continue

    def _send_responses(self, addr: Tuple, from_username: [str, None],
                        rsp_msg: [MsgBox, None],
                        broadcast_msg: [MsgBox, None]):
        if rsp_msg:
            self.sending_msg_queue.put(
                (rsp_msg, addr)
            )

        if broadcast_msg:
            for user, msg in NewUser.USER_DICT.items():
                if from_username != user:
                    self.sending_msg_queue.put(
                        (broadcast_msg, (msg.ip, msg.port))
                    )
            if isinstance(broadcast_msg, UserComeLeave):
                self.broadcast_online_users()

    def close(self):
        self.is_close = True
        self.udp_socket.close()

    def __del__(self):
        self.udp_socket.close()


def server(port=""):
    from littlechat.utils.util_log import set_scripts_logging

    set_scripts_logging(__file__, logger=logger, level=logging.DEBUG,
                        console_log=True, file_mode="a")
    Server(port=port).serve()


if __name__ == "__main__":
    server()
