from datetime import datetime

from django.shortcuts import render


def Components(request):
    example_date = datetime.utcfromtimestamp(1667317153)
    return render(
        request,
        "_components/index.html",
        context={"example_date": example_date},
    )
