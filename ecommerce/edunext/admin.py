"""
Django admin page for custom eduNEXT models
"""
from django.contrib import admin

from .models import SiteOptions


class SiteOptionsAdmin(admin.ModelAdmin):
    """
    Admin interface for the SiteOptions object.
    """
    list_display = ('site', 'options_blob')
    search_fields = ('site__domain', 'options_blob')

    class Meta(object):
        """
        Meta class for SiteOptions admin model
        """
        model = SiteOptions


admin.site.register(SiteOptions, SiteOptionsAdmin)
