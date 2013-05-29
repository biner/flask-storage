try:
    from .amazon import S3BotoStorage, S3BotoStorageFile
except Exception, e:
    from .filesystem import FileSystemStorage as S3BotoStorage
    from .filesystem import FileSystemStorageFile as S3BotoStorageFile
    

from .sina import SaeStorage, SaeStorageFile
from .aliyun import AliyunStorage, AliyunStorageFile
from .cloudfiles import CloudFilesStorage, CloudFilesStorageFile
from .filesystem import FileSystemStorage, FileSystemStorageFile
from .mock import MockStorage, MockStorageFile
from .base import (
    FileExistsError,
    FileNotFoundError,
    PermissionError,
    Storage,
    StorageException,
    StorageFile
)


__all__ = (
    CloudFilesStorage,
    CloudFilesStorageFile,
    FileExistsError,
    FileNotFoundError,
    FileSystemStorage,
    FileSystemStorageFile,
    MockStorage,
    MockStorageFile,
    PermissionError,
    S3BotoStorage,
    S3BotoStorageFile,
    SaeStorage,
    SaeStorageFile,
    AliyunStorage,
    AliyunStorageFile,
    Storage,
    StorageException,
    StorageFile,
    'STORAGE_DRIVERS',
    'get_default_storage_class',
    'get_filesystem_storage_class',
)


STORAGE_DRIVERS = {
    'amazon': S3BotoStorage,
    'sae': SaeStorage,
    'aliyun': AliyunStorage,
    'cloudfiles': CloudFilesStorage,
    'filesystem': FileSystemStorage,
    'mock': MockStorage
}


def get_default_storage_class(app):
    return STORAGE_DRIVERS[app.config['DEFAULT_FILE_STORAGE']]


def get_filesystem_storage_class(app):
    if app.config['TESTING']:
        return MockStorage
    else:
        return FileSystemStorage
