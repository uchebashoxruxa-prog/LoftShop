from .models import Cart, ProductCart, Product, Customer, Order, ProductOrder


class CartForAuthUser:
    def __init__(self, request, slug=None, action=None):
        self.user = request.user
        if slug and action:
            self.add_or_delete(slug, action)

    def get_cart_info(self):
        customer = self.user.customer
        cart = customer.cart
        products_cart = cart.productcart_set.all()
        return {
            'cart': cart,
            'products_cart': products_cart,
            'customer': customer
        }

    def add_or_delete(self, slug, action):
        cart = self.get_cart_info()['cart']
        product = Product.objects.get(slug=slug)
        product_cart, created = ProductCart.objects.get_or_create(cart=cart, product=product)

        if action == 'add' and product.quantity > 0 and product_cart.quantity < product.quantity:
            product_cart.quantity += 1
        elif action == 'delete':
            product_cart.quantity -= 1
        elif action == 'clear':
            product_cart.quantity = 0

        product_cart.save()

        if product_cart.quantity == 0:
            product_cart.delete()

    def save_order(self, delivery):
        data = self.get_cart_info()
        order = Order.objects.create(customer=data['customer'], delivery=delivery, cart=data['cart'],
                                     price=data['cart'].cart_total_price, completed=True)
        order.save()

        for p_cart in data['products_cart']:
            product = ProductOrder.objects.create(order=order, name=p_cart.product.title, slug=p_cart.product.slug,
                                                  price=p_cart.product.get_price(), photo=p_cart.product.first_photo(),
                                                  quantity=p_cart.quantity, total_price=p_cart.get_total_price)
            product.save()

    def clear_cart(self):
        cart = self.get_cart_info()['cart']
        products_cart = cart.productcart_set.all()
        for p_cart in products_cart:
            product = p_cart.product
            product.quantity -= p_cart.quantity
            product.save()
            p_cart.delete()

        cart.save()


def info_about_cart(request):
    cart = CartForAuthUser(request)
    info = cart.get_cart_info()
    return info


