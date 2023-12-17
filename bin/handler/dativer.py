import config
import logging

from mtools.base.handler import Dativer

log = logging.getLogger()


class XclubDativer(Dativer):

    club_user = {
        '_name': 'club_user',
        'id': 'int',
        'cate_code': {'type': 'str', 'relate': 'cate_role_bind.cate_code'},
    }


    schemas = [club_user]
