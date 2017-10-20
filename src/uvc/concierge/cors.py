# -*- coding: utf-8 -*-


def cors_middleware(app, global_conf):
    def cors_filter(environ, start_response):
        return app(environ, start_response)
    return cipher_layer
