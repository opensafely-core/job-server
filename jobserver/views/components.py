from django.shortcuts import render


def Components(request):
    return render(request, "_components/index.html")
