from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
            else:
                cart_items = CartItem.objects.all().filter(cart=cart[:1])
            for cart_item in cart_items:
                cart_count += cart_item.quantity
        except Cart.DoesNotExist:
            cart_count = 0
    return dict(cart_count=cart_count)


def add_cart(request, product_id, selected_quantity=0):
    if request.method == "POST":
        selected_quantity = int(request.POST["item_qty"])
    current_user = request.user
    product = Product.objects.get(id=product_id)
    if current_user.is_authenticated:
        product_variation = []
        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except:
                    pass

        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()

        if is_cart_item_exists:
            cart_items = CartItem.objects.filter(product=product, user=current_user)
            # check if current variation is in existing variations
            existing_var_list = []
            cart_ids = []
            for item in cart_items:
                existing_variations = item.variations.all()
                existing_var_list.append(list(existing_variations))
                cart_ids.append(item.id)

            if product_variation in existing_var_list:
                # increase cart item quantity
                index = existing_var_list.index(product_variation)
                item_id = cart_ids[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += selected_quantity
                item.save()

            else:
                # create a new cart item
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=selected_quantity,
                user=current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('carts:cart')
    # if user is not authenticated
    else:
        product_variation = []
        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except:
                    pass

        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(product=product, cart=cart)
        if cart_items.exists():
            # check if current variation is in existing variations
            existing_var_list = []
            cart_ids = []
            for item in cart_items:
                existing_variations = item.variations.all()
                existing_var_list.append(list(existing_variations))
                cart_ids.append(item.id)

            if product_variation in existing_var_list:
                # increase cart item quantity
                index = existing_var_list.index(product_variation)
                item_id = cart_ids[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += selected_quantity
                item.save()

            else:
                # create a new cart item
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=selected_quantity,
                cart=cart
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('carts:cart')


def remove_cart_item(request, product_id, cart_item_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    except:
        pass
    return redirect("carts:cart")


def remove_cart(request, product_id, cart_item_id, total=0):
    product = get_object_or_404(Product, id=product_id)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
                cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
            else:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_item = CartItem.objects.get(cart=cart, product=product, id=cart_item_id)
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                for cart_item in cart_items:
                    total += (cart_item.product.price * cart_item.quantity)
                subtotal = cart_item.product.price * cart_item.quantity
                tax = (2 * total) / 100
                grand_total = total + tax
                return JsonResponse({"status": "Success",
                                     "message": "Removed a product from the cart",
                                     "cart_counter": counter(request),
                                     "qty": cart_item.quantity,
                                     "total": total,
                                     "grand_total": grand_total,
                                     "subtotal": subtotal,
                                     "tax": tax})
            else:
                cart_item.quantity = 0
                cart_item.save()
                for cart_item in cart_items:
                    total += (cart_item.product.price * cart_item.quantity)
                subtotal = 0
                tax = (2 * total) / 100
                grand_total = total + tax
                return JsonResponse({"status": "Success",
                                     "message": "Removed a product from the cart",
                                     "cart_counter": counter(request),
                                     "qty": cart_item.quantity,
                                     "total": total,
                                     "grand_total": grand_total,
                                     "subtotal": subtotal,
                                     "tax": tax})
        except:
            return JsonResponse({"status": "Failed", "message": "Invalid request"})
    else:
        return JsonResponse({"status": "Failed", "message": "Invalid request"})


def cart(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True).order_by("-cart_id")
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by("-cart_id")

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except Cart.DoesNotExist:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/cart.html", context)


@login_required(login_url="accounts:login")
def checkout(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except Cart.DoesNotExist:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/checkout.html", context)


def increase_cart_item(request, product_id, cart_item_id, total=0):
    product = get_object_or_404(Product, id=product_id)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
                cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
            else:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_item = CartItem.objects.get(cart=cart, product=product, id=cart_item_id)
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            cart_item.quantity += 1
            cart_item.save()
            for cart_item in cart_items:
                total += (cart_item.product.price * cart_item.quantity)
            subtotal = cart_item.product.price * cart_item.quantity
            tax = (2 * total) / 100
            grand_total = total + tax
            return JsonResponse({"status": "Success",
                                 "message": "Added a product to the cart",
                                 "cart_counter": counter(request),
                                 "qty": cart_item.quantity,
                                 "total": total,
                                 "grand_total": grand_total,
                                 "subtotal": subtotal,
                                 "tax": tax})

        except:
            return JsonResponse({"status": "Failed", "message": "Invalid request"})
    else:
        return JsonResponse({"status": "Failed", "message": "Invalid request"})


def clear_carts(request):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart)
        if cart_items.exists():
            for cart_item in cart_items:
                cart_item.delete()
    except:
        pass
    return redirect("carts:cart")
