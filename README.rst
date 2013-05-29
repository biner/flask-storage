Flask-Storage
=============

Flask upload and storage extensions.


Confirgure
--------
    # local 配置
    app.config['UPLOADS_FOLDER'] = os.path.dirname(__file__)+'/static/'
    app.config['FILE_SYSTEM_STORAGE_FILE_VIEW'] = 'static'
    #app.config['UPLOADS_DEFAULT_URL'] = '/static/media'

    # sae 配置
    app.config['SAE_ACCESS_KEY_ID'] = "2y2j15w400"
    app.config['SAE_SECRET_ACCESS_KEY'] = "******"
    app.config['SAE_STORAGE_BUCKET_NAME'] = "base"
    app.config['SAE_S3_CUSTOM_DOMAIN'] = "pypet-base.stor.sinaapp.com"
    app.config['SAE_S3_SECURE_URLS'] = False

    # aliyun 配置
    app.config['ALIYUN_ACCESS_KEY_ID'] = "aowvikfoun3rx67073wlt825"
    app.config['ALIYUN_SECRET_ACCESS_KEY'] = "******"
    app.config['ALIYUN_STORAGE_BUCKET_NAME'] = "base22"
    app.config['ALIYUN_S3_CUSTOM_DOMAIN'] = "oss.aliyuncs.com"
    app.config['ALIYUN_S3_SECURE_URLS'] = False
    
    
    # sae
    if 'SERVER_SOFTWARE' in os.environ:
        app.config['DEFAULT_FILE_STORAGE'] = 'sae'
    else:
        app.config['DEFAULT_FILE_STORAGE'] = 'aliyun'
        
Tests
--------

    from flask.ext.storage import default_storage as get_storage

    storage = get_storage()
    rs = storage.save(name, content)
    
        
        
        
    
