#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains some utilitary function to complement the ecommerce service.
"""
from oscar.templatetags.currency_filters import currency as oscar_currency


def disable_translation(value):
    """
    This function just return the passed value instead of doing translation
    """
    return value


def ednx_currency(value, currency=None):
    """
    This function is a proxy of the django-oscar "currency" function
    Returns an ASCII encoded string after applying "currency" function
    """
    result = oscar_currency(value, currency)
    return result.encode('ascii', 'replace')
