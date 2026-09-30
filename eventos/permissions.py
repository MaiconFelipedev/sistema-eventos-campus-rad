from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


def eh_organizador(user):
    return user.is_authenticated and user.groups.filter(name="Organizadores").exists()


class OrganizadorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return eh_organizador(self.request.user)
