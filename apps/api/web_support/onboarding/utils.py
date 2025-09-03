"""
Utilities for the onboarding process.
"""

from users.models import User

# Define the sequence of onboarding steps. This must be kept in sync with the frontend.
ONBOARDING_STEPS = [
    {"id": "aboutYou", "name": "About You"},
    {"id": "yourServices", "name": "Your Services"},
    {"id": "serviceDetails", "name": "Service Details"},
    {"id": "howYoullPay", "name": "How You'll Pay"},
    {"id": "preferences", "name": "Preferences"},
    {"id": "confirmSubmit", "name": "Confirm & Submit"},
]

def is_step_complete(step_id, data, user_details):
    """
    Checks if a specific onboarding step is complete based on the provided data.
    """
    # Helper to get value from step-specific data or fall back to global user details
    def get_val(step_data, key, default=None):
        return step_data.get(key, user_details.get(key, default))

    if step_id == "aboutYou":
        about_you_data = data.get("aboutYou", {})
        # Check for contact information within the 'aboutYou' step data
        has_email = bool(get_val(about_you_data, "email"))
        has_phone = bool(get_val(about_you_data, "phone") or get_val(about_you_data, "mobile"))
        return has_email or has_phone

    elif step_id == "yourServices":
        your_services_data = data.get("yourServices", {})
        # Check if at least one service and one plan is selected
        has_services = your_services_data.get("services") and any(your_services_data["services"].values())
        has_plans = your_services_data.get("plans") and len(your_services_data["plans"]) > 0
        return has_services and has_plans

    elif step_id == "serviceDetails":
        # Assumes if the key exists and is not empty, it's sufficiently complete
        return "serviceDetails" in data and bool(data["serviceDetails"])

    elif step_id == "howYoullPay":
        how_youll_pay_data = data.get("howYoullPay", {})
        # Check if payment method is selected and details are provided if needed
        payment_method = how_youll_pay_data.get("payment_method")
        if not payment_method:
            return False
        if payment_method == "bank_account":
            bank_details = how_youll_pay_data.get("bank_details", {})
            return all(bank_details.get(k) for k in ["account_name", "account_number"])
        return True  # For other methods like 'credit_card'

    elif step_id == "preferences":
        preferences_data = data.get("preferences", {})
        # Check if communication and billing preferences are set
        return "communication_preference" in preferences_data and "billing_preference" in preferences_data


    elif step_id == "confirmSubmit":
        # This step is about user action, so it's considered "complete" if prior steps are done.
        # Actual submission is handled separately.
        return False # This step is never complete until submission

    return False

def get_onboarding_completion_status(onboarding_progress):
    """
    Calculates the completion status for all onboarding steps.
    """
    data = onboarding_progress.step_data or {}
    user = onboarding_progress.user
    
    # Fetch user details once to avoid repeated lookups
    # Use helper methods for fields now stored in Keycloak
    user_details = {
        "email": user.get_email() if hasattr(user, 'get_email') else '',
        "phone": user.get_phone() if hasattr(user, 'get_phone') else '',
        "mobile": user.get_phone() if hasattr(user, 'get_phone') else '',  # mobile and phone are the same
    }

    status = {step["id"]: is_step_complete(step["id"], data, user_details) for step in ONBOARDING_STEPS}
    return status

def get_next_incomplete_step(onboarding_progress):
    """
    Finds the 'id' of the first step that is not complete.
    """
    completion_status = get_onboarding_completion_status(onboarding_progress)
    for step in ONBOARDING_STEPS:
        if not completion_status.get(step["id"]):
            return step["id"]
    
    # If all are complete, return the last step id, as it's the final confirmation.
    return ONBOARDING_STEPS[-1]["id"] if ONBOARDING_STEPS else None
