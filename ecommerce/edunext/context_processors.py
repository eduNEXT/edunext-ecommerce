#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains django context_processors needed by edunext.
"""
import json


def theme_options(request):
    """
    This context processor lets us add extra context to the themable templates
    in a way that is unobstrusive and easy to migrate between releases
    """
    options_obj = request.site.options.last()

    if options_obj:
        try:
            options = json.loads(options_obj.options_blob)
        except TypeError as e:
            # Good place for a logger
            options = {}
    else:
        options = {}

    extra_context = {
        "theme_dir_name": request.site_theme.theme_dir_name,
        "siteconfiguration": request.site.siteconfiguration,
        "options": options,
    }
    return extra_context
