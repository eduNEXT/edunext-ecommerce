#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains models used by edunext for customizing the ecommerce service.
"""
import collections

from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield.fields import JSONField


class SiteOptions(models.Model):
    """
    This is where the information about the site's options are stored in the database

    Fields:
        site (OneToOneField): Foreign Key field pointing to django Site model
        options_blob (TextField): Contains a json with flexible options to use
    """
    site = models.OneToOneField('sites.Site', null=False, blank=False)
    options_blob = JSONField(
        verbose_name=_('Extended Site Options'),
        help_text=_('JSON string containing the extended edunext settings.'),
        null=False,
        blank=False,
        default={},
        load_kwargs={'object_pairs_hook': collections.OrderedDict},
    )

    class Meta(object):
        """
        Meta class for SiteOptions model
        """
        verbose_name_plural = "SiteOptions"
