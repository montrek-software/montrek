from user.models import MontrekUser


class MontrekUserRepository:
    def std_queryset(self):
        return MontrekUser.objects.all()
