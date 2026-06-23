from rest_framework import status
from rest_framework.response import Response

class SoftDeleteMixin:
    """
    Mixin para ViewSets de Django REST Framework.
    Sobrescribe el método destroy para realizar soft-delete en lugar de eliminar físicamente.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()  # Llama al método delete() del modelo que marca deleted_at
        return Response(
            {'detail': f'{instance.__class__.__name__} eliminado (soft delete).'},
            status=status.HTTP_200_OK
        )
