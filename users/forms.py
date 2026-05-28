import re

from django import forms
from django.contrib.auth import authenticate

from .models import User


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]

    def clean_password(self):
        password = self.cleaned_data.get("password", "")
        if len(password) < 8:
            raise forms.ValidationError("Минимум 8 символов")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class AuthForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        user = authenticate(email=cleaned.get("email"), password=cleaned.get("password"))
        if not user:
            self.add_error(None, "Неверный email или пароль")
        else:
            cleaned["user"] = user
        return cleaned


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        widgets = {"about": forms.Textarea(attrs={"rows": 3})}

    def clean_phone(self):
        phone = re.sub(r'[\s\-\(\)]', '', self.cleaned_data.get("phone", ""))
        if not re.match(r'^(\+7|8)\d{10}$', phone):
            raise forms.ValidationError("Неверный формат телефона")
        normalized = "+7" + phone[1:] if phone.startswith("8") else phone
        qs = User.objects.filter(phone=normalized)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Номер уже зарегистрирован")
        return normalized

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if url and "github.com" not in url.lower():
            raise forms.ValidationError("Только ссылки на GitHub")
        return url


class PasswordUpdateForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput, min_length=8)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        if not self.user.check_password(self.cleaned_data.get("old_password")):
            raise forms.ValidationError("Текущий пароль неверен")
        return self.cleaned_data["old_password"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password1") != cleaned.get("new_password2"):
            raise forms.ValidationError("Пароли не совпадают")
        return cleaned