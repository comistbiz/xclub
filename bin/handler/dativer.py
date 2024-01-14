import json
import config
import logging

from mtools.base.handler import Dativer

from common.define import ROLE_MAP

log = logging.getLogger()


class XclubDativer(Dativer):

    club_user = {
        '_name': 'club_user',
        'id': 'int',
    }

    badge = {
        '_name': 'badge',
        'id': 'int',
    }

    user_badge = {
        '_name': 'user_badge',
        'badge_id': {'type': 'int', 'relate': 'badge.id'},
        'id': 'int',
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


    schemas = [club_user, club_activity, club_activity_user, badge, user_badge]

    def map_data(self, data):

        data['role_name'] = ROLE_MAP.get(data['role']) or '游客'
        return data

    def map_product(self, datas):

        pids = [i['product_id'] for i in datas]

        products = self.drive('query', {
            'namespace': 'mchnt',
            'object': 'product',
            'field': ['id', 'name', 'descr', 'image_url', 'descr'],
            'rule': {'id': pids},
        })

        id_pdt_map = {i['id']: i for i in products}

        for i in datas:
            product = id_pdt_map.get(i['id']) or {}
            if product:
                descr = json.loads(product['descr'])
                product.update(descr)
            i['product'] = product
        return datas
