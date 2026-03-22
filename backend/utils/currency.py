def convert_and_apply_margin(payout_usd: float) -> float:
    rate = 80
    margin_percent = 0.7

    amount_inr = payout_usd * rate
    user_reward = amount_inr * margin_percent

    return round(user_reward, 2)