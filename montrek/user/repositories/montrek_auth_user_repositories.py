from user.models import MontrekUser


class MontrekUserRepository:
    def receive(self):
        return MontrekUser.objects.all()
