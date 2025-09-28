from rest_framework import permissions

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission untuk memastikan hanya staff yang bisa create/update/delete.
    User biasa hanya bisa read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_staff


class IsOwnerOrStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission untuk reservasi dan feedback.
    - Staff: full access
    - Owner: bisa edit/delete milik sendiri
    - User lain: hanya read
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions untuk semua authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Staff punya full access
        if request.user.is_staff:
            return True
        
        # Owner bisa edit/delete milik sendiri
        if hasattr(obj, 'requester'):  # Reservation
            return obj.requester == request.user
        elif hasattr(obj, 'user'):  # Feedback
            return obj.user == request.user
        
        return False


class IsStaffForApproval(permissions.BasePermission):
    """
    Permission khusus untuk approval reservasi - hanya staff
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff