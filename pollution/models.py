from django.db import models

from config.settings import AUTH_USER_MODEL


class PollutionPoint(models.Model):
    """Точка загрязнения на карте."""

    TYPE_CHOICES = (
        ('trash', 'Бытовой мусор'),
        ('oil', 'Нефтяное пятно'),
        ('industrial', 'Промышленные отходы'),
        ('plastic', 'Пластик'),
        ('other', 'Другое'),
    )

    STATUS_CHOICES = (
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('cleaned', 'Очищено'),
    )

    reporter = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pollution_reports'
    )
    pollution_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    photo = models.ImageField(upload_to='pollution_photos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_pollution_type_display()} ({self.latitude}, {self.longitude})"


class Comment(models.Model):
    """Комментарий от пользователей (НКО, волонтёров и т.д.)"""
    point = models.ForeignKey(PollutionPoint, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    photo = models.ImageField(upload_to='comment_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on point {self.point.id}"
