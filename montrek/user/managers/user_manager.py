from baseclasses.managers.montrek_manager import MontrekManager
from django.contrib.auth import get_user_model


class UserManager(MontrekManager):
    def get_superuser(self) -> None:
        user_model = get_user_model()
        return user_model.objects.filter(is_superuser=True).first()
