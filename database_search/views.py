from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from database_subscription.models import DatabaseSubscription
from .forms import DatabaseSearchForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required

@login_required
def database_search(request):
    results = []
    form = DatabaseSearchForm()

    if request.GET:
        form = DatabaseSearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data.get('query')
            collection = form.cleaned_data.get('collection')
            publisher_conditions = form.cleaned_data.get('publisher_conditions')
            subscription_duration = form.cleaned_data.get('subscription_duration')

            queryset = DatabaseSubscription.objects.all()

            if query:
                queryset = queryset.filter(
                    Q(DB_Name__icontains=query) |
                    Q(DBJournal_List__icontains=query) |
                    Q(DBEBook_List__icontains=query)
                )
            if collection:
                queryset = queryset.filter(DB_Collection__icontains=collection)
            if publisher_conditions:
                queryset = queryset.filter(publisher_conditions__icontains=publisher_conditions)
            if subscription_duration:
                try:
                    year = int(subscription_duration)
                    queryset = queryset.filter(
                        Q(subscription_start_date__year=year) |
                        Q(subscription_end_date__year=year)
                    )
                except ValueError:
                    pass

            results = queryset.distinct()

    return render(request, 'database_search/database_search.html', {
        'form': form,
        'results': results
    })