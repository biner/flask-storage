try:
    from .amazon import S3BotoStorage, S3BotoStorageFile
except Exception, e:
    from .filesystem import FileSystemStorage as S3BotoStorage
    from .filesystem import FileSystemStorageFile as S3BotoStorageFile
    
from flask import current_app
from .sina import SaeStorage, SaeStorageFile
from .aliyun import AliyunStorage, AliyunStorageFile
from .cloudfiles import CloudFilesStorage, CloudFilesStorageFile
from .filesystem import FileSystemStorage, FileSystemStorageFile
from .mock import MockStorage, MockStorageFile
from .base import (
    FileExistsError,
    FileNotFoundError,
    PermissionError,
    #Storage,
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
    #Storage,
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


def get_default_storage_class():
    default = current_app.config.get('DEFAULT_FILE_STORAGE', 'filesystem')
    return STORAGE_DRIVERS[default]


def get_filesystem_storage_class():
    testing = current_app.config.get('DEFAULT_FILE_STORAGE', 'filesystem')
    if testing:
        return MockStorage
    else:
        return FileSystemStorage

# init the default storage
def default_storage():
    if not hasattr(current_app, 'extensions'):
        current_app.extensions = {}
    current_app.extensions.setdefault('storage', None)
    if not current_app.extensions['storage']:
        default_class = get_default_storage_class()
        s= default_class()
        current_app.extensions['storage'] = s
    return current_app.extensions['storage']