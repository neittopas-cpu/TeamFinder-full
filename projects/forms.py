from django import forms
from .models import Project

def validate_name_length(value, min_length=3):

    cleaned = value.strip() if isinstance(value, str) else value
    if len(cleaned) < min_length:
        raise forms.ValidationError(f"Минимум {min_length} символа")
    return cleaned

def validate_github_url(value):

    if value and "github.com" not in value.lower():
        raise forms.ValidationError("Укажите ссылку на репозиторий GitHub")
    return value

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_name(self):
        name = self.cleaned_data.get("name", "")
        return validate_name_length(name)

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        return validate_github_url(url)
