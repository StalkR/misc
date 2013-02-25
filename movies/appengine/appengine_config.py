def webapp_add_wsgi_middleware(app):
    # https://developers.google.com/appengine/docs/python/tools/appstats
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
