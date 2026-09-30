from .permissions import eh_organizador


def papeis(request):
    return {"usuario_eh_organizador": eh_organizador(request.user)}
