import logging
import time
from typing import *
from abc import ABC, abstractmethod

from datetime import datetime
from copy import deepcopy
from threading import Lock

logger = logging.getLogger("server")


class MsgBox(object):

    def __init__(self, username=None, msg=""):
        self.username = username
        self.ip = ""
        self.port = ""
        self.msg = msg
        self.is_self = False
        self.msg_time = datetime.now()
        self.user_heartbeat_time = time.time()

    def get_msg_str(self, times=True):
        if times:
            return (f"{self.msg_time.strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"[{self.username}]: {self.msg}")
        return f"[{self.username}]: {self.msg}"

    def get_msg_time_str(self, time_format="%Y-%m-%d %H:%M") -> str:
        return self.msg_time.strftime(time_format)

    def fill_addr(self, ip, port):
        self.ip = ip
        self.port = port

    def check_valid(self):
        if not self.username:
            return False

        return True


class ServerMsg(MsgBox):
    def __init__(self, msg):
        super().__init__(username="server", msg=msg)


class ExceptionMsg(ServerMsg):
    pass


class DuplicatUser(ExceptionMsg):
    def __init__(self):
        super().__init__(msg="DuplicatUser")


class UserDict(ServerMsg):

    def __init__(self, user_dict):
        super().__init__(msg=f"Online users: {list(user_dict.keys())}")
        self.user_dict = user_dict


class TimeStamp(ServerMsg):
    def __init__(self, time_str):
        super().__init__(msg=time_str)


class UserComeLeave(ServerMsg):
    pass


class UserOnlineServer(UserComeLeave):
    def __init__(self, online_username):
        super().__init__(msg=f"`{online_username}` is online")


class UserOfflineServer(UserComeLeave):
    def __init__(self, exit_username):
        super().__init__(msg=f"`{exit_username}` is offline")


class ClientMsg(MsgBox):

    def get_copy(self):
        return deepcopy(self)

    @abstractmethod
    def get_response_msg(self):
        pass

    @abstractmethod
    def get_broadcast_msg(self):
        pass


class UserHeartbeat(ClientMsg):

    def get_response_msg(self):
        pass

    def get_broadcast_msg(self):
        pass

    def __init__(self, username):
        super().__init__(username=username, msg="heartbeat")


class ConCheck(ClientMsg):
    def __init__(self):
        super().__init__(username="conCheck", msg="conCheck")

    def get_response_msg(self):
        return self

    def get_broadcast_msg(self):
        pass


class NewUser(ClientMsg):
    EXPIRE_SECONDS = 3

    USER_DICT: Dict[str, ClientMsg] = {

    }

    _USER_DICT_UPDATE_LOCK = Lock()

    def __init__(self, username):
        super().__init__(username=username, msg="new_user")
        self.is_new = True

    @classmethod
    def update_user_heartbeat_time(cls, uhb: UserHeartbeat):
        username = uhb.username
        with cls._USER_DICT_UPDATE_LOCK:
            if username in NewUser.USER_DICT:
                NewUser.USER_DICT[username].user_heartbeat_time = time.time()
            else:
                new_user = NewUser(username)
                new_user.ip, new_user.port = uhb.ip, uhb.port
                NewUser.USER_DICT[username] = new_user
                logger.info(f"user {username} is back online !!")

    @classmethod
    def check_and_clear_expired_users(cls):
        with cls._USER_DICT_UPDATE_LOCK:
            expired_users = []
            for username, user in NewUser.USER_DICT.items():
                user_hb_time = NewUser.USER_DICT[username].user_heartbeat_time
                if time.time() - user_hb_time > cls.EXPIRE_SECONDS:
                    expired_users.append(user)
            for user in expired_users:
                NewUser.USER_DICT.pop(user.username)

        return expired_users

    @classmethod
    def remove_expired_user(cls, username):
        with cls._USER_DICT_UPDATE_LOCK:
            try:
                cls.USER_DICT.pop(username)
            except KeyError:
                pass

    @classmethod
    def load_new_user(cls, msg: ClientMsg):
        if msg.username not in cls.USER_DICT:
            cls.USER_DICT[msg.username] = msg
            cls.USER_DICT[msg.username] = msg
            logger.info(f"user {msg.username} is online")

    def is_user_exist(self):
        return self.username in NewUser.USER_DICT

    def get_response_msg(self):
        if self.is_user_exist():
            self.is_new = False
            return DuplicatUser()

        self.load_new_user(self)
        msg = self.get_copy()
        msg.msg = f"Welcome, {msg.username}"
        return msg

    def get_broadcast_msg(self, rsp_msg=None):
        if not self.is_new:
            return None
        return UserOnlineServer(self.username)


class UserOffline(ClientMsg):

    def get_response_msg(self):
        pass

    def get_broadcast_msg(self):
        NewUser.remove_expired_user(self.username)
        return UserOfflineServer(self.username)

    def __init__(self, username):
        super().__init__(username=username, msg="user exit")


class UserMsg(ClientMsg):

    def __init__(self, username, msg):
        super().__init__(username=username, msg=msg)

    def get_response_msg(self):
        pass

    def get_broadcast_msg(self):
        msg = self.get_copy()
        return msg
