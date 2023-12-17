import logging
from datetime import datetime, timedelta
from mtools.base.handler import RPCHandler
from mtools.utils.tools import datetime_to_str, future, to_datetime
from mtools.resp.excepts import ParamError

from domain.user import ClubUser

log = logging.getLogger()


class User(RPCHandler):

    def info(self, userid):

        # 查询其他服务
        auth_data = self.drive('query', {
            'namespace': 'ucus',
            'object': 'auth_user',
            'field': ['id', 'username'],
            'rule': {'userid': userid}
        })

        club_data = ClubUser().get(userid=userid)

        club_data.update(auth_data)
        return club_data

    def edit(self, userid, **kw):

        if 'role' in kw:
            role = kw.pop('role')
            ClubUser().update(
                by={'userid': userid},
                role=role,
            )

        if kw:
            # 更新基础字段
            self.drive('update', {
                'namespace': 'ucus',
                'object': 'auth_user',
                'data': kw,
                'setting': {'by': {'userid': userid}}
            })

    def open_card(self, userid, card_id):

        user_card = self.drive('query', {
            'namespace': 'member',
            'object': 'user_card',
            'rule': {
                'userid': userid, 'card_id': card_id,
                'ge.end_time': datetime_to_str(),
            },
            'setting': {'one': True}
        })

        card = self.drive('query', {
            'namespace': 'member',
            'object': 'member_card',
            'rule': {
                'card_id': card_id,
            },
        })

        # 有生效的卡 则延长时间
        if user_card:
            end_time = to_datetime(user_card['end_time'])
            if card['unit'] == 'month':
                end_time = future(end_time, months=card['period'])
            self.drive('update', {
                'namespace': 'memeber',
                'object': 'user_card',
                'data': {
                    'userid': userid,
                    'card_id': card_id,
                    'end_time': end_time,
                },
                'setting': {'by': {
                    'id': user_card['id'],
                }}
            })
        # 没有有生效的卡，新建一张
        else:
            start_time = datetime.now()
            if card['unit'] == 'month':
                end_time = future(start_time, months=card['period'])

            self.drive('create', {
                'namespace': 'memeber',
                'object': 'user_card',
                'data': {
                    'userid': userid,
                    'card_id': card_id,
                    'start_time': start_time,
                    'end_time': end_time,
                },
            })
