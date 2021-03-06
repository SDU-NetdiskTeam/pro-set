import os
import logging

from sqlalchemy.ext.declarative import declarative_base

from seafevents.app.config import appconfig, load_config
from seafevents.app.mq_handler import EventsHandler
from seafevents.events_publisher.events_publisher import events_publisher
from seafevents.utils.config import get_office_converter_conf
from seafevents.utils import has_office_tools, get_config, has_offline_download_tools
from seafevents.tasks import IndexUpdater, SeahubEmailSender, LdapSyncer,\
        VirusScanner, Statistics, CountUserActivity, CountTrafficInfo, ContentScanner,\
        WorkWinxinNoticeSender, FileUpdatesSender, RepoOldFileAutoDelScanner, OfflineDownloader

if has_office_tools():
    from seafevents.office_converter import OfficeConverter

Base = declarative_base()


class App(object):
    def __init__(self, args, events_handler_enabled=True, background_tasks_enabled=True):
        self._central_config_dir = os.environ.get('SEAFILE_CENTRAL_CONF_DIR')
        self._args = args
        self._events_handler_enabled = events_handler_enabled
        self._bg_tasks_enabled = background_tasks_enabled
        try:
            load_config(args.config_file)
        except Exception as e:
            logging.error('Error loading seafevents config. Detail: %s' % e)
            raise RuntimeError("Error loading seafevents config. Detail: %s" % e)

        self._events_handler = None
        if self._events_handler_enabled:
            self._events_handler = EventsHandler(self._args.config_file)

        if appconfig.publish_enabled:
            events_publisher.init()
        else:
            logging.info("Events publish to redis is disabled.")

        self._bg_tasks = None
        if self._bg_tasks_enabled:
            self._bg_tasks = BackgroundTasks(args.config_file)

        if appconfig.enable_statistics:
            self.update_login_record_task = CountUserActivity()
            self.count_traffic_task = CountTrafficInfo()

    def serve_forever(self):
        if self._events_handler:
            self._events_handler.start()
        else:
            logging.info("Event listener is disabled.")

        if self._bg_tasks:
            self._bg_tasks.start()
        else:
            logging.info("Background task is disabled.")

        if appconfig.enable_statistics:
            self.update_login_record_task.start()
            self.count_traffic_task.start()
        else:
            logging.info("User login statistics is disabled.")
            logging.info("Traffic statistics is disabled.")


class BackgroundTasks(object):

    def __init__(self, config_file):

        self._app_config = get_config(config_file)

        self._index_updater = IndexUpdater(self._app_config)
        self._seahub_email_sender = SeahubEmailSender(self._app_config)
        self._ldap_syncer = LdapSyncer()
        self._virus_scanner = VirusScanner(config_file)
        self._statistics = Statistics()
        self._content_scanner = ContentScanner(config_file)
        self._work_weixin_notice_sender = WorkWinxinNoticeSender(self._app_config)
        self._file_updates_sender = FileUpdatesSender()
        self._repo_old_file_auto_del_scanner = RepoOldFileAutoDelScanner(config_file)

        self._office_converter = None
        if has_office_tools():
            self._office_converter = OfficeConverter(get_office_converter_conf(self._app_config))

        self._offline_downloader = None
        if has_offline_download_tools():
            self._offline_downloader = OfflineDownloader(config_file)

    def start(self):
        logging.info('Starting background tasks.')

        self._file_updates_sender.start()

        if self._work_weixin_notice_sender.is_enabled():
            self._work_weixin_notice_sender.start()
        else:
            logging.info('work weixin notice sender is disabled')

        if self._index_updater.is_enabled():
            self._index_updater.start()
        else:
            logging.info('search indexer is disabled')

        if self._seahub_email_sender.is_enabled():
            self._seahub_email_sender.start()
        else:
            logging.info('seahub email sender is disabled')

        if self._ldap_syncer.enable_sync():
            self._ldap_syncer.start()
        else:
            logging.info('ldap sync is disabled')

        if self._virus_scanner.is_enabled():
            self._virus_scanner.start()
        else:
            logging.info('virus scan is disabled')

        if self._statistics.is_enabled():
            self._statistics.start()
        else:
            logging.info('data statistics is disabled')

        if self._content_scanner.is_enabled():
            self._content_scanner.start()
        else:
            logging.info('content scan is disabled')

        if self._office_converter and self._office_converter.is_enabled():
            self._office_converter.start()
        else:
            logging.info('office converter is disabled')

        if self._repo_old_file_auto_del_scanner.is_enabled():
            self._repo_old_file_auto_del_scanner.start()
        else:
            logging.info('repo old file auto del scanner disabled')

        if self._offline_downloader.is_enabled():
            self._offline_downloader.start()
        else:
            logging.info('offline downloader disabled')
