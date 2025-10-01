from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Sum

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=100)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    capacity = models.PositiveIntegerField(default=0)

    def get_average_rating(self):
        """
        Menghitung rata-rata rating dari semua feedback terkait.
        Mengembalikan 0 jika belum ada feedback.
        """
        # Menghitung rata-rata rating menggunakan agregasi database
        avg_dict = Feedback.objects.filter(reservation__room=self).aggregate(average=Avg('rating'))
        average = avg_dict.get('average')

        if average is None:
            return 0.0
        
        return round(average,2)

    def __str__(self):
        return f"{self.name} ({self.location.name})"


class Reservation(models.Model):
    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    purpose = models.CharField(max_length=255)
    requested_capacity = models.PositiveIntegerField(default=0)

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("DECLINED", "Declined"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room.name} | {self.start:%Y-%m-%d %H:%M}"


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=0,validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.rating} for {self.reservation}"
