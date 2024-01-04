import config
import logging

from mtools.base.handler import Dativer

from common.define import ROLE_MAP

log = logging.getLogger()


class XclubDativer(Dativer):

    club_user = {
        '_name': 'club_user',
        'id': 'int',
        'cate_code': {'type': 'str', 'relate': 'cate_role_bind.cate_code'},
    }

    schemas = [club_user]

    def map_data(self, data):

        data['role_name'] = ROLE_MAP.get(data['role']) or '游客'
        return data
