from django.contrib import admin
from django.urls import path
from .views import SetupView, GridView, NextView, RobotView

urlpatterns = [
    path("setup/", SetupView.as_view()),   # POST /api/setup/
    path("grid/",  GridView.as_view()),    # GET  /api/grid/
    path("next/",  NextView.as_view()),    # GET  /api/next/  (play step by step)
    path("robot/",  RobotView.as_view()),    # GET  /api/robot/ (what robots see)
]
