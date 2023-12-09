import logging

from mtools.micro.rpcore import RPCHandler

from handler import dativer

log = logging.getLogger()


class Handler(RPCHandler):
    def __init__(self, *args, **kw):
        super(Handler, self).__init__(*args, **kw)

        self.dativer = dativer.XclubDativer(*args, **kw)
