# coding: utf-8

import logging
from configparser import ConfigParser
from seafevents.app.config import appconfig
from seafevents.utils.config import get_offline_download_conf

logger = logging.getLogger('offline_download')
logger.setLevel(logging.DEBUG)


class Settings(object):
    def __init__(self, config_file):
        self.enable_offline_download = False
        self.temp_dir = '/tmp/offline-download'
        self.max_workers = 10
        # default 10
        self.max_size = 500 * 1024 * 1024
        # default 500M

        self.session_cls = None
        self.seaf_session_cls = None

        self.parse_config(config_file)

    def parse_config(self, config_file):
        try:
            cfg = ConfigParser()
            seaf_conf = config_file
            cfg.read(seaf_conf)
        except Exception as e:
            logger.error('Failed to read seafile config, disable offline download: %s', e)
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
        # default 1
        self.max_size = conf['max-size']

    def is_enabled(self):
        return self.enable_offline_download
