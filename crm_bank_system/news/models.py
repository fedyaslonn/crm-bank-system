from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.contrib.auth import get_user_model

from users.models import CustomUser

# Create your models here.

User = get_user_model()

class NewsManager(models.Manager):
    def create(self, title, content, authors, news_image):
        news = self.model(
            title=title,
            content=content,
            authors=authors,
            news_image=news_image
        )

        news.save(using=self._db)
        return news

    def like(self, news_id):
        try:
            news = self.get(id=news_id)
            news.likes_count += 1
            news.save(using=self._db)
            return news

        except ObjectDoesNotExist:
            raise ValueError(f"Новость с ID {news_id} не найдена.")


    def dislike(self, news_id):
        try:
            news = self.get(id=news_id)
            news.dislikes_count = F('likes_count') + 1
            news.save(using=self._db)
            return news

        except ObjectDoesNotExist:
            raise ValueError(f"Новость с ID {news_id} не найдена.")


    def delete(self, news_id):
        try:
            news = self.get(id=news_id)
            news.delete()
            return True

        except ObjectDoesNotExist:
            raise ValueError(f"Новость с ID {news_id} не найдена.")


    def delete_news(self, news_ids):
        if not news_ids:
            raise ValueError("Список ID новостей для удаления пуст.")

        try:
            deleted_count, _ = self.filter(id__in=news_ids).delete()
            return deleted_count

        except Exception as e:
            raise RuntimeError(f"Ошибка при удалении новостей: {str(e)}")


    def react(self, news_id, user, is_like):
        with transaction.atomic():
            news = self.get(id=news_id)

            reaction, created = UserReaction.objects.get_or_create(user=user, news=news)

            if not created and reaction.is_like == is_like:
                reaction.delete()

            else:
                reaction.is_like = is_like
                reaction.save()

            news.update_reactions()

            return {
                'likes_count': news.likes_count,
                'dislikes_count': news.dislikes_count
            }

    def __str__(self):
        return f"{self.title}"

class News(models.Model):
    from users.models import CustomUser
    title = models.CharField(max_length=40)
    content = models.TextField()
    authors = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)
    news_image = models.URLField(blank=True, help_text="Фото новости", null=True)

    objects = NewsManager()

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ["-created_at"]
        db_table = "News"

    def update_reaction(self):
        self.likes_count = self.reactions.filter(is_like=True).count()
        self.dislikes_count = self.reactions.filter(is_like=False).count()
        self.save()

    def __str__(self):
        return f"{self.title}"


class UserReaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="reactions")
    is_like = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'news')
        verbose_name = "Реакция пользователя"
        verbose_name_plural = "Реакции пользователей"
        db_table = "UserReaction"

class Comment(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["-created_at"]
        db_table = "Comments"
