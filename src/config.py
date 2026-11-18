USD_TO_EUR = 0.86  # ECB reference rate on 18/11/2026; prices from docs.mistral.ai/inference/pricing (USD per M tokens)

PRICES_USD = {
    "mistral-small-latest": (0.15, 0.6),
    "ministral-8b-latest": (0.15, 0.15),
    "ministral-3b-latest": (0.1, 0.1),
}
PRICES = {model: (inp * USD_TO_EUR, out * USD_TO_EUR) for model, (inp, out) in PRICES_USD.items()}
