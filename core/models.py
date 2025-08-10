from django.db import models
from django.contrib.auth.models import User
class Train(models.Model):
    number = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.number} - {self.name}"
    
class Coach(models.Model):
    COACH_TYPES = [
        ('SL', 'Sleeper'),
        ('3A', 'AC 3-Tier'),
        ('2A', 'AC 2-Tier'),
        ('1A', 'AC First Class'),
        ('GEN', 'General'),
        ('CC', 'Chair Car'),
        ('EC', 'Executive Chair Car'),
    ]
    coach_number = models.CharField(max_length=10)
    coach_type = models.CharField(max_length=10, choices=COACH_TYPES, default='SL')
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='coaches')
    def __str__(self):
        return f"{self.coach_number} ({self.get_coach_type_display()}) - {self.train}"

class Defect(models.Model):
    DEFECT_CHOICES = [
        ('Light', 'Light Not Working'),
        ('Fan', 'Fan Not Working'),
        ('Window', 'Broken Window'),
        ('Seat', 'Seat Damaged'),
        ('Other', 'Other'),
    ]
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    defect_type = models.CharField(max_length=100, choices=DEFECT_CHOICES)
    custom_defect_text = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='defect_images/', blank=True, null=True)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_reported = models.DateTimeField(auto_now_add=True)
    status = models.CharField(default='Pending', max_length=100)

    def __str__(self):
        return f"{self.coach.coach_number} - {self.defect_type} ({self.reported_by.username})"
    
class PassengerProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    def __str__(self):
        return self.user.username
