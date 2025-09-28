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
# /api/rooms/?location=Building A&min_capacity=10&max_capacity=50
# /api/rooms/?available_from=2023-12-01T09:00:00Z&available_to=2023-12-01T17:00:00Z
# /api/reservations/?status=APPROVED&room__location=1
# /api/feedback/?rating=5&reservation__room__location=1