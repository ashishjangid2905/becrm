from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.SimpleRouter()

router.register(r"labels", BranchLabelViewset, basename="branch-label")

urlpatterns = [path("", include(router.urls))]
