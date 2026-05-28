import io
import random
import re

from PIL import Image, ImageDraw, ImageFont
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models

# Константы длин полей
NAME_MAX_LENGTH = 124
SURNAME_MAX_LENGTH = 124
PHONE_MAX_LENGTH = 12
ABOUT_MAX_LENGTH = 256


def _generate_avatar(initial: str, size: int = 200) -> ContentFile:
    hue = random.randint(0, 360)
    saturation = random.uniform(0.45, 0.65)
    lightness = random.uniform(0.65, 0.80)

    c = (1 - abs(2 * lightness - 1)) * saturation
    x = c * (1 - abs((hue / 60) % 2 - 1))
    m = lightness - c / 2
    sectors = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)]
    r, g, b = [int((v + m) * 255) for v in sectors[hue // 60]]

    img = Image.new("RGB", (size, size), (r, g, b))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("Arial.ttf", size // 2)
    except IOError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initial.upper(), font=font)
    pos = ((size - (bbox[2] - bbox[0])) // 2, (size - (bbox[3] - bbox[1])) // 2 - 10)
    draw.text(pos, initial.upper(), fill="white", font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return ContentFile(buf.read(), name=f"avatar_{initial.lower()}.png")


class _PhoneHandler:
    @staticmethod
    def normalize(raw: str) -> str:
        cleaned = re.sub(r'[\s\-\(\)]', '', raw)
        if not re.match(r'^(\+7|8)\d{10}$', cleaned):
            raise ValidationError("Неверный формат: требуется +7XXXXXXXXXX или 8XXXXXXXXXX")
        return "+7" + cleaned[1:] if cleaned.startswith("8") else cleaned


class AccountManager(BaseUserManager):
    def create_user(self, email, name, surname, password=None, **extra):
        if not all([email, name, surname]):
            raise ValueError("Поля email, имя и фамилия обязательны")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name.strip(), surname=surname.strip(), **extra)
        user.set_password(password)
        user.avatar = _generate_avatar(name[0])
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, surname, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, name, surname, password, **extra)


class User(AbstractUser):
    username = None  # убираем поле username
    email = models.EmailField(unique=True, db_index=True, verbose_name="Электронная почта")
    name = models.CharField(max_length=NAME_MAX_LENGTH, verbose_name="Имя")
    surname = models.CharField(max_length=SURNAME_MAX_LENGTH, verbose_name="Фамилия")
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", verbose_name="Аватар")
    phone = models.CharField(max_length=PHONE_MAX_LENGTH, unique=True, verbose_name="Телефон")
    github_url = models.URLField(blank=True, null=True, verbose_name="GitHub")
    about = models.TextField(max_length=ABOUT_MAX_LENGTH, blank=True, verbose_name="О себе")
    favorites = models.ManyToManyField(
        "projects.Project",
        related_name="interested_users",
        blank=True,
        verbose_name="Избранные проекты"
    )

    objects = AccountManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "Участник"
        verbose_name_plural = "Участники"

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        self.phone = _PhoneHandler.normalize(self.phone)
        if self.github_url and "github.com" not in self.github_url.lower():
            raise ValidationError({"github_url": "Разрешены только ссылки на github.com"})
        super().save(*args, **kwargs)