class MsgTooLong(Exception):

    def __init__(self, msg_length, allow_length=65535):
        super().__init__(f"Msg is too long, length: {msg_length}, "
                         f"allow_length: {allow_length}")
