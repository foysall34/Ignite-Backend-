
from rest_framework.exceptions import PermissionDenied

def check_prompt_limit(user):
    user.reset_prompt_count_if_needed()

    if user.role == "admin":
        return 

    
    base_limit = 20 if user.plan_type == "freebie" else 50 # premium users get 3 prompts/month
    total_limit = base_limit + user.extra_prompts

    if user.monthly_prompt_count >= total_limit:
        raise PermissionDenied(
            f"You have reached your monthly limit of {base_limit} prompts. "
            f"Please  buy a top-up."
        )

    user.increment_prompt_count()






