# address_plans/plans.py

def get_electricity_plans():
    return [
        {
            "id": "wholesale-price",
            "name": "Wholesale Price",
            "description": "Pay real-time market rates. Ideal for low-usage users."
        },
        {
            "id": "fixed-price",
            "name": "Fixed Price",
            "description": "Flat rate per kWh. Predictable billing."
        }
    ]

def get_broadband_plans():
    return [
        {
            "id": "fibre",
            "name": "Fibre",
            "description": "High-speed reliable connection."
        },
        {
            "id": "wireless",
            "name": "Fixed Wireless",
            "description": "Broadband without fibre. Easy setup."
        }
    ]
