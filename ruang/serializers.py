from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Location, Room, Reservation, Feedback


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address']


class RoomSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'name', 'location', 'location_name', 'capacity', 'rating']

    def get_rating(self, obj):
        return obj.get_average_rating()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ReservationSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.username', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    location_name = serializers.CharField(source='room.location.name', read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'requester', 'requester_name', 'room', 'room_name', 
            'location_name', 'start', 'end', 'purpose', 'requested_capacity',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['requester', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Set requester dari user yang login
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)


class ReservationApprovalSerializer(serializers.ModelSerializer):
    """Serializer khusus untuk approval/decline reservasi"""
    class Meta:
        model = Reservation
        fields = ['status']


class FeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    reservation_room = serializers.CharField(source='reservation.room.name', read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'user', 'user_name', 'reservation', 'reservation_room',
            'rating', 'text', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        # Set user dari user yang login
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate_reservation(self, value):
        """Validasi bahwa user hanya bisa memberikan feedback untuk reservasi mereka sendiri"""
        user = self.context['request'].user
        if value.requester != user:
            raise serializers.ValidationError("You can only give feedback for your own reservations.")
        if value.status != 'APPROVED':
            raise serializers.ValidationError("You can only give feedback for approved reservations.")
        return value