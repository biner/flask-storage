# -*- coding: utf-8 -*-
from functools import wraps
import mimetypes


from flask import current_app
from flask.ext.storage.base import Storage, StorageException, StorageFile, reraise

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import oss.oss_api
import oss.oss_util
import oss.oss_fs

class AliyunStorage(Storage):
    
    def __init__(
            self,
            folder_name=None,
            access_key=None,
            secret_key=None,
            bucket_acl=None,
            acl=None,
            headers=None,
            gzip=None,
            gzip_content_types=None,
            querystring_auth=None,
            querystring_expire=None,
            reduced_redundancy=None,
            custom_domain=None,
            secure_urls=None,
            location=None,
            file_name_charset=None,
            preload_metadata=None,
            calling_format=None,
            file_overwrite=None,
            auto_create_bucket=None):

        access_key = access_key or \
            current_app.config.get('ALIYUN_ACCESS_KEY_ID', None)
        secret_key = secret_key or \
            current_app.config.get('ALIYUN_SECRET_ACCESS_KEY', None)
        # calling_format = calling_format or \
        #     current_app.config.get(
        #         'ALIYUN_S3_CALLING_FORMAT',
        #         SubdomainCallingFormat()
        #     )
        calling_format = None
        self.auto_create_bucket = auto_create_bucket or \
            current_app.config.get('ALIYUN_AUTO_CREATE_BUCKET', False)
        self.bucket_name = folder_name or \
            current_app.config.get('ALIYUN_STORAGE_BUCKET_NAME', None)
        self.acl = acl or \
            current_app.config.get('ALIYUN_DEFAULT_ACL', 'public-read')
        self.bucket_acl = bucket_acl or \
            current_app.config.get('ALIYUN_BUCKET_ACL', self.acl)
        self.file_overwrite = file_overwrite or \
            current_app.config.get('ALIYUN_S3_FILE_OVERWRITE', False)
        self.headers = headers or \
            current_app.config.get('ALIYUN_HEADERS', {})
        self.preload_metadata = preload_metadata or \
            current_app.config.get('ALIYUN_PRELOAD_METADATA', False)
        self.gzip = gzip or \
            current_app.config.get('ALIYUN_IS_GZIPPED', False)
        self.gzip_content_types = gzip_content_types or \
            current_app.config.get(
                'GZIP_CONTENT_TYPES', (
                    'text/css',
                    'application/javascript',
                    'application/x-javascript',
                )
            )
        self.querystring_auth = querystring_auth or \
            current_app.config.get('ALIYUN_QUERYSTRING_AUTH', True)
        self.querystring_expire = querystring_expire or \
            current_app.config.get('ALIYUN_QUERYSTRING_EXPIRE', 3600)
        self.reduced_redundancy = reduced_redundancy or \
            current_app.config.get('ALIYUN_REDUCED_REDUNDANCY', False)
        self.custom_domain = custom_domain or \
            current_app.config.get('ALIYUN_S3_CUSTOM_DOMAIN', None)
        self.secure_urls = secure_urls or \
            current_app.config.get('ALIYUN_S3_SECURE_URLS', True)
        self.location = location or current_app.config.get('ALIYUN_LOCATION', '')
        self.location = self.location.lstrip('/')
        self.file_name_charset = file_name_charset or \
            current_app.config.get('ALIYUN_S3_FILE_NAME_CHARSET', 'utf-8')

        # self.connection = sae.storage.Client(
        #     access_key, secret_key,
        #     calling_format=calling_format
        # )
        #self.connection = sae.storage.Client()
        self.connection = oss.oss_fs.OssFS(self.custom_domain,access_key,secret_key)
        self.client = oss.oss_api.OssAPI(self.custom_domain,access_key,secret_key)

        self._entries = {}

    @property
    def folder_name(self):
        return self.bucket_name

    @property
    def bucket(self):
        """
        Get the current bucket. If there is no current bucket object
        create it.
        """
        if not hasattr(self, '_bucket'):
            self._bucket = self._get_or_create_bucket(self.bucket_name)
        return self._bucket

    def _get_or_create_bucket(self, name):
        """Retrieves a bucket if it exists, otherwise creates it."""
        try:
            domain_list = self.connection.list_bucket()
            for bucket_name,bucket_date in domain_list:
                if bucket_name == name:
                    return name
            if name in domain_list:
                return name
            else:
                return self.connection.put_bucket(name,self.bucket_acl)
        except :
            raise
            if self.auto_create_bucket:
                bucket = self.connection.put_bucket(name,self.bucket_acl)
                return bucket
            raise RuntimeError(
                "Bucket specified by "
                "S3_BUCKET_NAME does not exist. "
                "Buckets can be automatically created by setting "
                "SAE_AUTO_CREATE_BUCKET=True")

    def _put_file(self, name, content):
        content_type = oss.oss_util.get_content_type_by_filename(name)
        input_content = content
        res = self.client.put_object_with_data(self.bucket, name, input_content,content_type)
        if (res.status / 100) == 2:
            print "put_object_from_string OK"
        else:
            print "put_object_from_string ERROR"
        

    def _read(self, name):
        memory_file = StringIO()
        try:
            memory_file = self.client.get_object(self.bucket, name).read()
        except:
            pass
        return memory_file

    def _open(self, name, mode='r'):
        return self.file_class(self, name=name, mode=mode)

    def _save(self, name, content): 
        name = self._encode_name(self._normalize_name(self._clean_name(name)))
        content_str = ''
        if isinstance(content, basestring):
            content_str = content
        else:
            if hasattr(content, 'chunks'):
                content_str = ''.join(chunk for chunk in content.chunks())
            else:
                content_str = content.read()
            #for fake tempfile
            if not content_str and hasattr(content, "file"):
                try:
                    content_str = content.file.getvalue()
                except:
                    pass
        self._put_file(name, content_str)
        return name

    def delete(self, name):
        name = self._normalize_name(self._clean_name(name))
        self.client.delete(self.bucket, name)

    def exists(self, name):
        name = self._normalize_name(self._clean_name(name))
        try:
            attr = self.get_object_attr(name)
            print attr
            o = self.client.head_object(self.bucket, name).status
            if o == 200:
                return True
        except:
            pass
        return False

    def listdir(self):
        files = self.client.list_objects(self.bucket)
        return files
        
    def size(self, name):
        try:
            stat = self.client.head_object(self.bucket, name)
        except:
            return 0
        return stat.length

    def url(self, name):
        name = self._encode_name(self._normalize_name(self._clean_name(name)))

        url = self.client.sign_url("GET",self.bucket, name,60)
        url = url.split("?")
        return str(url[0])

    @property
    def file_class(self):
        return AliyunStorageFile

    def get_object(self, name):
        name = self._normalize_name(self._clean_name(name))
        try:
            ob = self.connection.read_file(self.bucket, name)
            return ob
        except Exception, e:
            pass
        return None

    def get_object_attr(self, name):
        attr = {}
        name = self._normalize_name(self._clean_name(name))
        try:
            res = self.client.head_object(self.bucket, name)
            for key,value in res.getheaders():
                attr[key] = value
        except Exception, e:
            pass
        return attr
            
        
    def isdir(self, name):
        return False if name else True

    def isfile(self, name):
        return self.exists(name) if name else False
        
    def modified_time(self, name):
        from datetime import datetime
        return datetime.now()
        
    def path(self,name):
        return name
        
class AliyunStorageFile(StorageFile):
    _attr = None
    _file = None
    """docstring for SaeStorageFile"""
    def __init__(self, storage, name, mode):
        self._name = name
        self._storage = storage
        self._mode = mode
        self._is_dirty = False
        self._is_read = False

    @property
    def size(self):
        if not hasattr(self, '_size'):
            self._size = self.attr['content-length']
        return self._size

    @property
    def last_modified(self):
        if not hasattr(self, '_last_modified'):
            self._last_modified = self.attr['date']
        return self._last_modified

    @property
    def file(self):
        if not self._file:
            data = self._storage.get_object(self.name)
            self._file = StringIO(data)
        return self._file

    @property
    def attr(self):
        if not self._attr:
            self._attr = self._storage.get_object_attr(self.name)
        return self._attr

    @property
    def content_type(self):
        if not hasattr(self, '_contenttype'):
            self._contenttype = self.attr['content-type']
        return self._contenttype

    def read(self, size=-1):
        return self.file.read(size)
            
    def write(self, content):
        if 'w' not in self._mode:
            raise AttributeError("File was opened for read-only access.")

        saefile = self._storage.save(self._name,content)
        self._file = saefile.file
        self._is_read = True

    def close(self):
        if self._is_dirty:
            self._storage._put_file(self._name, self.file.getvalue())
        self.file.close()