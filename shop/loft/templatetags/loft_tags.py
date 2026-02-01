from django import template
from loft.models import Category, FavoriteProduct

register = template.Library()


@register.simple_tag()
def get_categories():
    cats = Category.objects.filter(parent=None)

    return cats


@register.simple_tag(takes_context=True)
def query_params(context, **kwargs):
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        if value is not None and (key != 'page' or value != 1):
            query[key] = value
        elif key in query:
            del query[key]

        lst = ['model', 'price_from', 'price_to']

        for i in lst:
            if key == 'cat':
                try:
                    del query[i]
                except:
                    pass

    return query.urlencode()


@register.simple_tag()
def get_favorites(user):
    favorites = FavoriteProduct.objects.filter(user=user)
    products = [i.product for i in favorites]

    return products
