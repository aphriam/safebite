from django.urls import path
from .views import predict_food_allergy

urlpatterns = [
    path("predict/", predict_food_allergy, name="predict"),
]