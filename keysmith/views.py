from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import APITokenForm
from .models import APIToken


@login_required
def token_list(request):
    tokens = APIToken.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, "keysmith/token_list.html", {"tokens": tokens})

@login_required
def token_create(request):
    if request.method == "POST":
        form = APITokenForm(request.POST)
        if form.is_valid():
            token = form.save(commit=False)
            token.created_by = request.user
            # You'll call your utility here to generate and hash token
            # token.key, token.prefix, token.hint = generate_hashed_token()
            token.save()
            form.save_m2m()
            return redirect("keysmith:token_list")
    else:
        form = APITokenForm()
    return render(request, "keysmith/token_form.html", {"form": form})

@login_required
def token_detail(request, pk):
    token = get_object_or_404(APIToken, pk=pk, created_by=request.user)
    return render(request, "keysmith/token_detail.html", {"token": token})
