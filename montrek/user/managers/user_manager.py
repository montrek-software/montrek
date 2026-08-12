from baseclasses.managers.montrek_manager import MontrekManager
from django.contrib.auth import get_user_model
from user.models import MontrekUser


class UserManager(MontrekManager):
    def get_superuser(self) -> MontrekUser:
        user_model = get_user_model()
        super_user = user_model.objects.filter(is_superuser=True).first()
        if super_user is None:
            raise ValueError("No superuser available!")
        return super_user
