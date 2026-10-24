
import math
from datetime import datetime, timezone

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .mongodb import applications_collection


def home(request):
    context = {}

    if request.method == "POST":
        farmer_name = request.POST.get("farmer_name", "").strip()

        try:
            land_size_acres = float(request.POST.get("land_size_acres", ""))
            annual_income = float(request.POST.get("annual_income", ""))
            damage_pct = float(request.POST.get("damage_pct", ""))

            values = [land_size_acres, annual_income, damage_pct]

            if (
                not farmer_name
                or not all(math.isfinite(value) for value in values)
                or land_size_acres <= 0
                or annual_income < 0
                or not 0 <= damage_pct <= 100
            ):
                raise ValueError

        except (ValueError, TypeError):
            context["error"] = (
                "Please enter valid details. Land must be positive, "
                "income cannot be negative, and damage must be between 0 and 100%."
            )
            return render(request, "subsidy/home.html", context)

        # Check eligibility
        eligible = (
            land_size_acres <= 10
            and annual_income <= 1_500_000
            and damage_pct >= 20
        )

        status = "APPROVED" if eligible else "REJECTED"

        # Calculate subsidy only for eligible farmers
        calculated_subsidy = 0

        if eligible:
            base_relief = land_size_acres * 2000
            calculated_subsidy = round(
                min(base_relief * damage_pct / 100, 15000), 2
            )

        # Save the application in MongoDB
        application = {
            "farmer_name": farmer_name,
            "land_size_acres": land_size_acres,
            "annual_income": annual_income,
            "damage_pct": damage_pct,
            "status": status,
            "calculated_subsidy": calculated_subsidy,
            "created_at": datetime.now(timezone.utc),
        }

        applications_collection.insert_one(application)

        # Send the result to the website
        context["status"] = status
        context["calculated_subsidy"] = calculated_subsidy
        context["farmer_name"] = farmer_name
        context["message"] = (
            "Application approved!"
            if eligible
            else "Application rejected because one or more eligibility "
                 "conditions were not met."
        )

    return render(request, "subsidy/home.html", context)


@staff_member_required(login_url="/admin/login/")
def dashboard(request):
    applications = list(
        applications_collection.find().sort("created_at", -1)
    )

    return render(
        request,
        "subsidy/dashboard.html",
        {"applications": applications},
    )
