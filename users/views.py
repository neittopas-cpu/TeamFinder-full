from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .forms import RegistrationForm, AuthForm, ProfileEditForm, PasswordUpdateForm
from .models import User

# Константы для фильтров
FILTER_OWNERS_OF_FAVORITE_PROJECTS = "owners-of-favorite-projects"
FILTER_OWNERS_OF_PARTICIPATING_PROJECTS = "owners-of-participating-projects"
FILTER_INTERESTED_IN_MY_PROJECTS = "interested-in-my-projects"
FILTER_PARTICIPANTS_OF_MY_PROJECTS = "participants-of-my-projects"

# Пагинация
PAGINATE_BY = 12


def paginate_queryset(request, queryset, per_page=PAGINATE_BY):
    """Возвращает страницу с объектами."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page", 1)
    return paginator.get_page(page_number)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("projects:catalog")

    if request.method == "POST":
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("projects:catalog")
    else:
        form = RegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:catalog")

    if request.method == "POST":
        form = AuthForm(request.POST or None)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            return redirect("projects:catalog")
    else:
        form = AuthForm()
    return render(request, "users/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("projects:catalog")


def user_list_view(request):
    qs = User.objects.all()  # сортировка из модели

    active_filter = request.GET.get("filter")
    if request.user.is_authenticated and active_filter:
        if active_filter == FILTER_OWNERS_OF_FAVORITE_PROJECTS:
            qs = User.objects.filter(owned_projects__in=request.user.favorites.all()).distinct()
        elif active_filter == FILTER_OWNERS_OF_PARTICIPATING_PROJECTS:
            qs = User.objects.filter(owned_projects__participants=request.user).distinct()
        elif active_filter == FILTER_INTERESTED_IN_MY_PROJECTS:
            qs = User.objects.filter(favorites__in=request.user.owned_projects.all()).distinct()
        elif active_filter == FILTER_PARTICIPANTS_OF_MY_PROJECTS:
            qs = User.objects.filter(participated_projects__in=request.user.owned_projects.all()).distinct()

    page_obj = paginate_queryset(request, qs)
    return render(request, "users/participants.html", {
        "participants": page_obj,
        "page_obj": page_obj,
        "active_filter": active_filter,
    })


def user_detail_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return render(request, "users/user-details.html", {"user": user})


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST or None, request.FILES or None, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:detail", user_id=request.user.pk)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordUpdateForm(request.user, request.POST or None)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password1"])
            request.user.save()
            update_session_auth_hash(request, request.user)
            return redirect("users:detail", user_id=request.user.pk)
    else:
        form = PasswordUpdateForm(request.user)
    return render(request, "users/change_password.html", {"form": form})