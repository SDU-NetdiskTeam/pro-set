# coding: utf-8

import logging
from configparser import ConfigParser
from seafevents.app.config import appconfig
from seafevents.utils.config import get_offline_download_conf

logger = logging.getLogger('offline_download')
logger.setLevel(logging.INFO)


class Settings(object):
    def __init__(self, config_file):
        self.enable_offline_download = False
        self.temp_dir = '/tmp/offline-download'
        self.max_workers = 10
        # default 10
        self.time_limit = 30 * 60
        # default 30 minutes

        self.session_cls = None
        self.seaf_session_cls = None

        self.parse_config(config_file)

    def parse_config(self, config_file):
        try:
            cfg = ConfigParser()
            events_conf = config_file
            cfg.read(events_conf)
        except Exception as e:
            logger.error('Failed to read events config, disable offline download: %s', e)
            return

        conf = get_offline_download_conf(cfg)
        if not conf['enabled']:
            return

        try:
            self.session_cls = appconfig.session_cls
            self.seaf_session_cls = appconfig.seaf_session_cls
        except Exception as e:
            logger.warning('Failed to init db session class: %s', e)
            return

        self.enable_offline_download = True
        self.temp_dir = conf['tempdir']
        self.max_workers = conf['workers']
        # default 10
        self.time_limit = conf['time-limit']

    def is_enabled(self):
        return self.enable_offline_download
