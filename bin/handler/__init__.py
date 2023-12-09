import logging

from mtools.micro.rpcore import RPCHandler

from handler import user
from handler import dativer

log = logging.getLogger()


class Handler(RPCHandler):
    def __init__(self, *args, **kw):
        super(Handler, self).__init__(*args, **kw)

        self.user = user.User(*args, **kw)
        self.dativer = dativer.UserDativer(*args, **kw)
