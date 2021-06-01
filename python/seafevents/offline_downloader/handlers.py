# coding: utf-8
import logging
import logging.handlers

# from seafevents.app.config import appconfig
from .db_oper import add_offline_download_record


def OfflineDownloadEventHandler(session, msg):
    elements = msg['content'].split('\t')
    if len(elements) != 5:
        logging.warning("got bad message: %s", elements)
        logging.debug("Expected 4 arguments, found %d.", len(elements))
        return
    repo_id = elements[1]
    path = elements[2]
    user_name = elements[3]
    url = elements[4]

    # add_offline_download_record(appconfig.session_cls(), repo_id, path, user_name)
    add_offline_download_record(session, repo_id, path, user_name, url)


def register_handlers(handlers):
    handlers.add_handler('seahub.stats:offline-file-upload', OfflineDownloadEventHandler)
