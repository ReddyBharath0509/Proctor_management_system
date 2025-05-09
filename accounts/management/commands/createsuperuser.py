from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a superuser with all required fields'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str)
        parser.add_argument('--email', type=str)
        parser.add_argument('--password', type=str)
        parser.add_argument('--role', type=str, default='admin')

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')
        role = options.get('role')

        if not username or not email or not password:
            self.stdout.write(self.style.ERROR('Username, email, and password are required'))
            return

        try:
            with transaction.atomic():
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    role=role,
                    address='',  # Empty string for address
                    phone_number=''  # Empty string for phone number
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {username}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}')) 