from ast import Or
import json

from orders.models   import Order, Cart
from django.http     import HttpResponse, JsonResponse
from django.views    import View
from core.decorator  import log_in_decorator
from json.decoder    import JSONDecodeError
from django.db       import transaction
from decimal         import Decimal

from products.models import Product

class CartView(View):
    @log_in_decorator
    def get(self,request):
        try: 
            carts = Cart.objects.filter(user_id = request.user.id)
            result = []
            for cart in carts:
                result.append({
                    "cart_id" : cart.id,
                    "product"  : cart.product.name,
                    "product_image_1" : cart.product.thumnail_url_1,
                    "product_image_2" : cart.product.thumnail_url_2,
                    "price" : cart.product.price,
                    "quantity" : cart.quantity,
                    "product_id" : cart.product.id
                    })
            return JsonResponse({'carts' : result}, status = 200)

        except KeyError:
            return JsonResponse({'message':'KeyError'}, status = 400)   

    @log_in_decorator
    def post(self,request):
        try : 
            user_id    = request.user.id
            data       = json.loads(request.body)
            quantity   = data['quantity']
            price      = data['price']
            product_id = data['product_id']

            if Cart.objects.filter(user_id = user_id,product_id = product_id).exists():
                cart = Cart.objects.filter(user_id = user_id).get(product_id = product_id)
                cart.quantity += int(quantity)
                cart.price    += Decimal(price)
                cart.save()
                return JsonResponse({'message' : 'cart updated'}, status = 201)

            Cart.objects.create(   
                quantity   = quantity,
                price      = price,
                product_id = data['product_id'],
                user_id    = user_id
            )
            return JsonResponse({'message': 'cart created'}, status = 201)

        except KeyError:
            return JsonResponse({'message':'KeyError'}, status = 400)   

        except JSONDecodeError:
            return JsonResponse({'message':'json형태이상함'}, status = 400)
            
    def delete(self,request):
        try:
            data = json.loads(request.body)
            cart = Cart.objects.filter(id=data['cart_id'])
            cart.delete()
            return HttpResponse(status = 204)
            
        except KeyError:
            return JsonResponse({'message':'키에러'}, status = 400)

        except Order.DoesNotExist:
            return JsonResponse({'message':'삭제할 장바구니가 존재하지 않습니다.'}, status = 400)

        except JSONDecodeError:
            return JsonResponse({'message':'json형태이상함'}, status = 400)

    def patch(self,request):
        try:
            data = json.loads(request.body)
            data = data['carts_info']
            for i in range(len(data)) :
                quantity = data[i]["quantity"]
                price    = data[i]["price"]
                Cart.objects.filter(id = data[i]["cart_id"]).update(
                    quantity = quantity,
                    price    = price
                )
            return JsonResponse({'message' : 'cart updated'},status = 200)
            
        except KeyError:
            return JsonResponse({'message':'KeyError'}, status = 400)

class OrderView(View):
    @log_in_decorator
    def get(self,request):
        try : 
            orders = Order.objects.filter(user_id = request.user.id)
            result = []
            for order in orders:
                product = order.product
                status  = order.status
                result.append({
                        "order_id" : order.id,
                        "product"  : product.name,
                        "product_image_1" : product.thumnail_url_1,
                        "product_image_2" : product.thumnail_url_2,
                        "price" : order.price,
                        "quantity" : order.quantity,
                        "status" : status.status,
                        "product_id" : order.product.id
                    })
            return JsonResponse({'orders' : result}, status = 200)

        except KeyError:
            return JsonResponse({'message':'KeyError'}, status = 400) 
    
    @log_in_decorator
    def post(self,request):
        try : 
            data = json.loads(request.body)
            if 'cart_id' in list(data.keys()):
                carts_id = list(data['cart_id'])

                with transaction.atomic():
                    order_list = []
                    for i in carts_id:
                        cart = Cart.objects.get(id = i)
                        order_list.append(Order(
                            quantity   = cart.quantity,
                            price      = cart.price,
                            product_id = cart.product_id,
                            user_id    = cart.user_id
                            ))
                        cart.delete()
                    Order.objects.bulk_create(order_list)
                    
            else:
                user_id  = request.user
                product  = Product.objects.get(id = data['product_id'])
                quantity = data['quantity']
                user_id  = request.user.id
                Order.objects.create(  
                    product_id = product.id,
                    quantity   = quantity,
                    user_id    = user_id,
                    price      = product.price
                )
            return JsonResponse({'message' : 'order created'}, status = 201)

        except KeyError:
            return JsonResponse({'message':'KeyError'}, status = 400)   

        except Cart.DoesNotExist:
            return JsonResponse({'message':'삭제할 장바구니가 존재하지 않습니다.'},status = 404)

        except JSONDecodeError:
            return JsonResponse({'message':'json형태이상함'},status = 400)
