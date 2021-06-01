#coding: utf-8

import os
import tempfile
import subprocess
import traceback

from seaserv import seafile_api
from .db_oper import DBOper
from .models import OfflineDownloadStatus
from ..virus_scanner.thread_pool import ThreadPool
from .offline_download_settings import logger


class OfflineDownloadTask(object):
    def __init__(self, odr_id, repo_id, path, url, owner):
        self.odr_id = odr_id
        self.repo_id = repo_id
        self.path = path    # The path is actually the dir
        self.url = url
        self.owner = owner


class OfflineDownload(object):
    def __init__(self, settings):
        self.settings = settings
        self.db_oper = DBOper(settings)
        self.thread_pool = ThreadPool(self.download_file, self.settings.max_workers)
        self.thread_pool.start()

    def restore(self):
        # Check and restore all the interrupted tasks.
        task_list = self.db_oper.get_offline_download_tasks_by_status(OfflineDownloadStatus.DOWNLOADING)

        for row in task_list:
            self.thread_pool.put_task(OfflineDownloadTask(row.odr_id, row.repo_id, row.path, row.url, row.owner))

    def start(self):
        # Check and restore all the interrupted tasks.
        task_list = self.db_oper.get_offline_download_tasks_by_status(OfflineDownloadStatus.WAITING)

        for row in task_list:
            self.db_oper.set_record_status(row.odr_id, OfflineDownloadStatus.DOWNLOADING)
            self.thread_pool.put_task(OfflineDownloadTask(row.odr_id, row.repo_id, row.path, row.url, row.owner))

    def download_file(self, download_task: OfflineDownloadTask):
        tdir: str = ''
        try:
            tdir = tempfile.mkdtemp(dir=self.settings.temp_dir)
            logger.debug("Created temp dir '%s' for task '%d'", tdir, download_task.odr_id)

            log_dir = os.path.join(os.environ.get('SEAFEVENTS_LOG_DIR', ''))
            logfile = os.path.join(log_dir, 'offline_download.log')
            with open(logfile, 'a') as fp:
                logger.debug("Setting %s as log space.", logfile)
                logger.debug("Executing: aria2c --dir \"%s\" \"%s\"", tdir, download_task.url)
                subprocess.call(['aria2c', '--dir', tdir, download_task.url], stdout=fp, stderr=fp)

            file_list = os.listdir(tdir)
            if len(file_list) != 1:
                raise Exception('No file downloaded')
            else:
                tfile_path = os.path.join(tdir, file_list[0])
                if not os.path.exists(tfile_path):
                    raise Exception('File has lost')


            seafile_api.post_file(
                download_task.repo_id, tfile_path,
                download_task.path, file_list[0], download_task.owner
            )
            self.db_oper.set_record_file_size(download_task.odr_id, os.path.getsize(tfile_path))
            self.db_oper.set_record_status(download_task.odr_id, OfflineDownloadStatus.OK)

        except Exception as e:
            print(traceback.print_exc())
            logger.warning('Failed to do offline download for task %d: %s.',
                           download_task.odr_id, e)
            self.db_oper.set_record_status(download_task.odr_id, OfflineDownloadStatus.ERROR,
                                           "Download worker error: %s" % e)
        finally:
            if tdir is not None and len(tdir) > 0:
                file_list = os.listdir(tdir)
                for item in file_list:
                    os.unlink(os.path.join(tdir, item))
                os.rmdir(tdir)

