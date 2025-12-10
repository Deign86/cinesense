"""
Custom template tags for the movies app.

This module provides custom Django template tags and filters
for use in movie-related templates.
"""

from django import template
from django.http import QueryDict

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Replace or add query parameters in the current URL.
    
    Usage in templates:
        {% url_replace page=2 %}
        {% url_replace page=page_obj.next_page_number %}
    
    This preserves all existing query parameters and only updates
    the ones specified in kwargs. Useful for pagination with filters.
    
    Args:
        context: Template context (automatically provided)
        **kwargs: Query parameters to replace/add
    
    Returns:
        Query string with updated parameters
    
    Example:
        Current URL: /movies/?genre=Action&year=2020
        {% url_replace page=2 %}
        Result: genre=Action&year=2020&page=2
    """
    request = context['request']
    query = request.GET.copy()
    
    # Update or add the specified parameters
    for key, value in kwargs.items():
        query[key] = value
    
    return query.urlencode()
