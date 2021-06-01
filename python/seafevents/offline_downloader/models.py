from sqlalchemy import Column, Integer, String, Text, SmallInteger, DateTime, BigInteger

from seafevents.db import Base


class OfflineDownloadRecord(Base):
    __tablename__ = 'OfflineDownloadRecord'

    odr_id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String(length=36), nullable=False)
    path = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    owner = Column(String(length=255), nullable=False)
    timestamp = Column(DateTime(), nullable=False)
    size = Column(BigInteger, nullable=False, default=0)
    status = Column(SmallInteger, nullable=False, comment='0=Unknown, 1=Waiting, 2=Downloading, 3=OK, 4=Error')
    comment = Column(Text, nullable=False)
    __table_args__ = {'extend_existing':True}

    def __init__(self, repo_id, path, url, owner, timestamp, status, comment):
        self.repo_id = repo_id
        self.path = path    # The path is actually the dir, not a concrete file.
        self.url = url
        self.owner = owner
        self.timestamp = timestamp
        self.status = status
        self.comment = comment


class OfflineDownloadStatus(object):
    UNKNOWN = 0
    WAITING = 1
    DOWNLOADING = 2
    OK = 3
    ERROR = 4
