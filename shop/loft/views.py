from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import *
from django.views.generic import ListView, DetailView
from .forms import LoginForm, RegisterForm, DeliveryForm, EditUserForm, EditCustomerForm, ContactForm
from django.contrib.auth import login, logout
from django.contrib import messages
from .tests import filter_products
from django.contrib.auth.mixins import LoginRequiredMixin
from .utils import CartForAuthUser, info_about_cart
import stripe
from shop.settings import STRIPE_SECRET_KEY


class MainPage(ListView):
    model = Category
    template_name = 'loft/main.html'
    context_object_name = 'categories'
    extra_context = {'title': 'LOFT МЕБЕЛЬ КОМФОРТА'}

    def get_queryset(self):
        categories = Category.objects.filter(parent=None)

        return categories


class ProductDetail(DetailView):
    model = Product
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super(ProductDetail, self).get_context_data()
        product = context['product']
        context['title'] = product.title
        context['product_models'] = Product.objects.filter(model=product.model)
        context['same_products'] = Product.objects.filter(category__parent=product.category.parent).exclude(
            pk=product.pk).order_by('-created_at')

        return context


def auth_user_page(request):
    if not request.user.is_authenticated:
        context = {
            'title': 'Авторизация/Регистрация',
            'log_form': LoginForm(),
            'reg_form': RegisterForm(),
        }

        return render(request, 'loft/auth.html', context)
    else:
        return redirect('main')


def login_user_view(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            form = LoginForm(data=request.POST)
            if form.is_valid():
                user = form.get_user()
                if user:
                    login(request, user)
                    return redirect('main')

        messages.error(request, 'Неверный логин или пароль')

        return redirect('auth')

    else:
        return redirect('main')


def logout_user_view(request):
    logout(request)

    return redirect('main')


def register_user_view(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            form = RegisterForm(data=request.POST)
            phone = request.POST.get('phone')
            if form.is_valid():
                user = form.save()
                customer = Customer.objects.create(user=user, phone=phone)
                customer.save()
                cart = Cart.objects.create(customer=customer)
                cart.save()
                login(request, user)

            for err in form.errors:
                messages.error(request, form.errors[err].as_text())

            return redirect('auth')

    else:
        return redirect('main')


class ProductByCategory(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'loft/category.html'
    paginate_by = 4

    def get_queryset(self):
        category = Category.objects.get(slug=self.kwargs['slug'])
        products = Product.objects.filter(category__in=category.subcategories.all())
        products = filter_products(self.request, products).order_by('-created_at')
        
        return products

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProductByCategory, self).get_context_data()
        category = Category.objects.get(slug=self.kwargs['slug'])
        products = Product.objects.filter(category__slug=self.request.GET.get('cat'))

        context['title'] = category.title
        context['subcats'] = category.subcategories.all()
        context['prices'] = [i for i in range(1000, 100001, 1000)]
        context['models'] = set(i.model for i in products)
        try:
            context['cat_name'] = Category.objects.get(slug=self.request.GET.get('cat')).title
            context['model_name'] = ModelProduct.objects.get(slug=self.request.GET.get('model')).title
        except:
            pass

        return context


class SalesProducts(ListView):
    model = Product
    context_object_name = 'products'
    extra_context = {'title': 'Товары по акции'}
    paginate_by = 4

    def get_queryset(self):
        products = Product.objects.filter(discount__gt=0).order_by('-created_at')

        return products


@login_required(login_url='auth')
def save_delete_favorite(request, slug):
    user = request.user
    product = Product.objects.get(slug=slug)
    favorites = FavoriteProduct.objects.filter(user=user)

    if product not in [i.product for i in favorites]:
        FavoriteProduct.objects.create(user=user, product=product)
    else:
        fav = FavoriteProduct.objects.get(user=user, product=product)
        fav.delete()

    next_page = request.META.get('HTTP_REFERER', 'main')

    return redirect(next_page)


class FavoriteListView(LoginRequiredMixin, ListView):
    model = FavoriteProduct
    template_name = 'loft/product_list.html'
    context_object_name = 'products'
    extra_context = {'title': 'Избранные товары'}
    login_url = 'auth'

    def get_queryset(self):
        favorites = FavoriteProduct.objects.filter(user=self.request.user)
        products = [i.product for i in favorites]
        return products


@login_required(login_url='auth')
def action_with_cart(request, slug, action):
    cart = CartForAuthUser(request, slug, action)
    next_page = request.META.get('HTTP_REFERER', 'main')

    return redirect(next_page)


@login_required(login_url='auth')
def customer_cart_view(request):
    cart = info_about_cart(request)
    context = {
        'title': 'Ваша корзина',
        'products_cart': cart['products_cart'],
        'cart': cart['cart']
    }

    return render(request, 'loft/my_cart.html', context)


@login_required(login_url='auth')
def checkout_view(request):
    cart = info_about_cart(request)
    if cart['products_cart'] and request.method == 'POST':
        regions = Region.objects.all()
        dict_city = {i.pk: [[j.name, j.pk] for j in i.cities.all()] for i in regions}

        context = {
            'title': 'Оформления заказа',
            'products_cart': cart['products_cart'],
            'cart': cart['cart'],
            'form': DeliveryForm(),
            'dict_city': dict_city
        }

        return render(request, 'loft/checkout.html', context)
    else:
        return redirect('main')


@login_required(login_url='auth')
def create_checkout_session(request):
    stripe.api_key = STRIPE_SECRET_KEY
    if request.method == 'POST':
        cart = info_about_cart(request)
        total_price = cart['cart'].cart_total_price
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'rub',
                    'product_data': {'name': ', '.join(i.product.title for i in cart['products_cart'])},
                    'unit_amount': int(total_price * 100)
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('success')),
            cancel_url=request.build_absolute_uri(reverse('checkout'))
        )

        request.session[f'form_{request.user.pk}'] = request.POST

        return redirect(session.url)


@login_required(login_url='auth')
def success_payment(request):
    cart = info_about_cart(request)
    try:
        form = request.session.get(f'form_{request.user.pk}')
        request.session.pop(f'form_{request.user.pk}')
    except:
        form = False

    if cart['products_cart'] and form:
        delivery_form = DeliveryForm(data=form)
        if delivery_form.is_valid():
            delivery = delivery_form.save(commit=False)
            delivery.customer = Customer.objects.get(user=request.user)
            delivery.save()

            cart_user = CartForAuthUser(request)
            cart_user.save_order(delivery)
            cart_user.clear_cart()
        else:
            return redirect('checkout')

        context = {'title': 'Успешная оплата'}
        return render(request, 'loft/success.html', context)

    else:
        return redirect('main')


@login_required(login_url='auth')
def profile_customer(request):
    if request.method == 'POST':
        user_form = EditUserForm(request.POST, instance=request.user)
        customer_form = EditCustomerForm(request.POST, instance=request.user.customer)
        if user_form.is_valid() and customer_form.is_valid():
            user_form.save()
            customer_form.save()
            return redirect('profile')
    else:
        user_form = EditUserForm(instance=request.user)
        customer_form = EditCustomerForm(instance=request.user.customer)

    context = {
        'title': 'Профиль покупателя',
        'user_form': user_form,
        'customer_form': customer_form,
        'order': Order.objects.filter(customer=request.user.customer).last()
    }

    return render(request, 'loft/profile.html', context)


class CustomerOrders(LoginRequiredMixin, ListView):
    model = Order
    context_object_name = 'orders'
    extra_context = {'title': 'История заказов'}
    login_url = 'auth'

    def get_queryset(self):
        orders = Order.objects.filter(customer=self.request.user.customer)
        return orders.order_by('-created_at')


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contact')
    else:
        form = ContactForm()

    context = {
        'title': 'Связаться с нами',
        'form': form
    }

    return render(request, 'loft/contact.html', context)
