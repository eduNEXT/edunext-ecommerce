#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains django context_processors needed by edunext.
"""


def theme_options(request):
    """
    This context processor lets us add extra context to the themable templates
    in a way that is unobstrusive and easy to migrate between releases
    """
    options_obj = request.site.options.last()
    if options_obj:
        try:
            options = options_obj.options_blob
        except TypeError:
            # Good place for a logger
            options = {}
    else:
        options = {}

    try:
        site_theme_name = request.site_theme.theme_dir_name
    except AttributeError:
        site_theme_name = None

    extra_context = {
        "theme_dir_name": site_theme_name,
        "site_configuration": request.site.siteconfiguration,
        "options": options,
    }
    return extra_context
