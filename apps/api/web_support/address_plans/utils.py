def get_electricity_plans(address):
    city = address.town_city.strip().lower()

    if city == "auckland":
        standard_daily_charge = 1.50
        standard_variable_charge = 0.14
    elif city == "wellington":
        standard_daily_charge = 1.20
        standard_variable_charge = 0.12
    elif city == "christchurch":
        standard_daily_charge = 1.00
        standard_variable_charge = 0.10
    else:
        standard_daily_charge = 1.00
        standard_variable_charge = 0.10

    low_user_daily_charge = 0.30
    low_user_variable_charge = standard_variable_charge + 0.02

    return [
        {
            "id": 1,
            "name": "Fixed Price Plan",
            "description": "Fixed daily and variable charges for predictable billing.",
            "term": "12 Month",
            "terms_url": "/legal/power/fixed",
            "rate": round(standard_daily_charge * 30, 2),
            "rate_details": f"Fixed monthly fee for electricity in {city.capitalize()}",
            "charges": {
                "standard": {
                    "daily_charge": {"amount": standard_daily_charge, "unit": "$/day"},
                    "variable_charge": {"amount": standard_variable_charge, "unit": "$/kWh"}
                },
                "lowUser": {
                    "daily_charge": {"amount": low_user_daily_charge, "unit": "$/day"},
                    "variable_charge": {"amount": low_user_variable_charge, "unit": "$/kWh"}
                }
            }
        },
        {
            "id": 2,
            "name": "TOU Plan",
            "description": "Save during off-peak hours with flexible pricing.",
            "term": "12 Month",
            "terms_url": "/legal/power/tou",
            "rate": round(standard_daily_charge * 30 + 5.00, 2),
            "rate_details": f"Peak: $0.12/kWh, Off-Peak: $0.08/kWh in {city.capitalize()}",
            "charges": {
                "standard": {
                    "daily_charge": {"amount": standard_daily_charge, "unit": "$/day"},
                    "peak_charge": {"amount": 0.12, "unit": "$/kWh"},
                    "off_peak_charge": {"amount": 0.08, "unit": "$/kWh"}
                },
                "lowUser": {
                    "daily_charge": {"amount": low_user_daily_charge, "unit": "$/day"},
                    "peak_charge": {"amount": 0.14, "unit": "$/kWh"},
                    "off_peak_charge": {"amount": 0.10, "unit": "$/kWh"}
                }
            }
        },
        {
            "id": 3,
            "name": "Spot Plan",
            "description": "Track wholesale rates and benefit from low usage times.",
            "term": "Open Term",
            "terms_url": "/legal/power/spot",
            "rate": round(standard_daily_charge * 30 + 10.00, 2),
            "rate_details": f"Spot pricing model for {city.capitalize()}",
            "charges": {
                "standard": {
                    "daily_charge": {"amount": standard_daily_charge, "unit": "$/day"},
                    "wholesale_rate": {"amount": 0.10, "unit": "$/kWh"},
                    "network_charge": {"amount": 0.05, "unit": "$/kWh"}
                },
            }
        }
    ]


def get_broadband_plans(address):
    city = address.town_city.strip().lower()

    if city == "auckland":
        monthly_charge = 79.99
    elif city == "hamilton":
        monthly_charge = 69.99
    elif city == "tauranga":
        monthly_charge = 59.99
    else:
        monthly_charge = 49.99

    return [
        {
            "id": 101,
            "name": "Fibre Broadband",
            "description": "Unlimited broadband with fast fibre speeds.",
            "term": "12 Month",
            "terms_url": "/legal/broadband/fibre",
            "rate": round(monthly_charge, 2),
            "rate_details": f"Fixed monthly charge for broadband in {city.capitalize()}",
            "charges": {
                "monthly_charge": monthly_charge
            }
        },
        {
            "id": 102,
            "name": "Fixed Wireless",
            "description": "Reliable connectivity over wireless, ideal for urban areas.",
            "term": "Open Term",
            "terms_url": "/legal/broadband/wireless",
            "rate": round(monthly_charge + 10.00, 2),
            "rate_details": f"Peak and Off-Peak rates in {city.capitalize()}",
            "charges": {
                "monthly_charge": monthly_charge
            }
        },
        {
            "id": 103,
            "name": "Rural Broadband",
            "description": "Stay connected in rural zones with wider coverage.",
            "term": "Open Term",
            "terms_url": "/legal/broadband/rural",
            "rate": round(monthly_charge + 15.00, 2),
            "rate_details": f"Spot broadband pricing with network charges in {city.capitalize()}",
            "charges": {
                "monthly_charge": monthly_charge
            }
        }
    ]
