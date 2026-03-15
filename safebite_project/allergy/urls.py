from django.urls import path
from . import views

urlpatterns = [

    # ── Auth ──────────────────────────────────────
    path('auth/register/',  views.register,     name='register'),
    path('auth/login/',     views.login_view,    name='login'),
    path('auth/logout/',    views.logout_view,   name='logout'),

    # ── Dashboard ─────────────────────────────────
    path('dashboard/',      views.dashboard,     name='dashboard'),

    # ── Allergy Profile ───────────────────────────
    path('profile/',                              views.get_profile,    name='profile'),
    path('profile/add-allergy/',                  views.add_allergy,    name='add_allergy'),
    path('profile/delete-allergy/<int:allergy_id>/', views.delete_allergy, name='delete_allergy'),

    # ── Food Prediction ───────────────────────────
    path('predict/',        views.predict_food_allergy,  name='predict'),
    path('history/',        views.prediction_history,    name='history'),
    path('history/clear/',  views.clear_history,         name='clear_history'),

    # ── Medicine Checker ──────────────────────────
    path('medicine/check/',    views.check_medicine,       name='check_medicine'),
    path('medicine/history/',  views.medicine_history,     name='medicine_history'),
    path('medicine/history/clear/', views.clear_medicine_history, name='clear_medicine_history'),
    path('medicine/search/',   views.search_medicine_info, name='search_medicine'),

    # ── Drug Interaction Checker ──────────────────
    path('medicine/interactions/',         views.drug_interaction_check, name='drug_interactions'),
    path('medicine/interactions/history/', views.interaction_history,    name='interaction_history'),

    # ── Symptom Tracker ───────────────────────────
    path('symptoms/log/',     views.log_symptoms,    name='log_symptoms'),
    path('symptoms/history/', views.symptom_history, name='symptom_history'),
]
