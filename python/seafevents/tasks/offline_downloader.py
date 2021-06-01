# coding: utf-8

import logging
from threading import Thread, Event

from seafevents.offline_downloader import OfflineDownload
from seafevents.offline_downloader import Settings


class OfflineDownloader(object):
    def __init__(self, config_file):
        self.settings = Settings(config_file)
        self.downloader = OfflineDownload(self.settings)

    def is_enabled(self):
        return self.settings.is_enabled()

    def start(self):
        logging.info("Start offline downloader, refresh interval = 5 sec")
        logging.info("Restoring interrupted download tasks...")
        self.downloader.restore()
        OfflineDownloadTimer(self.downloader, self.settings).start()


class OfflineDownloadTimer(Thread):
    def __init__(self, downloader, settings):
        Thread.__init__(self)
        self.settings = settings
        self.finished = Event()
        self.downloader = downloader

    def run(self):
        while not self.finished.is_set():
            self.finished.wait(5)
            if not self.finished.is_set():
                self.downloader.start()

    def cancel(self):
        self.finished.set()
