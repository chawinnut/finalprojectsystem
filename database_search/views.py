from django.shortcuts import render
from database_subscription.models import DatabaseSubscription, CollectionDetail
from .forms import DatabaseSearchForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required

@login_required
def database_search(request):
    results = []
    form = DatabaseSearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        collection = form.cleaned_data.get('collection')
        subscription_year = form.cleaned_data.get('subscription_year')

        queryset = DatabaseSubscription.objects.all()

        if query:
            queryset = queryset.filter(
                Q(DB_Name__icontains=query) |
                Q(collection_details__collection_name__icontains=query)
            ).distinct()

        if collection:
            queryset = queryset.filter(collection_details__collection_name__icontains=collection).distinct()

        if subscription_year:
            try:
                year = int(subscription_year)
                queryset = queryset.filter(renewal_year=year).distinct()
            except ValueError:
                pass

        results = list(queryset)

    return render(request, 'database_search/database_search.html', {
        'form': form,
        'results': results
    })