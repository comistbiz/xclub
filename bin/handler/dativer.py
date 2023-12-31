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

    club_activity = {
        '_name': 'club_activity',
        'id': 'int',
        'title': 'str',
        'content': 'str',
        'activity_time':'str',
        'ctime': 'str',
        'utime': 'str'
    }

    club_activity_user = {
        '_name': 'club_activity_user',
        'id': 'int',
        'ctime': 'str',
        'utime': 'str',
        'activity_id': {'type': 'int', 'relate': 'club_activity.id'},
        'user_id': 'str'
    }


    schemas = [club_user, club_activity, club_activity_user]

    def map_data(self, data):

        data['role_name'] = ROLE_MAP.get(data['role']) or '游客'
        return data
