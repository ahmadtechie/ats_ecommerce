from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from elasticsearch import Elasticsearch

from search.documents import CategoryDocument, ProductDocument
from elasticsearch_dsl.query import MoreLikeThis
from elasticsearch_dsl import Search

from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from orders.models import OrderProduct
from store.forms import ReviewForm
from store.models import Product, ReviewRating


class StoreListAndCategoryView(View):
    def get(self, request, category_slug=None):
        if category_slug is not None:
            category = get_object_or_404(Category, slug=category_slug)
            products = Product.objects.filter(category=category, is_available=True)
        else:
            category = None
            products = Product.objects.all().filter(is_available=True).order_by("product_name")

        paginator = Paginator(products, 6)
        page = request.GET.get("page")
        paged_products = paginator.get_page(page)
        product_count = products.count()
        categories = Category.objects.all()

        context = {
            "products": paged_products,
            "product_count": product_count,
            "category": category,
            "categories": categories,
        }
        return render(request, 'store/store.html', context)


class ProductDetailView(DetailView):
    def get(self, request, category_slug, product_slug, order_product=None):
        try:
            single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
            in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
            print(single_product)
        except Exception as e:
            raise e
        if request.user.is_authenticated:
            try:
                order_product = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
            except OrderProduct.DoesNotExist:
                order_product = None

        # get all reviews for this product
        reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)


        similar_products = Product.objects.filter(category=single_product.category)
        context = {
            "product": single_product,
            "in_cart": in_cart,
            "similar_products": similar_products,
            "ordered_product": order_product,
            "reviews": reviews

        }
        return render(request, "store/product_detail.html", context)


def search(request):
    q = request.GET.get('q')
    if q:
        products = ProductDocument.search().query("match", product_name=q)
        categories = CategoryDocument.search().query("match", description=q)
    else:
        products = ''
        categories = ''

    context = {
        "products": products,
        "categories": categories,
    }
    return render(request, 'store/search_results.html', context)


def ascending(request):
    q = request.GET.get('q')
    if q:
        categories = CategoryDocument.search().query("match", categroy_name=q)
        products_descending = ProductDocument.search().query("match", product_name=q).sort("price")
    else:
        products_descending = ''
        categories = ''

    context = {
        "products": products_descending,
        "categories": categories,
    }
    return render(request, 'store/search_results.html', context)


def descending(request):
    q = request.GET.get('q')
    if q:
        categories = CategoryDocument.search().query("match", categroy_name=q)
        products_descending = ProductDocument.search().query("match", product_name=q).sort("-price")
    else:
        products_descending = ''
        categories = ''

    context = {
        "products": products_descending,
        "categories": categories,
    }
    return render(request, 'store/search_results.html', context)


@login_required(login_url="accounts:login")
def submit_review(request, product_id):
    url = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        try:
            review = ReviewRating.objects.get(user_id=request.user.id, product_id=product_id)
            form = ReviewForm(request.POST, instance=review)
            form.save()
            messages.success(request, "Thank you! Your review has been updated.")
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data["subject"]
                data.rating = form.cleaned_data["rating"]
                data.review = form.cleaned_data["review"]
                data.ip = request.META.get("REMOTE_ADDR")
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, "Thank you! Your review has been submitted.")
                return redirect(url)





