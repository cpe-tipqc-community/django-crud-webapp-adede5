from datetime import date
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.template.loader import get_template

from .decorators import *
from .models import *
from .forms import OrderForm, CreateUserForm, CustomerForm
from .filters import OrderFilter
from .utils import render_to_pdf


@unauthenticated_user
def register_page(request):
	form = CreateUserForm()

	if request.method == 'POST':
		form = CreateUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			username = form.cleaned_data.get('username')

			group = Group.objects.get(name='customer')
			user.groups.add(group)

			Customer.objects.create(
				user=user,
				name=user,
				email=user.email,
			)

			messages.success(request,'Account created! Welcome, ' + username)
			return redirect('login')

	context = {'form':form}
	return render(request, 'accounts/register.html', context)

@unauthenticated_user
def login_page(request):
	form = CreateUserForm()
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')

		user = authenticate(request, username=username, password=password)

		if user is not None:
			login(request, user)
			if request.user.is_staff:
				return redirect('/')
			else:
				customer = Customer.objects.get(user=user)
				customer_id = customer.id
				context = {'customer':customer, 'customer_id':customer_id}
				return render(request, 'accounts/user.html', context)
		else:
			messages.info(request, 'Username OR password is incorrect')

	context = {}
	return render(request, 'accounts/login.html', context)


def logout_user(request):
	logout(request)
	return redirect('login')

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def user_page(request, pk):
	customer = Customer.objects.get(id=pk)
	orders = request.user.customer.order_set.all()

	total_orders = orders.count()
	delivered = orders.filter(status='Delivered').count()
	stash = orders.filter(status='In the stash').count()
	on_cour = orders.filter(status='On the courier').count()

	context = {'customer':customer, 'orders':orders,'total_orders':total_orders,'delivered':delivered, 'stash':stash, 'on_cour':on_cour}
	return render(request, 'accounts/user.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def account_settings(request,pk):
	
	customer = request.user.customer
	form = CustomerForm(instance=customer)

	if request.method == 'POST':
		form = CustomerForm(request.POST, request.FILES, instance=customer)
		if form.is_valid():
			form.save()

	context={'customer':customer, 'form':form}
	return render(request, 'accounts/account_settings.html', context)


@login_required(login_url='login')
@admin_only
def home(request):
	orders = Order.objects.all()
	customers = Customer.objects.all()

	total_customers = customers.count()
	orders_in_stash = orders.filter(status='In the stash')
	total_orders = orders.count()
	delivered = orders.filter(status='Delivered').count()
	stash = orders_in_stash.count()
	on_cour = orders.filter(status='On the courier').count()

	
	context = {'orders':orders, 'customers':customers, 'orders_in_stash':orders_in_stash, 'total_orders':total_orders, 'delivered':delivered, 'stash':stash, 'on_cour':on_cour}
	return render(request, 'accounts/dashboard.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def products(request):
	products = Product.objects.all()
	return render(request, 'accounts/products.html', {'products':products})

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def customer(request, pk_test):
	customer = Customer.objects.get(id=pk_test)

	orders = customer.order_set.all()
	order_count = orders.count()

	myFilter = OrderFilter(request.GET, queryset=orders)
	orders = myFilter.qs

	context = {'customer':customer, 'orders': orders, 'order_count':order_count, 'myFilter':myFilter}
	return render(request, 'accounts/customer.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def create_order(request, pk):
	OrderFormSet = inlineformset_factory(Customer, Order, fields=('product','status'))
	customer = Customer.objects.get(id=pk)
	#form = OrderForm(initial={'customer':customer})
	formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
	if request.method == 'POST':
		formset = OrderFormSet(request.POST, queryset=Order.objects.none(), instance=customer)
		if formset.is_valid():
			formset.save()
			return redirect('/')

	context = {'formset':formset}
	return render(request, 'accounts/order_form.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def customer_create_order(request, pk):
	OrderFormSet = inlineformset_factory(Customer, Order, fields=('product',))
	customer = Customer.objects.get(id=pk)
	initial_val = 'In the stash'
	#form = OrderForm(initial={'customer':customer})
	formset = OrderFormSet(queryset=Order.objects.none(), instance=customer, initial=[{'status': initial_val}])
	if request.method == 'POST':
		formset = OrderFormSet(request.POST, queryset=Order.objects.none(), instance=customer)
		if formset.is_valid():
			formset.save()
			return redirect('user_page', str(customer.id))
			

	context = {'customer':customer, 'formset':formset}
	return render(request, 'accounts/customer_order_form.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def update_order(request, pk):

	order = Order.objects.get(id=pk)
	form = OrderForm(instance=order)
	context = {'form':form}

	if request.method == 'POST':
		form = OrderForm(request.POST, instance=order)
		if form.is_valid():
			form.save()
			return redirect('/')

	return render(request, 'accounts/update_order_form.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def delete_order(request, pk):
	order = Order.objects.get(id=pk)

	if request.method == "POST":
		order.delete()
		return redirect('/')

	context = {'item':order}

	return render(request, 'accounts/delete.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def print_order_report(request, *args, **kwargs):
	today = date.today()
	orders = Order.objects.all()
	customers = Customer.objects.all()
	total_orders = orders.count()
	template = get_template('accounts/order_report.html')
	
	context = {'orders':orders, 'customers':customers, 'total_orders':total_orders }

	html = template.render(context)
	pdf = render_to_pdf('accounts/order_report.html', context)

	if pdf:
		response = HttpResponse(pdf, content_type='application/pdf')
		filename = "Order_Report_%s.pdf" %(today)
		content = "attachment; filename=%s" %(filename)
		response['Content-Disposition'] = content
		return response

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def view_order_report(request, *args, **kwargs):
	today = date.today()
	orders = Order.objects.all()
	customers = Customer.objects.all()
	total_orders = orders.count()
	template = get_template('accounts/order_report.html')
	
	context = {'orders':orders, 'customers':customers, 'total_orders':total_orders }

	html = template.render(context)
	pdf = render_to_pdf('accounts/order_report.html', context)

	if pdf:
		response = HttpResponse(pdf, content_type='application/pdf')
		filename = "Order_Report_%s.pdf" %(today)
		content = "inline; filename=%s" %(filename)
		response['Content-Disposition'] = content
		return response
	#return HttpResponse(pdf, content_type='application/pdf')