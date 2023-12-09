import config
import logging

from mtools.base.handler import Dativer

log = logging.getLogger()


class XclubDativer(Dativer):

    auth_user = {
        '_name': 'auth_user',
        'id': 'int',
        'cate_code': {'type': 'str', 'relate': 'cate_role_bind.cate_code'},
    }

    cate_role_bind = {
        '_name': 'cate_role_bind',
        'id': 'int',
        'cate_code': 'str',
        'role_id': {'type': 'int', 'relate': 'role.id'},
    }

    role = {
        '_name': 'role',
        'id': 'int',
        'role_code': 'str',
        'role_name': 'str',
    }

    schemas = [auth_user, cate_role_bind, role]
