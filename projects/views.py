from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from .models import Project
from .forms import ProjectForm
from users.models import User

# Константы для статусов (синхронизированы с Project.Status)
PROJECT_STATUS_CLOSED = Project.Status.CLOSED
PROJECT_STATUS_OPEN = Project.Status.OPEN

# Константы для ответов
JSON_STATUS_OK = "ok"
JSON_STATUS_ERROR = "error"

# Вынесенная бизнес-логика (бывший метод is_open)
def is_project_open(project):
    return project.status == PROJECT_STATUS_OPEN

def project_list_view(request):
    qs = Project.objects.select_related("owner").prefetch_related("participants").all()
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "projects/project_list.html", {"projects": page_obj, "page_obj": page_obj, "query_prefix": ""})

def project_detail_view(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants"),
        pk=project_id
    )
    return render(request, "projects/project-details.html", {"project": project})

@login_required
def project_create_view(request):
    if request.method != "POST":
        form = ProjectForm()
        return render(request, "projects/create-project.html", {"form": form, "is_edit": False})

    form = ProjectForm(request.POST)
    if not form.is_valid():
        return render(request, "projects/create-project.html", {"form": form, "is_edit": False})

    proj = form.save(commit=False)
    proj.owner = request.user
    proj.save()
    proj.participants.add(request.user)
    return redirect("projects:detail", project_id=proj.pk)

@login_required
def project_edit_view(request, project_id):
    proj = get_object_or_404(Project, pk=project_id)
    if proj.owner != request.user:
        return JsonResponse({"status": JSON_STATUS_ERROR}, status=403)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=proj)
        if form.is_valid():
            form.save()
            return redirect("projects:detail", project_id=proj.pk)
    else:
        form = ProjectForm(instance=proj)

    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})

@login_required
@require_POST
def complete_project_view(request, project_id):
    from django.http import HttpResponseBadRequest
    proj = get_object_or_404(Project, pk=project_id)
    if proj.owner != request.user or not is_project_open(proj):
        return JsonResponse({"status": JSON_STATUS_ERROR}, status=400)

    proj.status = PROJECT_STATUS_CLOSED
    proj.save(update_fields=["status"])
    return JsonResponse({
        "status": JSON_STATUS_OK,
        "project_status": PROJECT_STATUS_CLOSED
    })

@login_required
@require_POST
def toggle_participate_view(request, project_id):
    proj = get_object_or_404(Project, pk=project_id)
    is_part = request.user in proj.participants.all()
    if is_part:
        proj.participants.remove(request.user)
    else:
        proj.participants.add(request.user)
    return JsonResponse({"status": JSON_STATUS_OK, "participant": not is_part})

@login_required
def favorites_view(request):
    qs = request.user.favorites.select_related("owner").prefetch_related("participants").all()
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "projects/favorite_projects.html", {"projects": page_obj})

@login_required
@require_POST
def toggle_favorite_view(request, project_id):
    proj = get_object_or_404(Project, pk=project_id)
    is_fav = request.user in proj.interested_users.all()
    if is_fav:
        request.user.favorites.remove(proj)
    else:
        request.user.favorites.add(proj)
    return JsonResponse({"status": JSON_STATUS_OK, "favorited": not is_fav})