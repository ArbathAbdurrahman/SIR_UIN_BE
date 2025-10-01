from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Location, Room, Reservation, Feedback

User = get_user_model()


class LocationViewSetTest(APITestCase):
    """Test LocationViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass123'
        )
        self.location = Location.objects.create(
            name='Main Building',
            address='123 Main St'
        )
    
    def test_list_locations_unauthenticated(self):
        """Unauthenticated users can view locations"""
        response = self.client.get('/api/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_locations_authenticated(self):
        """Authenticated users can view locations"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_location_as_staff(self):
        """Staff can create locations"""
        self.client.force_authenticate(user=self.staff_user)
        data = {
            'name': 'New Building',
            'address': '456 New St'
        }
        response = self.client.post('/api/locations/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Location.objects.count(), 2)
    
    def test_create_location_as_regular_user(self):
        """Regular users cannot create locations"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'name': 'New Building',
            'address': '456 New St'
        }
        response = self.client.post('/api/locations/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_location_as_staff(self):
        """Staff can update locations"""
        self.client.force_authenticate(user=self.staff_user)
        data = {'name': 'Updated Building'}
        response = self.client.patch(f'/api/locations/{self.location.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.location.refresh_from_db()
        self.assertEqual(self.location.name, 'Updated Building')
    
    def test_delete_location_as_staff(self):
        """Staff can delete locations"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(f'/api/locations/{self.location.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Location.objects.count(), 0)
    
    def test_search_locations(self):
        """Test location search functionality"""
        Location.objects.create(name='Tech Hub', address='789 Tech Ave')
        response = self.client.get('/api/locations/?search=Tech')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class RoomViewSetTest(APITestCase):
    """Test RoomViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass123'
        )
        self.location = Location.objects.create(
            name='Main Building',
            address='123 Main St'
        )
        self.room = Room.objects.create(
            name='Conference Room A',
            location=self.location,
            capacity=10
        )
    
    def test_list_rooms(self):
        """Test listing rooms"""
        response = self.client.get('/api/rooms/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_room_as_staff(self):
        """Staff can create rooms"""
        self.client.force_authenticate(user=self.staff_user)
        data = {
            'name': 'Meeting Room B',
            'location': self.location.id,
            'capacity': 8
        }
        response = self.client.post('/api/rooms/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Room.objects.count(), 2)
    
    def test_create_room_as_regular_user(self):
        """Regular users cannot create rooms"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'name': 'Meeting Room B',
            'location': self.location.id,
            'capacity': 8
        }
        response = self.client.post('/api/rooms/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_filter_rooms_by_location(self):
        """Test filtering rooms by location"""
        response = self.client.get(f'/api/rooms/?location={self.location.name}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_rooms_by_capacity(self):
        """Test filtering rooms by capacity"""
        Room.objects.create(name='Small Room', location=self.location, capacity=5)
        response = self.client.get('/api/rooms/?min_capacity=8')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_room_availability_endpoint(self):
        """Test room availability check"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        
        response = self.client.get(
            f'/api/rooms/{self.room.id}/availability/',
            {
                'start': start.isoformat(),
                'end': end.isoformat()
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
    
    def test_room_availability_with_conflict(self):
        """Test room availability with conflicting reservation"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        
        # Create approved reservation
        Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=end,
            purpose='Test Meeting',
            status='APPROVED'
        )
        
        response = self.client.get(
            f'/api/rooms/{self.room.id}/availability/',
            {
                'start': start.isoformat(),
                'end': end.isoformat()
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['available'])
    
    def test_room_availability_missing_parameters(self):
        """Test availability endpoint with missing parameters"""
        response = self.client.get(f'/api/rooms/{self.room.id}/availability/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_filter_available_rooms(self):
        """Test filtering available rooms"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        
        # Create another room
        room2 = Room.objects.create(
            name='Conference Room B',
            location=self.location,
            capacity=15
        )
        
        # Book first room
        Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=end,
            purpose='Test Meeting',
            status='APPROVED'
        )
        
        response = self.client.get(
            '/api/rooms/',
            {
                'available_from': start.isoformat(),
                'available_to': end.isoformat()
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Room 2 should be available, room 1 should not
        room_ids = [r['id'] for r in response.data]
        self.assertIn(room2.id, room_ids)
        self.assertNotIn(self.room.id, room_ids)


class ReservationViewSetTest(APITestCase):
    """Test ReservationViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )
        self.location = Location.objects.create(
            name='Main Building',
            address='123 Main St'
        )
        self.room = Room.objects.create(
            name='Conference Room A',
            location=self.location,
            capacity=10
        )
    
    def test_create_reservation(self):
        """User can create reservation"""
        self.client.force_authenticate(user=self.regular_user)
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        
        data = {
            'room': self.room.id,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'purpose': 'Team Meeting'
        }
        response = self.client.post('/api/reservations/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
    
    def test_list_reservations_as_regular_user(self):
        """Regular users only see their own reservations"""
        self.client.force_authenticate(user=self.regular_user)
        start = timezone.now() + timedelta(days=1)
        
        # Create reservation for regular user
        Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=start + timedelta(hours=1),
            purpose='My Meeting'
        )
        
        # Create reservation for other user
        Reservation.objects.create(
            room=self.room,
            requester=self.other_user,
            start=start + timedelta(hours=2),
            end=start + timedelta(hours=3),
            purpose='Other Meeting'
        )
        
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_list_reservations_as_staff(self):
        """Staff users see all reservations"""
        self.client.force_authenticate(user=self.staff_user)
        start = timezone.now() + timedelta(days=1)
        
        Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=start + timedelta(hours=1),
            purpose='User Meeting'
        )
        
        Reservation.objects.create(
            room=self.room,
            requester=self.other_user,
            start=start + timedelta(hours=2),
            end=start + timedelta(hours=3),
            purpose='Other Meeting'
        )
        
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_approve_reservation_as_staff(self):
        """Staff can approve reservations"""
        self.client.force_authenticate(user=self.staff_user)
        start = timezone.now() + timedelta(days=1)
        
        reservation = Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=start + timedelta(hours=1),
            purpose='Meeting'
        )
        
        response = self.client.patch(
            f'/api/reservations/{reservation.id}/approve/',
            {'status': 'APPROVED'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'APPROVED')
    
    def test_approve_reservation_as_regular_user(self):
        """Regular users cannot approve reservations"""
        self.client.force_authenticate(user=self.regular_user)
        start = timezone.now() + timedelta(days=1)
        
        reservation = Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=start + timedelta(hours=1),
            purpose='Meeting'
        )
        
        response = self.client.patch(
            f'/api/reservations/{reservation.id}/approve/',
            {'status': 'APPROVED'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_approve_with_conflict(self):
        """Cannot approve reservation with time conflict"""
        self.client.force_authenticate(user=self.staff_user)
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        
        # Create approved reservation
        Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=end,
            purpose='First Meeting',
            status='APPROVED'
        )
        
        # Create pending reservation with overlap
        reservation2 = Reservation.objects.create(
            room=self.room,
            requester=self.other_user,
            start=start + timedelta(minutes=30),
            end=end + timedelta(minutes=30),
            purpose='Second Meeting'
        )
        
        response = self.client.patch(
            f'/api/reservations/{reservation2.id}/approve/',
            {'status': 'APPROVED'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_decline_reservation(self):
        """Staff can decline reservations"""
        self.client.force_authenticate(user=self.staff_user)
        start = timezone.now() + timedelta(days=1)
        
        reservation = Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=start + timedelta(hours=1),
            purpose='Meeting'
        )
        
        response = self.client.patch(
            f'/api/reservations/{reservation.id}/approve/',
            {'status': 'DECLINED'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'DECLINED')
    
    def test_my_reservations_endpoint(self):
        """Test my_reservations custom action"""
        self.client.force_authenticate(user=self.regular_user)
        start = timezone.now() + timedelta(days=1)
        
        Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=start + timedelta(hours=1),
            purpose='My Meeting'
        )
        
        response = self.client.get('/api/reservations/my_reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_filter_reservations_by_status(self):
        """Test filtering reservations by status"""
        self.client.force_authenticate(user=self.staff_user)
        start = timezone.now() + timedelta(days=1)
        
        Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start,
            end=start + timedelta(hours=1),
            purpose='Pending Meeting',
            status='PENDING'
        )
        
        Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=start + timedelta(hours=2),
            end=start + timedelta(hours=3),
            purpose='Approved Meeting',
            status='APPROVED'
        )
        
        response = self.client.get('/api/reservations/?status=APPROVED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class FeedbackViewSetTest(APITestCase):
    """Test FeedbackViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )
        self.location = Location.objects.create(
            name='Main Building',
            address='123 Main St'
        )
        self.room = Room.objects.create(
            name='Conference Room A',
            location=self.location,
            capacity=10
        )
        self.reservation = Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=timezone.now() - timedelta(days=1),
            end=timezone.now() - timedelta(hours=23),
            purpose='Past Meeting',
            status='APPROVED'
        )
    
    def test_create_feedback(self):
        """User can create feedback"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'reservation': self.reservation.id,
            'rating': 5,
            'text': 'Great room!'
        }
        response = self.client.post('/api/feedback/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 1)
    
    def test_list_feedback(self):
        """Test listing feedback"""
        self.client.force_authenticate(user=self.regular_user)
        
        Feedback.objects.create(
            user=self.regular_user,
            reservation=self.reservation,
            rating=5,
            text='Excellent'
        )
        
        response = self.client.get('/api/feedback/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_my_feedback_endpoint(self):
        """Test my_feedback custom action"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Create feedback for regular user
        Feedback.objects.create(
            user=self.regular_user,
            reservation=self.reservation,
            rating=5,
            text='My feedback'
        )
        
        # Create feedback for other user
        other_reservation = Reservation.objects.create(
            room=self.room,
            requester=self.other_user,
            start=timezone.now() - timedelta(days=2),
            end=timezone.now() - timedelta(days=2, hours=-1),
            purpose='Other Meeting',
            status='APPROVED'
        )
        
        Feedback.objects.create(
            user=self.other_user,
            reservation=other_reservation,
            rating=4,
            text='Other feedback'
        )
        
        response = self.client.get('/api/feedback/my_feedback/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['text'], 'My feedback')
    
    def test_filter_feedback_by_rating(self):
        """Test filtering feedback by rating"""
        self.client.force_authenticate(user=self.regular_user)
        
        Feedback.objects.create(
            user=self.regular_user,
            reservation=self.reservation,
            rating=5,
            text='Excellent'
        )
        
        other_reservation = Reservation.objects.create(
            room=self.room,
            requester=self.regular_user,
            start=timezone.now() - timedelta(days=2),
            end=timezone.now() - timedelta(days=2, hours=-1),
            purpose='Another Meeting',
            status='APPROVED'
        )
        
        Feedback.objects.create(
            user=self.regular_user,
            reservation=other_reservation,
            rating=3,
            text='Average'
        )
        
        response = self.client.get('/api/feedback/?rating=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_update_own_feedback(self):
        """User can update their own feedback"""
        self.client.force_authenticate(user=self.regular_user)
        
        feedback = Feedback.objects.create(
            user=self.regular_user,
            reservation=self.reservation,
            rating=4,
            text='Good'
        )
        
        response = self.client.patch(
            f'/api/feedback/{feedback.id}/',
            {'text': 'Updated feedback'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        feedback.refresh_from_db()
        self.assertEqual(feedback.text, 'Updated feedback')
    
    def test_cannot_update_others_feedback(self):
        """User cannot update other users' feedback"""
        self.client.force_authenticate(user=self.other_user)
        
        feedback = Feedback.objects.create(
            user=self.regular_user,
            reservation=self.reservation,
            rating=4,
            text='Good'
        )
        
        response = self.client.patch(
            f'/api/feedback/{feedback.id}/',
            {'text': 'Trying to update'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_staff_can_delete_feedback(self):
        """Staff can delete any feedback"""
        self.client.force_authenticate(user=self.staff_user)
        
        feedback = Feedback.objects.create(
            user=self.regular_user,
            reservation=self.reservation,
            rating=4,
            text='Good'
        )
        
        response = self.client.delete(f'/api/feedback/{feedback.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Feedback.objects.count(), 0)