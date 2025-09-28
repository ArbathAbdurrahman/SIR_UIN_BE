from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "ruang"

router = DefaultRouter()
router.register(r'locations', views.LocationViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'reservations', views.ReservationViewSet, basename='reservation')
router.register(r'feedback', views.FeedbackViewSet, basename='feedback')

urlpatterns = [
    path('', include(router.urls)),
]

# URL patterns yang akan dihasilkan:
# GET/POST    /api/locations/                 - List/Create locations (staff only untuk POST)
# GET/PUT/PATCH/DELETE /api/locations/{id}/   - Detail location (staff only untuk PUT/PATCH/DELETE)
# 
# GET/POST    /api/rooms/                     - List/Create rooms (staff only untuk POST)
# GET/PUT/PATCH/DELETE /api/rooms/{id}/       - Detail room (staff only untuk PUT/PATCH/DELETE)
# GET         /api/rooms/{id}/availability/   - Check room availability
#
# GET/POST    /api/reservations/              - List/Create reservations 
# GET/PUT/PATCH/DELETE /api/reservations/{id}/ - Detail reservation
# PATCH       /api/reservations/{id}/approve/ - Approve/decline reservation (staff only)
# GET         /api/reservations/my_reservations/ - User's own reservations
#
# GET/POST    /api/feedback/                  - List/Create feedback
# GET/PUT/PATCH/DELETE /api/feedback/{id}/    - Detail feedback
# GET         /api/feedback/my_feedback/      - User's own feedback

# Contoh filter parameters:
# Filter berdasarkan lokasi dan kapasitas
# GET /api/rooms/?location=Building A&min_capacity=10&max_capacity=50

# Filter availability saja
# GET /api/rooms/?available_from=2023-12-01T09:00:00Z&available_to=2023-12-01T17:00:00Z

# Kombinasi semua filter (seperti yang Anda minta)
# GET /api/rooms/?location=Building A&min_capacity=10&max_capacity=50&available_from=2023-12-01T09:00:00Z&available_to=2023-12-01T17:00:00Z

# Filter berdasarkan capacity saja
# GET /api/rooms/?min_capacity=20

# Filter berdasarkan lokasi saja (case-insensitive)
# GET /api/rooms/?location=building