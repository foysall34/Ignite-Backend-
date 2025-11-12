# utils.py
from rest_framework.exceptions import PermissionDenied

def check_prompt_limit(user):
    user.reset_prompt_count_if_needed()

    if user.role == "admin":
        return  # Unlimited

    # Determine base limit
    base_limit = 2 if user.role == "user" else 3 # premium users get 3 prompts/month
    total_limit = base_limit + user.extra_prompts

    if user.monthly_prompt_count >= total_limit:
        raise PermissionDenied(
            f"You have reached your monthly limit of {base_limit} prompts. "
            f"Please wait for next month or buy a top-up."
        )

    # Increment usage
    user.increment_prompt_count()
