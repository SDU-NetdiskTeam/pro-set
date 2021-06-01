# coding: utf-8
import time

from sqlalchemy import desc
from sqlalchemy.orm import Session, Query

from .models import OfflineDownloadRecord, OfflineDownloadStatus
from .offline_download_settings import logger


class DBOper(object):
    def __init__(self, settings):
        self.edb_session = settings.session_cls
        self.seafdb_session = settings.seaf_session_cls

    def set_record_status(self, odr_id, status, comment=None):
        session: Session = self.edb_session()
        try:
            q = session.query(OfflineDownloadRecord).filter(OfflineDownloadRecord.odr_id == odr_id)
            r = q.first()
            if not r:
                logger.error('No offline download record: %d.', odr_id)
                return
            else:
                r.status = status
                if comment is not None:
                    r.comment = comment
                session.commit()
        except Exception as e:
            logger.warning('Failed to update offline download status from db: %s.', e)
        finally:
            session.close()

    def set_record_comment(self, odr_id, comment):
        session: Session = self.edb_session()
        try:
            q = session.query(OfflineDownloadRecord).filter(OfflineDownloadRecord.odr_id == odr_id)
            r = q.first()
            if not r:
                logger.error('No offline download record: %d.', odr_id)
                return
            else:
                r.comment = comment
                session.commit()
        except Exception as e:
            logger.warning('Failed to update offline download comment from db: %s.', e)
        finally:
            session.close()

    def get_offline_download_tasks_by_status(self, status=OfflineDownloadStatus.WAITING):
        session: Session = self.edb_session()
        try:
            q: Query = session.query(OfflineDownloadRecord).filter(OfflineDownloadRecord.status == status)
            return q.all()
        except Exception as e:
            logger.warning('Failed to get offline download tasks (%d) from db: %s.', status, e)
            return None

    def set_record_file_size(self, odr_id, size):
        session: Session = self.edb_session()
        try:
            q = session.query(OfflineDownloadRecord).filter(OfflineDownloadRecord.odr_id == odr_id)
            r = q.first()
            if not r:
                logger.error('No offline download record: %d.', odr_id)
                return
            else:
                r.size = size
                session.commit()
        except Exception as e:
            logger.warning('Failed to update offline download file size from db: %s.', e)
        finally:
            session.close()


# Returns the added record id.
def add_offline_download_record(session: Session, repo_id, path, owner, url):
    try:
        od_record = OfflineDownloadRecord(repo_id, path, url, owner, time.time(), OfflineDownloadStatus.WAITING, '')
        session.add(od_record)
        session.commit()
        return od_record.odr_id
    except Exception as e:
        logger.error(e)
        return -1
    finally:
        session.close()


def get_offline_download_tasks_by_user(session: Session, user, start, limit):
    if start < 0:
        logger.error('start must be non-negative')
        raise RuntimeError('start must be non-negative')

    if limit <= 0:
        logger.error('limit must be positive')
        raise RuntimeError('limit must be positive')

    try:
        q: Query = session.query(OfflineDownloadRecord).filter(OfflineDownloadRecord.owner == user)
        q = q.order_by(desc(OfflineDownloadRecord.odr_id))
        q = q.slice(start, start+limit)
        return q.all()
    except Exception as e:
        logger.warning('Failed to get offline download tasks from db: %s.', e)
        return None


def get_record_status(session: Session, odr_id):
    try:
        q: Query = session.query(OfflineDownloadRecord).filter(OfflineDownloadRecord.odr_id == odr_id)
        r = q.first()
        if not r:
            logger.error('No offline download record: %d.', odr_id)
            return -1
        else:
            return r.status
    except Exception as e:
        logger.warning('Failed to get offline download status from db: %s.', e)
    finally:
        session.close()


def get_record_comment(session: Session, odr_id):
    try:
        q: Query = session.query(OfflineDownloadRecord).filter(OfflineDownloadRecord.odr_id == odr_id)
        r = q.first()
        if not r:
            logger.error('No offline download record: %d.', odr_id)
            return -1
        else:
            return r.comment
    except Exception as e:
        logger.warning('Failed to get offline download comment from db: %s.', e)
    finally:
        session.close()


def get_record_file_size(session: Session, odr_id):
    try:
        q: Query = session.query(OfflineDownloadRecord).filter(OfflineDownloadRecord.odr_id == odr_id)
        r = q.first()
        if not r:
            logger.error('No offline download record: %d.', odr_id)
            return -1
        else:
            return r.size
    except Exception as e:
        logger.warning('Failed to get offline download file size from db: %s.', e)
    finally:
        session.close()
