from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

User = get_user_model()

class ReportManager(models.Manager):
    def create_report(self, report_dto):
        report = self.model(
            user=report_dto.user,
            description=report_dto.description,
            screenshot=report_dto.screenshot
        )
        report.save(using=self._db)
        return report

    def get_all(self):
        return self.all()

    def get_detail_report(self, id):
        return self.get(pk=id)

class Report(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    description = models.TextField(verbose_name="Описание проблемы")
    screenshot = models.URLField(blank=True, null=True, verbose_name="URL скриншота")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING',
                              verbose_name="Статус жалобы", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления", blank=True, null=True)
    document_url = models.URLField(blank=True, null=True, verbose_name="URL документа Word")
    admin_response = models.TextField(blank=True, null=True, verbose_name="Ответ администратора")

    objects = ReportManager()

    class Meta:
        verbose_name = "Жалоба"
        verbose_name_plural = "Жалобы"
        ordering = ["-created_at"]
        db_table = "Reports"