from django.http import HttpResponse
from django.shortcuts import  get_object_or_404, render

from django.conf import settings 
from .models import Customer, Restaurant, Item, Cart
import razorpay

# Create your views here.
def say_hello(request):
    # return HttpResponse("Say Hello from MealHive Delivery App")
    return render(request, "index.html")

def open_signup(request):
    return render(request, "signup.html")   

def open_signin(request):
    return render(request, "signin.html")

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')

        try:
            Customer.objects.get(username = username)
            return HttpResponse("Username already exists. Please choose a different username.")
        except:
            Customer.objects.create(
                username = username,
                password = password,
                email = email,
                mobile = mobile,
                address = address,
            )
    return render(request, 'signin.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

    try:
        Customer.objects.get(username = username, password = password)
        if username == 'admin':
            return render(request, 'admin_home.html')
        else:
            restaurantList = Restaurant.objects.all()
            return render(request, 'customer_home.html', {'restaurantList': restaurantList, 'username': username})

    except Customer.DoesNotExist:
        return render(request, 'fail.html')
    
def open_add_restaurant(request):
    return render(request, 'add_restaurant.html')

def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        try:
            Restaurant.objects.get(name = name)
            return HttpResponse("Restaurant already exists.")
        except:
            Restaurant.objects.create(
                name = name,
                picture = picture,
                cuisine = cuisine,
                rating = rating,
            )
    return render(request, 'admin_home.html')

def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurants.html', {'restaurantList': restaurantList})

def open_update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    return render(request, 'update_restaurant.html', {'restaurant': restaurant}) 

def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        restaurant.name = name
        restaurant.picture = picture
        restaurant.cuisine = cuisine
        restaurant.rating = rating
        restaurant.save()
    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurants.html', {'restaurantList': restaurantList})

def delete_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    restaurant.delete()
    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurants.html', {'restaurantList': restaurantList})

def open_update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()

    return render(request, 'update_menu.html', {'restaurant': restaurant, 'itemList': itemList})

def update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        Vegetarian = request.POST.get('vegetarian') == 'on'
        picture = request.POST.get('picture')

        try:
            Item.objects.get(name = name)
            return HttpResponse("Item already exists in the menu.")
        except:
            Item.objects.create(
                restaurant = restaurant,
                name = name,
                description = description,
                price = price,
                vegetarian = Vegetarian,
                picture = picture,
            )
    return render(request, 'admin_home.html')

def view_menu(request, restaurant_id, username):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()
    # itemList = Item.objects.all()
    return render(request, 'customer_menu.html', {'restaurant': restaurant, 'itemList': itemList, 'username': username})


def add_to_cart(request, item_id, username):
    item = Item.objects.get(id = item_id)
    customer = Customer.objects.get(username = username)
    cart, created = Cart.objects.get_or_create(customer=customer)
    cart.items.add(item)
    customer.save()
    return HttpResponse("Item added to cart successfully.")


def show_cart(request, username):
    customer = Customer.objects.get(username = username)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0
    return render(request, 'cart.html', {'itemList': items, 'total_price': total_price, 'username': username})     

def checkout(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if total_price == 0:
        return render(request, 'checkout.html', {'error': 'Your cart is empty.',})

    # Razorpay integration
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    client.session.trust_env = False

    order_data = {
        'amount': int(total_price * 100),  # Amount in paisa
        'currency': 'INR',
        'payment_capture': '1',
    }

    try:
        order = client.order.create(data=order_data)
    except Exception:
        return render(request, 'checkout.html', 
                      { 'username': username, 'cart_items': cart_items, 'total_price': total_price,
                          'error': 'payment service is currently unavailable. Please try again later.',})
    

    return render(request, 'checkout.html', 
                  { 'username': username, 'cart_items': cart_items, 
                   'total_price': total_price,  
                   'razorpay_key_id': settings.RAZORPAY_KEY_ID, 'order_id': order['id'], 'amount_paise': order_data['amount'],})


def orders(request, username):
    Customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=Customer).first()

    cart_items = cart.items.all() if cart else []   
    total_price = cart.total_price() if cart else 0

    if cart:
        cart.items.clear()  # Clear the cart after checkout

    return render(request, 'orders.html', {'username': username, 'cart_items': cart_items, 'total_price': total_price, 'customer': Customer})





