from functools import wraps
import mimetypes


from flask import current_app
from flask.ext.storage.base import Storage, StorageException, StorageFile, reraise

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    import sae.storage
    from sae.storage import DomainNotExistsError,ObjectNotExistsError,PermissionDeniedError
except Exception, e:
    pass



class SaeStorage(Storage):
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
            current_app.config.get('SAE_ACCESS_KEY_ID', None)
        secret_key = secret_key or \
            current_app.config.get('SAE_SECRET_ACCESS_KEY', None)
        # calling_format = calling_format or \
        #     current_app.config.get(
        #         'SAE_S3_CALLING_FORMAT',
        #         SubdomainCallingFormat()
        #     )
        calling_format = None
        self.auto_create_bucket = auto_create_bucket or \
            current_app.config.get('SAE_AUTO_CREATE_BUCKET', False)
        self.bucket_name = folder_name or \
            current_app.config.get('SAE_STORAGE_BUCKET_NAME', None)
        self.acl = acl or \
            current_app.config.get('SAE_DEFAULT_ACL', 'public-read')
        self.bucket_acl = bucket_acl or \
            current_app.config.get('SAE_BUCKET_ACL', self.acl)
        self.file_overwrite = file_overwrite or \
            current_app.config.get('SAE_S3_FILE_OVERWRITE', False)
        self.headers = headers or \
            current_app.config.get('SAE_HEADERS', {})
        self.preload_metadata = preload_metadata or \
            current_app.config.get('SAE_PRELOAD_METADATA', False)
        self.gzip = gzip or \
            current_app.config.get('SAE_IS_GZIPPED', False)
        self.gzip_content_types = gzip_content_types or \
            current_app.config.get(
                'GZIP_CONTENT_TYPES', (
                    'text/css',
                    'application/javascript',
                    'application/x-javascript',
                )
            )
        self.querystring_auth = querystring_auth or \
            current_app.config.get('SAE_QUERYSTRING_AUTH', True)
        self.querystring_expire = querystring_expire or \
            current_app.config.get('SAE_QUERYSTRING_EXPIRE', 3600)
        self.reduced_redundancy = reduced_redundancy or \
            current_app.config.get('SAE_REDUCED_REDUNDANCY', False)
        self.custom_domain = custom_domain or \
            current_app.config.get('SAE_S3_CUSTOM_DOMAIN', None)
        self.secure_urls = secure_urls or \
            current_app.config.get('SAE_S3_SECURE_URLS', True)
        self.location = location or current_app.config.get('SAE_LOCATION', '')
        self.location = self.location.lstrip('/')
        self.file_name_charset = file_name_charset or \
            current_app.config.get('SAE_S3_FILE_NAME_CHARSET', 'utf-8')

        # self.connection = sae.storage.Client(
        #     access_key, secret_key,
        #     calling_format=calling_format
        # )
        self.connection = sae.storage.Client()

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

    def list_folders(self):
        return [bucket.name for bucket in self.connection.get_all_buckets()]

    @property
    def folder(self):
        return self.bucket

    def list_files(self):
        return [
            self.file_class(self, key.name) for key in self.bucket.list()
        ]

    def create_folder(self, name=None):
        if not name:
            name = self.folder_name
        try:
            bucket = self.connection.create_bucket(name)
            bucket.set_acl(self.bucket_acl)
        except S3CreateError, e:
            reraise(e)
        return bucket

    def _get_or_create_bucket(self, name):
        """Retrieves a bucket if it exists, otherwise creates it."""
        try:
            domain_list = self.connection.list_domain()
            if name in domain_list:
            	return name
            else:
                raise DomainNotExistsError()
                return self.connection.get_bucket(
                    name,
                    validate=self.auto_create_bucket
                )
        except S3ResponseError:
            if self.auto_create_bucket:
                bucket = self.connection.create_bucket(name)
                bucket.set_acl(self.bucket_acl)
                return bucket
            raise RuntimeError(
                "Bucket specified by "
                "S3_BUCKET_NAME does not exist. "
                "Buckets can be automatically created by setting "
                "SAE_AUTO_CREATE_BUCKET=True")

    def _save(self, name, content):
        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)
        headers = self.headers.copy()
        name = cleaned_name
        content_type = mimetypes.guess_type(name)[0] or Key.DefaultContentType
        encoded_name = self._encode_name(name)

        # key = self.bucket.new_key(encoded_name)
        # if self.preload_metadata:
        #     self._entries[encoded_name] = key

        # key.set_metadata('Content-Type', content_type)
        # if isinstance(content, basestring):
        #     key.set_contents_from_string(
        #         content,
        #         headers=headers,
        #         policy=self.acl,
        #         reduced_redundancy=self.reduced_redundancy
        #     )
        # else:
        #     content.name = cleaned_name
        #     key.set_contents_from_file(
        #         content,
        #         headers=headers,
        #         policy=self.acl,
        #         reduced_redundancy=self.reduced_redundancy
        #     )
        # return self.open(encoded_name)
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
        self._put_file(encoded_name, content_str)
        return self.open(encoded_name)


    def _put_file(self, name, content):
        ob = sae.storage.Object(content)
        self.connection.put(self.bucket, name, ob)

    def _open(self, name, mode='r'):
        return self.file_class(self, name=name, mode=mode)

    def delete_folder(self, name=None):
        if name is None:
            name = self.folder_name
        self.bucket.delete()

    def delete(self, name):
        name = self._encode_name(self._normalize_name(self._clean_name(name)))
        if self.exists(name):
            return self.connection.delete(self.bucket,name)
        return False
        if self.bucket.lookup(name) is None:
            raise StorageException('%s already exists' % name, 404)

        self.bucket.delete_key(name)

    def exists(self, name):
        name = self._normalize_name(self._clean_name(name))
        try:
            stat = self.connection.stat(self.bucket, name)
        except Exception, e:
            return False
        return True

        return bool(self.bucket.lookup(self._encode_name(name)))

    def url(self, name):
        name = self._normalize_name(self._clean_name(name))

        if self.custom_domain:
            return "%s://%s/%s" % ('https' if self.secure_urls else 'http',
                                   self.custom_domain, name)
        
        return self.connection.url(self.bucket, name)
        return self.connection.generate_url(
            self.querystring_expire,
            method='GET',
            bucket=self.bucket.name,
            key=self._encode_name(name),
            query_auth=self.querystring_auth,
            force_http=not self.secure_urls
        )

    @property
    def file_class(self):
        return SaeStorageFile

    def get_object(self, name):
        name = self._normalize_name(self._clean_name(name))
        try:
            ob = self.connection.get(self.bucket, name)
            return ob
        except sae.storage.ObjectNotExistsError, e:
            reraise(e)
        except Exception, e:
            reraise(e)

    def get_object_attr(self, name):
        name = self._normalize_name(self._clean_name(name))

        stat = self.connection.stat(self.bucket, name)
        return stat

    def _read(self, name):
        memory_file = StringIO()
        try:
            o = self.get_object(name)
            memory_file.write(o.data)
        except sae.storage.ObjectNotExistsError, e:
            pass
        return memory_file

def require_opening(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._is_open:
            self._key.open(self._mode)
            self._is_open = True
        return func(self, *args, **kwargs)
    return wrapper

class SaeStorageFile(StorageFile):
    _saeobject = None
    _saeattr = None
    _file = None
    """docstring for SaeStorageFile"""
    def __init__(self, storage, name, mode):
        self._name = name
        self._storage = storage
        self._mode = mode
        self._is_dirty = False
        self._is_read = False

    @property
    def saeobject(self):
        if not self._saeobject:
            self._saeobject = self._storage.get_object(self.name)
        return self._saeobject

    @property
    def size(self):
        if not hasattr(self, '_size'):
            self._size = self.attr['length']
        return self._size

    @property
    def last_modified(self):
        if not hasattr(self, '_last_modified'):
            self._last_modified = self.attr['datetime']
        return self._last_modified

    @property
    def file(self):
        if not self._file:
            self._file = StringIO(self.saeobject.data)
        return self._file

    @property
    def attr(self):
        if not self._saeattr:
            self._saeattr = self._storage.get_object_attr(self.name)
        return self._saeattr

    @property
    def content_type(self):
        return getattr(
            self.file,
            'content_type',
            mimetypes.guess_type(self.name)[0]
        )

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