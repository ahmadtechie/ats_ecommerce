from django.urls import path
from .views import (
    RegisterUserView,
    ActivateUserView,
    UserLoginView,
    ForgotPasswordView,
    PasswordResetValidateView,
    PasswordResetView,
    logout,
    DashboardView,
    MyOrdersView,
    edit_profile,
    change_password,
    order_detail
)
app_name = "accounts"
urlpatterns = [
    path("register", RegisterUserView.as_view(), name="register"),
    path("login", UserLoginView.as_view(), name="login"),
    path("logout", logout, name="logout"),
    path("",  DashboardView.as_view(), name="dashboard"),
    path("my_orders", MyOrdersView.as_view(), name="my_orders"),
    path("edit_profile", edit_profile, name="edit_profile"),


    path("activate/<uidb64>/<token>/", ActivateUserView.as_view(), name="activate"),
    path("forgotPassword/", ForgotPasswordView.as_view(), name="forgotPassword"),
    path("resetpassword_validate/<uidb64>/<token>/", PasswordResetValidateView.as_view(), name="resetpassword_validate"),
    path("resetPassword/", PasswordResetView.as_view(), name="resetPassword"),
    path("change_password/", change_password, name="change_password"),
    path("order_detail/<int:order_id>/", order_detail, name="order_detail"),
]
