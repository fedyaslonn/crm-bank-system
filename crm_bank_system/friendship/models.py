from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint, CheckConstraint, Q
from django.db.models import F

# Create your models here.


User = get_user_model()

class FriendshipManager(models.Manager):
    def create(self, user_from, user_to, status):
        friendship = self.model(
            user_from=user_from,
            user_to=user_to,
            status=status
        )

        friendship.save(using=self._db)
        return friendship

    def delete(self, friendship_id):
        try:
            friendship = self.get(id=friendship_id)
            friendship.delete()
            return {"status": "success", "friendship_id": friendship_id}

        except ObjectDoesNotExist:
            raise ValueError(f"Дружба с ID {friendship_id} не найдена.")

    def delete_friendship(self, user_from, user_to):
        try:
            friendship = self.get(Q(user_from=user_from, user_to=user_to) | Q(user_from=user_to, user_to=user_from))
            friendship.delete()
            return {"status": "success"}

        except ObjectDoesNotExist:
            return {"status": "error", "message": f"Дружба между {user_from} и {user_to} не найдена."}


class Friendship(models.Model):
    from users.models import CustomUser

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    user_from = models.ForeignKey(User, related_name='friendships_initiated', on_delete=models.CASCADE)
    user_to = models.ForeignKey(CustomUser, related_name='friendships_received', on_delete=models.CASCADE)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Статус дружбы"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FriendshipManager()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user_from', 'user_to'], name='unique_friendship'),
            CheckConstraint(
                check=~Q(user_from=F('user_to')),
                name='prevent_self_frienship'
            )
        ]

        verbose_name = "Дружба"
        verbose_name_plural = "Дружбы"
        ordering = ["-created_at"]
        db_table = "Frienship"


    def __str__(self):
        return f"{self.user_from.username} - {self.user_to.username}"