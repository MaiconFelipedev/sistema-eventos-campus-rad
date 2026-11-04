from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from rest_framework.permissions import BasePermission


def eh_organizador(user):
    return user.is_authenticated and user.groups.filter(name="Organizadores").exists()


class OrganizadorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return eh_organizador(self.request.user)


class EhOrganizador(BasePermission):
    """Permite escrita apenas para usuários do grupo Organizadores."""

    message = "Apenas organizadores podem realizar esta operação."

    def has_permission(self, request, view):
        return eh_organizador(request.user)


class EhOrganizadorDoObjeto(BasePermission):
    """Protege Evento e Atividade sem confiar em dados enviados pelo cliente."""

    message = "Você não pode alterar um recurso de outro organizador."

    def has_object_permission(self, request, view, obj):
        organizador_id = getattr(obj, "organizador_id", None)
        if organizador_id is None and hasattr(obj, "evento"):
            organizador_id = obj.evento.organizador_id
        return organizador_id == request.user.id
