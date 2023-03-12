from django.core.paginator import Paginator

from django.conf import settings


def the_paginator(QuerySet, request):
    paginator = Paginator(QuerySet, settings.NUMBER_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
