from django.core.management.base import BaseCommand, CommandError
from users.models import CustomUser

class Command(BaseCommand):
    help = "Устанавливает зарплату пользователю по email"

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help="Email пользователя для установки ему зарплаты"
        )

        parser.add_argument(
            'salary',
            type=float,
            help="Зарплата, которую мы хотим установить"
        )

    def handle(self, *args, **kwargs):
        email = kwargs['email']
        salary = kwargs['salary']

        try:
            user = CustomUser.objects.get(email=email)
            user.salary = salary
            user.save()

            self.stdout.write(
            self.style.SUCCESS(f'Зарплата пользователя {email} успешно установлена на {salary}!')
            )

        except CustomUser.DoesNotExist:
            raise CommandError(f'Пользователь с email "{email}" не найден.')
