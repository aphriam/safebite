from django.db import models
from django.contrib.auth.models import User


# ═══════════════════════════════════════════
# USER ALLERGY PROFILE
# ═══════════════════════════════════════════

class UserAllergyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='allergy_profile')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class UserAllergy(models.Model):
    ITEM_TYPE_CHOICES = [
        ('food', 'Food'),
        ('medicine', 'Medicine'),
        ('other', 'Other'),
    ]
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('anaphylaxis', 'Anaphylaxis'),
    ]

    profile = models.ForeignKey(UserAllergyProfile, on_delete=models.CASCADE, related_name='allergies')
    allergen_name = models.CharField(max_length=200)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='food')
    symptoms = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='mild')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.allergen_name} ({self.severity})"

    class Meta:
        ordering = ['-severity', 'allergen_name']


# ═══════════════════════════════════════════
# FOOD PREDICTION HISTORY
# ═══════════════════════════════════════════

class PredictionHistory(models.Model):
    RISK_CHOICES = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    item_name = models.CharField(max_length=300)
    item_type = models.CharField(max_length=20, default='food')
    ingredients_text = models.TextField()
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES)
    confidence = models.FloatField()
    allergens_found = models.JSONField(default=list)
    matched_allergens = models.JSONField(default=list)
    alternatives = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.item_name} [{self.risk_level}]"

    class Meta:
        ordering = ['-created_at']


# ═══════════════════════════════════════════
# MEDICINE CHECK HISTORY
# ═══════════════════════════════════════════

class MedicineCheckHistory(models.Model):
    RISK_CHOICES = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicine_checks')
    medicine_name = models.CharField(max_length=300)
    ingredients_text = models.TextField(blank=True)
    drug_class = models.CharField(max_length=100, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES)
    confidence = models.FloatField(default=0)
    allergens_found = models.JSONField(default=list)
    matched_allergens = models.JSONField(default=list)
    alternative_medicines = models.JSONField(default=list)
    side_effects = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.medicine_name} [{self.risk_level}]"

    class Meta:
        ordering = ['-created_at']


# ═══════════════════════════════════════════
# DRUG INTERACTION CHECK HISTORY
# ═══════════════════════════════════════════

class DrugInteractionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drug_interactions')
    medicines_checked = models.JSONField(default=list)
    interactions_found = models.JSONField(default=list)
    total_interactions = models.IntegerField(default=0)
    is_safe = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.medicines_checked} [{self.total_interactions} interactions]"

    class Meta:
        ordering = ['-created_at']


# ═══════════════════════════════════════════
# SYMPTOM TRACKER
# ═══════════════════════════════════════════

class SymptomLog(models.Model):
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='symptom_logs')
    symptoms = models.JSONField(default=list)
    current_medicines = models.JSONField(default=list)
    recent_foods = models.TextField(blank=True)
    overall_severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='mild')
    possible_allergens = models.JSONField(default=list)
    medicine_warnings = models.JSONField(default=list)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.overall_severity} ({self.created_at.date()})"

    class Meta:
        ordering = ['-created_at']
