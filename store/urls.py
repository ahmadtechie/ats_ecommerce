from django.urls import path
from .views  import StoreListAndCategoryView, ProductDetailView, submit_review
from store import views as search_views


app_name = "store"
urlpatterns = [
    path('', StoreListAndCategoryView.as_view(), name='store'),
    path('category/<slug:category_slug>/', StoreListAndCategoryView.as_view(), name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('search/', search_views.search, name="search"),
    path('search/', search_views.descending, name="descending"),
    path('search/', search_views.ascending, name="ascending"),
    path('submit_review/<int:product_id>', submit_review, name="submit_review")
]

