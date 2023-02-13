import requests
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import TemplateView

from accounts.forms import RegistrationForm, UserProfileForm, UserForm
from accounts.models import Account, UserProfile
from carts.models import Cart, CartItem
from carts.views import _cart_id
from category.models import Category
from orders.models import Order, OrderProduct


class RegisterUserView(View):
    def get(self, request):
        form = RegistrationForm()

        context = {
            "form": form,
        }
        return render(request, "accounts/register.html", context)

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            print("form is valid")
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            username = email.split("@")[0]
            print(username)

            user = Account.objects.create_user(email=email, username=username, password=password)
            user.save()

            # send user activation email to user
            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            message = render_to_string("accounts/account_verification_email.html", {
                "user": user,
                "domain": current_site,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            return redirect(f"/accounts/login?command=verification&email={email}")
        else:
            if form.non_field_errors():
                messages.error(request, "Password does not match!")
            context = {
                "form": RegistrationForm(request.POST)
            }
            return render(request, "accounts/register.html", context)


class ActivateUserView(View):
    def get(self, request, uidb64, token):
        try:
            # decode the uidb64 & check if it matches user id
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Account._default_manager.get(pk=uid)
        except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Congratulations! Your account is activated.")
            return redirect("accounts:login")
        else:
            messages.error(request, "Invalid activation link")
            return redirect("accounts:register")


class UserLoginView(View):

    def get(self, request):
        return render(request, "accounts/login.html")

    def post(self, request):
        email = request.POST["email"]
        password = request.POST["password"]

        user = auth.authenticate(email=email, password=password)
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_items = CartItem.objects.filter(cart=cart)

                    product_variation = []
                    for item in cart_items:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Get the user cart items & variations
                    cart_item = CartItem.objects.filter(user=user)
                    existing_var_list = []
                    cart_ids = []
                    for item in cart_item:
                        existing_variations = item.variations.all()
                        existing_var_list.append(list(existing_variations))
                        cart_ids.append(item.id)

                    for pr in product_variation:
                        if pr in existing_var_list:
                            index = existing_var_list.index(pr)
                            item_id = cart_ids[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            auth.login(request, user)
            messages.success(request, "You are logged in.")
            url = request.META.get("HTTP_REFERER")
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split("=") for x in query.split("&"))
                if "next" in params:
                    nextPage = params["next"]
                    return redirect(nextPage)
            except:
                return redirect("home")
        else:
            messages.error(request, "Invalid login credentials")
            return redirect("accounts:login")
        return render(request, "accounts/login.html")


class ForgotPasswordView(View):
    def get(self, request):
        return render(request, "accounts/forgotPassword.html")

    def post(self, request):
        email = request.POST["email"]
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # send password reset email to user
            current_site = get_current_site(request)
            mail_subject = "Reset Your Password"
            message = render_to_string("accounts/reset_password_email.html", {
                "user": user,
                "domain": current_site,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, "Password reset email has been sent to your email address.")
            return redirect("accounts:login")
        else:
            messages.error(request, "Account does not exist!")
            return redirect("accounts:login")


class PasswordResetValidateView(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Account._default_manager.get(pk=uid)
        except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
            uid = None
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            request.session["uid"] = uid
            messages.success(request, "Please reset your password")
            return redirect("accounts:resetPassword")
        else:
            messages.error(request, "This link is expired!")
            return redirect("accounts:login")


class PasswordResetView(View):
    def get(self, request):
        return render(request, "accounts/resetPassword.html")

    def post(self, request):
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password == confirm_password:
            uid = request.session.get("uid")
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successful")
            return redirect("accounts:login")
        else:
            messages.error(request, "Password do not match")
            return redirect("resetPassword")


@login_required(login_url="accounts:login")
def logout(request):
    auth.logout(request)
    messages.success(request, "You are logged out.")
    return redirect("accounts:login")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        orders = Order.objects.order_by("-created_at").filter(user_id=self.request.user.id, is_ordered=True)
        context["orders"] = "orders"
        context["orders_count"] = orders.count()
        return context


class MyOrdersView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/my_orders.html"

    def get_context_data(self, **kwargs):
        context = super(MyOrdersView, self).get_context_data(**kwargs)
        context["orders"] = Order.objects.filter(user=self.request.user, is_ordered=True).order_by("-created_at")
        return context


@login_required(login_url="accounts:login")
def edit_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:edit_profile")
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "user_profile": user_profile,
    }
    return render(request, "accounts/edit_profile.html", context)


@login_required(login_url="accounts:login")
def change_password(request):
    if request.method == "POST":
        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        user = Account.objects.get(username__exact=request.user.username)
        if new_password == confirm_password:
            # check if entered password matches current one
            is_password_correct = user.check_password(current_password)
            if is_password_correct:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password updated successfully")
                return redirect("accounts:login")
            else:
                messages.error(request, "Please enter valid current password")
        else:
            messages.error(request, "Password does not match")
            return redirect("accounts:change_password")

    return render(request, "accounts/change_password.html")


@login_required(login_url="accounts:login")
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)

    sub_total = 0
    for i in order_detail:
        sub_total += i.product_price * i.quantity
    context = {
        "order_detail": order_detail,
        "order": order,
        "sub_total": sub_total
    }

    return render(request, "accounts/order_detail.html", context)
