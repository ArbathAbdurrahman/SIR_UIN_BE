from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.db.models import Q
from datetime import datetime

from .models import Location, Room, Reservation, Feedback
from .serializers import (
    LocationSerializer, RoomSerializer, ReservationSerializer, 
    ReservationApprovalSerializer, FeedbackSerializer
)
from siruinsk.utils.permissions import IsStaffOrReadOnly, IsOwnerOrStaffOrReadOnly, IsStaffForApproval


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'address']


class RoomFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(field_name='location__name', lookup_expr='icontains')
    min_capacity = django_filters.NumberFilter(field_name='capacity', lookup_expr='gte')
    max_capacity = django_filters.NumberFilter(field_name='capacity', lookup_expr='lte')
    available_from = django_filters.DateTimeFilter(method='filter_available_from')
    available_to = django_filters.DateTimeFilter(method='filter_available_to')
    
    class Meta:
        model = Room
        fields = ['location', 'capacity']
    
    def filter_available_from(self, queryset, name, value):
        # Filter room yang tidak ada reservasi yang approved pada waktu tersebut
        if hasattr(self, '_available_to') or 'available_to' in self.data:
            available_to = self._available_to if hasattr(self, '_available_to') else self.data.get('available_to')
            if available_to:
                # Exclude rooms yang punya reservasi approved yang overlap dengan waktu yang diminta
                conflicting_reservations = Reservation.objects.filter(
                    status='APPROVED',
                    start__lt=available_to,
                    end__gt=value
                ).values_list('room_id', flat=True)
                queryset = queryset.exclude(id__in=conflicting_reservations)
        
        self._available_from = value
        return queryset
    
    def filter_available_to(self, queryset, name, value):
        # Simpan nilai untuk digunakan di filter_available_from
        self._available_to = value
        return queryset


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related('location')
    serializer_class = RoomSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RoomFilter
    search_fields = ['name', 'location__name']
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Check room availability for specific time range"""
        room = self.get_object()
        start_time = request.query_params.get('start')
        end_time = request.query_params.get('end')
        
        if not start_time or not end_time:
            return Response(
                {'error': 'start and end query parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            return Response(
                {'error': 'Invalid datetime format. Use ISO format.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for conflicting approved reservations
        conflicting = Reservation.objects.filter(
            room=room,
            status='APPROVED',
            start__lt=end_dt,
            end__gt=start_dt
        ).exists()
        
        return Response({
            'room': room.id,
            'available': not conflicting,
            'checked_period': {
                'start': start_time,
                'end': end_time
            }
        })


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsOwnerOrStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'room', 'room__location']
    search_fields = ['purpose', 'room__name', 'room__location__name']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Reservation.objects.select_related('requester', 'room', 'room__location')
        else:
            return Reservation.objects.select_related('requester', 'room', 'room__location').filter(
                requester=self.request.user
            )
    
    @action(detail=True, methods=['patch'], permission_classes=[IsStaffForApproval])
    def approve(self, request, pk=None):
        """Approve atau decline reservasi (hanya untuk staff)"""
        reservation = self.get_object()
        serializer = ReservationApprovalSerializer(
            reservation, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            # Validasi tidak ada conflict jika approve
            if request.data.get('status') == 'APPROVED':
                conflicting = Reservation.objects.filter(
                    room=reservation.room,
                    status='APPROVED',
                    start__lt=reservation.end,
                    end__gt=reservation.start
                ).exclude(id=reservation.id).exists()
                
                if conflicting:
                    return Response(
                        {'error': 'Room is already booked for this time period'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_reservations(self, request):
        """Get reservasi milik user yang login"""
        reservations = self.get_queryset().filter(requester=request.user)
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)


class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsOwnerOrStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['rating', 'reservation__room', 'reservation__room__location']
    search_fields = ['text', 'reservation__room__name']
    
    def get_queryset(self):
        return Feedback.objects.select_related('user', 'reservation', 'reservation__room')
    
    @action(detail=False, methods=['get'])
    def my_feedback(self, request):
        """Get feedback yang dibuat oleh user yang login"""
        feedback = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(feedback, many=True)
        return Response(serializer.data)