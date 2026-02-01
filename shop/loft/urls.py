from django.urls import path
from .views import *


urlpatterns = [
    path('', MainPage.as_view(), name='main'),
    path('product/<slug:slug>/', ProductDetail.as_view(), name='product'),
    path('authentication/', auth_user_page, name='auth'),
    path('login/', login_user_view, name='login'),
    path('logout/', logout_user_view, name='logout'),
    path('register/', register_user_view, name='register'),
    path('category/<slug:slug>/', ProductByCategory.as_view(), name='category'),
    path('sales/', SalesProducts.as_view(), name='sales'),
    path('action_favorite/<slug:slug>/', save_delete_favorite, name='action_favorite'),
    path('favorites/', FavoriteListView.as_view(), name='favs'),
    path('action_cart/<slug:slug>/<str:action>/', action_with_cart, name='action_cart'),
    path('basket/', customer_cart_view, name='basket'),
    path('checkout/', checkout_view, name='checkout'),
    path('payment/', create_checkout_session, name='payment'),
    path('success/', success_payment, name='success'),
    path('profile/', profile_customer, name='profile'),
    path('orders/', CustomerOrders.as_view(), name='orders'),
    path('contact/', contact_view, name='contact')


]