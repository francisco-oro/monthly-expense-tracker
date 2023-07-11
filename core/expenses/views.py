from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from django.template.loader import render_to_string
from rest_framework import status
from .models import *
from .serializers import *
import json
from userpreferences.models import UserPreferences
import datetime
import csv
import xlwt
from weasyprint import HTML
import tempfile
import pdb
# Create your views here.

def search_expenses(request):
     if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')

        expenses = Expense.objects.filter(
            amount__istartswith=search_str, owner = request.user) | Expense.objects.filter(
            date__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            description__icontains=search_str, owner=request.user) | Expense.objects.filter(
            category__icontains=search_str, owner= request.user)
        
        data = expenses.values()
        
        return JsonResponse(list(data), safe=False)


@login_required(login_url='/auth/login/')
def index(request):
    categories = Category.objects.all()
    expenses = Expense.objects.filter(owner=request.user)

    paginator = Paginator(expenses, 2)
    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)
    
    # User customized settings 

    try:
        currency = UserPreferences.objects.get(user=request.user).currency
    except ObjectDoesNotExist:
         messages.info(request, "Please take a moment to set your preferences at the account section")
         return redirect('preferences')


    context = {
          'expenses': expenses,
          "page_obj": page_obj,
          "currency": currency,
    }

    return render(request, 'expenses/index.html', context)

@login_required(login_url='/auth/login/')
def addExpense(request):

    categories = Category.objects.all()

    context = {
        'categories': categories,
        'values': request.POST
    }
    if request.method == "GET": 
        return render(request, 'expenses/add_expense.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['expense_date']
        try: 
            category = request.POST['category']
        except:
             messages.error(request, "Please add a valid category")
             return render(request, 'expenses/add_expense.html')
        

        if not amount: 
            messages.error(request, "Amount is required")
            return render(request, 'expenses/add_expense.html', context)
        
        if not description: 
            messages.error(request, "Description is required")
            return render(request, 'expenses/add_expense.html', context)
        
        try:
            Expense.objects.create(owner=request.user,amount=amount, date=date, category=category, description=description)
        
        except Exception as e:
                        messages.error(request, "Please enter a valid date")
                        return render(request, 'expenses/add_expense.html', context)
        
        messages.success(request, "Record inserted successfully")
        return redirect('expenses')
    
@login_required(login_url='/auth/login/')
def expense_edit(request, id):
     expense = Expense.objects.get(pk=id)
     categories = Category.objects.all()
     context = {
          'expense': expense,
          'values': expense,
          "categories": categories,
     }

     if request.method == 'GET':
          return render(request, 'expenses/edit-instance.html', context)
     
     if request.method == 'POST': 
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['expense_date']

        try: 
            category = request.POST['category']
        except:
             messages.error(request, "Please add a valid category")
             return render(request, 'expenses/edit-instance.html')
        

        if not amount: 
            messages.error(request, "Amount is required")
            return render(request, 'expenses/edit-instance.html', context)
        
        if not description: 
            messages.error(request, "Description is required")
            return render(request, 'expenses/edit-instance.html', context)
        
        
        if expense.owner != request.user:
             messages.error(request, 'This record belongs to another account')
             return render(request, 'expenses/edit-instance.html', context)

        expense.amount = amount
        expense.date = date
        expense.category = category
        expense.description = description

        try: 
            expense.save()
        except: 
            messages.error(request, "Please enter a valid date")
            return render(request, 'expenses/edit-instance.html', context)
         
        messages.success(request, "Record updated successfully")
        return redirect('expenses')
     
@login_required(login_url='/auth/login/')
def delete_expense(request, id):
     expense = Expense.objects.get(pk=id)
     if request.user == expense.owner: 
        if expense:
            expense.delete()
            messages.success(request, "Record succesfully removed")
            return redirect('expenses')
        
     messages.error(request, "Cannot delete that record")
     return redirect('expenses')

def expense_category_summary(request, opt):

     today = datetime.date.today()

     if opt == 1:
        one_week_ago = today - datetime.timedelta(days=7)
        start_from = one_week_ago

     elif opt == 2:
        one_month_ago = today - datetime.timedelta(days=30)
        start_from = one_month_ago

     elif opt == 3:
        four_months_ago = today - datetime.timedelta(days=30*4)
        start_from = four_months_ago
     
     elif opt == 4:
        six_months_ago = today - datetime.timedelta(days=30*6)
        start_from = six_months_ago
     
     elif opt == 5:
        one_year_ago = today - datetime.timedelta(days=365)
        start_from = one_year_ago
     else:
         return JsonResponse({"error", "Invalid option key"}, safe=False)


     expenses = Expense.objects.filter(date__gte = start_from, date__lte = today, owner=request.user)
     
     expenses_summary = {}

     def get_category(expense):
          return expense.category
    
     def get_expense_category_amount(expense):
          amount = 0
          
          filtered_by_category = Expense.objects.filter(category=category)
          for item in filtered_by_category:
               amount += item.amount
          return amount


     category_list = list(set(map(get_category, expenses)))

     for expense in expenses:
        for category in category_list:
             expenses_summary[category] = get_expense_category_amount(category)

     return JsonResponse(expenses_summary, safe=False)

def stats_view(request):
     return render(request, 'expenses/stats.html')


def timeline_expenses_tracker(request, opt):
    try:
        calendar = []
        today = datetime.datetime.today()
        start_from = today - datetime.timedelta(days=opt)
         
        expenses = Expense.objects.filter(date__gte=start_from, date__lte=today, owner=request.user)
        
        if opt >= 60:
            count = [0] * (opt // 30)

            for i in range(opt // 30):
                 
                 start_month = today - datetime.timedelta(days=(opt - (i * 30)))
                 end_month = today - datetime.timedelta(days=(opt - ((i + 1) * 30 - 1)))

                 monthly_expenses = expenses.filter(date__gte=start_month, date__lte=end_month)
                 total_expenses = monthly_expenses.aggregate(total_amount=Sum('amount'))['total_amount']

                 count[i] = total_expenses or 0
                 formatted_month = start_month.strftime("%B")
                 
                 calendar.append(formatted_month)
        
        else:
            count = [0] * opt
             
            for i in range(opt):    

                current_day_expenses = expenses.filter(date=start_from)
                count[i] = sum(expense.amount for expense in current_day_expenses)
                
                if opt >= 30:
                    formatted_date = start_from.strftime("%d/%m/%Y")
                else:
                    formatted_date = start_from.strftime("%A")
                calendar.append(formatted_date)
                start_from += datetime.timedelta(days=1)
         
        content = {
            'count': count,
            'tags': calendar
        }

        return JsonResponse(content)
    except Exception:
        return HttpResponse('You must provide a valid days count', status.HTTP_400_BAD_REQUEST)
    
    

def dashboard_view(request):
    return render(request, 'dashboard/stats.html')

def export_csv(request):
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment: filename = Expenses' + str(datetime.datetime.now()) + '.csv'

    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Category', 'Date'])

    expenses = Expense.objects.filter(owner=request.user)

    for expense in expenses:
        writer.writerow([expense.amount, expense.description, expense.category, expense.date])


def export_xlx(request):
    response = HttpResponse(content_type = 'application/mx-excel')
    response['Content-Disposition'] = 'attachment: filename = Expenses' + str(datetime.datetime.now()) + '.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Expenses')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Amount', 'Description', 'Category', 'Date']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    
    font_style = xlwt.XFStyle()

    rows = Expense.objects.filter(owner = request.user).values_list('amount', 'description', 'category', 'date')

    for row in rows:
        row_num += 1

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)
    
    return response

def export_pdf(request):
    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = 'attachment: filename = Expenses' + str(datetime.datetime.now()) + '.pdf'

    response['Content-Transfer-Encoding'] = 'binary'

    html_string = render_to_string('expenses/pdf-output.html', {'expenses': [], 'total': 0})
    html = HTML(string=html_string)
    
    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()


        output = open(output.name, 'rb')

        response.write(output.read())

    return response
