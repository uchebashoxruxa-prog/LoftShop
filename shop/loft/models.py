from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.urls import reverse


class Category(models.Model):
    title = models.CharField(max_length=150, verbose_name='Название категории')
    icon = models.ImageField(upload_to='icons/', null=True, blank=True, verbose_name='Иконка')
    slug = models.SlugField(unique=True, verbose_name='Слаг категории')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories',
                               verbose_name='Родитель')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('category', kwargs={'slug': self.slug})

    def get_icon(self):
        if self.icon:
            return self.icon.url
        else:
            return ''


    class Meta:
        verbose_name = 'Категорию'
        verbose_name_plural = 'Категории'


class Product(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название товара')
    slug = models.SlugField(unique=True, verbose_name='Слаг товара')
    description = models.TextField(verbose_name='Описание товара')
    quantity = models.IntegerField(default=10, verbose_name='Количество')
    price = models.IntegerField(default=1000, verbose_name='Цена')
    color_name = models.CharField(max_length=100, default='Белый', verbose_name='Название цвета')
    color_code = models.CharField(max_length=20, default='#ffffff', verbose_name='Код цвета')
    width = models.IntegerField(verbose_name='Ширина')
    length = models.IntegerField(verbose_name='Глубина')
    height = models.IntegerField(verbose_name='Высота')
    discount = models.IntegerField(default=0, verbose_name='Скидка на товар')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', related_name='products')
    model = models.ForeignKey('ModelProduct', on_delete=models.CASCADE, verbose_name='Модель товара',
                              related_name='model_products')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product', kwargs={'slug': self.slug})

    def get_icon(self):
        if self.icon:
            return self.icon.url
        else:
            return ''

    def first_photo(self):
        if self.images:
            try:
                return self.images.first().image.url
            except:
                return ''
        else:
            return ''

    def get_price(self):
        if self.discount:
            p = self.price - int(self.price * self.discount / 100)
            return p
        else:
            return self.price


    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


class ModelProduct(models.Model):
    title = models.CharField(max_length=150, verbose_name='Название модели')
    slug = models.SlugField(unique=True, verbose_name='Слаг модели')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Модель'
        verbose_name_plural = 'Модели'


class ImagesProduct(models.Model):
    image = models.ImageField(upload_to='products/', verbose_name='Фото товара')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар', related_name='images')

    def __str__(self):
        return f'Фото товара {self.product.title}'

    class Meta:
        verbose_name = 'Фото'
        verbose_name_plural = 'Фото товаров'


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    phone = models.CharField(max_length=30, verbose_name='Номер телефона')
    region = models.CharField(max_length=100, verbose_name='Регион', null=True, blank=True)
    city = models.CharField(max_length=100, verbose_name='Город', null=True, blank=True)
    street = models.CharField(max_length=100, verbose_name='Улица', null=True, blank=True)
    house = models.CharField(max_length=100, verbose_name='Дом/Корпус', null=True, blank=True)
    flat = models.CharField(max_length=100, verbose_name='Квартира №', null=True, blank=True)

    def __str__(self):
        return f'Покупатель {self.user.username}'

    class Meta:
        verbose_name = 'Покупателя'
        verbose_name_plural = 'Покупатели'


class FavoriteProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    def __str__(self):
        return f'Товар {self.product.title} пользователя {self.user.username}'

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class Cart(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, verbose_name='Покупатель')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f'Корзина №{self.pk} покупателя {self.customer.user.username}'

    @property
    def cart_total_price(self):
        products = self.productcart_set.all()
        price = sum([i.get_total_price for i in products])
        return price

    @property
    def cart_total_quantity(self):
        products = self.productcart_set.all()
        quantity = sum([i.quantity for i in products])
        return quantity

    class Meta:
        verbose_name = 'Корзина покупателя'
        verbose_name_plural = 'Корзины покупателей'


class ProductCart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name='Корзина')
    quantity = models.IntegerField(default=0, verbose_name='Количество')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    @property
    def get_total_price(self):
        return self.quantity * self.product.get_price()

    @property
    def get_old_price(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f'Товар {self.product.title} корзины №{self.cart.pk} покупателя {self.cart.customer.user}'

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'


class Delivery(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Покупатель')
    phone = models.CharField(max_length=30, verbose_name='Номер Получателя')
    comment = models.CharField(max_length=300, verbose_name='Комментарии', null=True, blank=True)
    region = models.ForeignKey('Region', on_delete=models.CASCADE, verbose_name='Регион')
    city = models.ForeignKey('City', on_delete=models.CASCADE, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    home = models.CharField(max_length=100, verbose_name='Дом/Корпус')
    flat = models.CharField(max_length=100, verbose_name='Квартира номер', null=True, blank=True)
    status = models.BooleanField(default=False, verbose_name='Статус доставки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата оформления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата получения')

    def __str__(self):
        return f'Доставка для покупателя {self.customer.user.username}'

    class Meta:
        verbose_name = 'Доставку'
        verbose_name_plural = 'Доставки'


class Region(models.Model):
    name = models.CharField(max_length=100, verbose_name='Регион')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'


class City(models.Model):
    name = models.CharField(max_length=100, verbose_name='Город')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, verbose_name='Регион', related_name='cities')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Заказ')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name='Корзина')
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE, verbose_name='Доставка')
    price = models.IntegerField(default=0, verbose_name='Сумма заказа')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата получения заказа')
    completed = models.BooleanField(default=False, verbose_name='Статус оплаты заказа')

    def __str__(self):
        return f'Заказ №: {self.pk}, покупателя: {self.customer.user.username}'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы покупателей'


class ProductOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ', related_name='products')
    name = models.CharField(max_length=300, verbose_name='Название товара')
    slug = models.CharField(max_length=300, verbose_name='Слаг товара')
    price = models.IntegerField(default=0, verbose_name='Цена товара')
    photo = models.ImageField(upload_to='products/', verbose_name='Фото товара')
    quantity = models.IntegerField(default=0, verbose_name='Количество')
    total_price = models.IntegerField(default=0, verbose_name='На сумму в количестве')

    def __str__(self):
        return f'Товар {self.name}, заказа №: {self.order.pk}, покупателя: {self.order.customer.user.username}'

    class Meta:
        verbose_name = 'Товар заказа'
        verbose_name_plural = 'Товар заказов'


class Contact(models.Model):
    name = models.CharField(max_length=50, verbose_name='Имя клиента')
    phone = models.CharField(max_length=50, verbose_name='Телефон клиента')
    text = models.CharField(max_length=350, verbose_name='Запрос клиента')
    file = models.FileField(upload_to='contact/', verbose_name='Файл', null=True, blank=True)

    def __str__(self):
        return f'Запрос от {self.name}, телефон: {self.phone}'

    class Meta:
        verbose_name = 'Запрос клиента'
        verbose_name_plural = 'Запросы клиентов'
