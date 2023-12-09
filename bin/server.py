import os
import sys

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(HOME, 'conf'))
import config

if config.WORK_MODE == 'gevent':
    from gevent import monkey

    monkey.patch_all()

from mtools.base import logger

log = logger.install(config.LOGFILE)
from mtools.micro import rpcore
import multiprocessing
from handler import Handler
from mtools.base import redispool

redispool.patch()

cores = multiprocessing.cpu_count()
log.info('cpu cores: %d', cores)
if config.MAX_PROC > cores * 2:
    log.warning('config.MAX_PROC(%d) > cpu cores(%d*2), please check', config.MAX_PROC, cores)


if config.WORK_MODE == 'gevent':
    server = rpcore.GeventServer(config, Handler)
else:
    server = rpcore.ThreadServer(config, Handler)
server.forever()

if __name__ == '__main__':
    pass
