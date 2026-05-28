from django.urls import path
from . import views
app_name = "projects"
urlpatterns = [
    path("list/", views.project_list_view, name="catalog"),
    path("create-project/", views.project_create_view, name="create"),
    path("<int:project_id>/", views.project_detail_view, name="detail"),
    path("<int:project_id>/edit/", views.project_edit_view, name="edit"),
    path("<int:project_id>/complete/", views.complete_project_view, name="complete"),
    path("<int:project_id>/toggle-participate/", views.toggle_participate_view, name="toggle_participate"),
    path("favorites/", views.favorites_view, name="favorites"),
    path("<int:project_id>/toggle-favorite/", views.toggle_favorite_view, name="toggle_favorite"),
]