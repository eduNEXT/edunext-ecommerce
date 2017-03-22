#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains django context_processors needed by edunext.
"""
from ecommerce.edunext.models import SiteOptions


def theme_options(request):
    """
    This context processor lets us add extra context to the themable templates
    in a way that is unobstrusive and easy to migrate between releases
    """

    try:
        options = request.site.siteoptions.options_blob
    except SiteOptions.DoesNotExist:
        # Good place for a logger
        options = {}

    try:
        site_theme_name = request.site_theme.theme_dir_name
    except AttributeError:
        site_theme_name = None

    return {
        "theme_dir_name": site_theme_name,
        "site_configuration": request.site.siteconfiguration,
        "options": options,
    }
