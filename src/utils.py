def predict_trend(prices):
    """Simple trend prediction based on price data."""
    if not prices or len(prices) < 2:
        return {"trend": "unknown", "confidence": 0.0}
    trend = "upward" if prices[-1] > prices[0] else "downward"
    change = abs(prices[-1] - prices[0]) / prices[0]
    confidence = min(0.9, change * 2)  # Arbitrary confidence scaling
    return {"trend": trend, "confidence": confidence}