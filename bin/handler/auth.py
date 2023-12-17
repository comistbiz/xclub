import config
import logging

from mtools.base.handler import RPCHandler

from domain.user import ClubUser

log = logging.getLogger()


class Auth(RPCHandler):

    def login(self, code, userid):

        r = self.rcall(
            'ucus', 'auth.plat_third_login',
            {'login_code': code, 'org_userid': userid}
        )

        userid = r['userid']
        club_d = ClubUser()

        user = club_d.get(userid=userid)
        if not user:
            club_d.create(userid=userid)
            self.drive('update', {
                'namespace': 'ucus',
                'object': 'auth_user',
                'data': {'nickname': '游客'},
                'setting': {'by': {'id': userid}}
            })

        return r
