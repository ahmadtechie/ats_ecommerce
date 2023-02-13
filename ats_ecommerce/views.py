from django.db.models import Q
from django.views.generic import TemplateView
from django.shortcuts import render

from category.models import Category
from store.models import Product


class HomePageView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context["products"] = Product.objects.filter(is_available=True,
                                                     price__lt=5000). \
            order_by("-created_date")
        return context


def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)


class ContactUsPageView(TemplateView):
    template_name = "contact.html"



