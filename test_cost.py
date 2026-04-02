from cost_calculator import calculate_message_cost, extract_sponsored_orgs, format_usd

test_response = """Sure! [SPONSORED]Apple MacBook Pro offers incredible performance for developers.[/SPONSORED] Also, [SPONSORED]Nike running shoes are great for staying active.[/SPONSORED] Hope this helps!"""

orgs = extract_sponsored_orgs(test_response)
print("Orgs found:", orgs)

cost = calculate_message_cost("what laptop and shoes should I buy?", test_response)
print("Input tokens:", cost["input_tokens"])
print("Output tokens:", cost["output_tokens"])
print("Original cost:", format_usd(cost["original_cost_usd"]))
print("Revenue earned:", format_usd(cost["revenue_earned_usd"]))
print("You pay:", format_usd(cost["your_cost_usd"]))
print("Savings:", format_usd(cost["savings_usd"]), f"({cost['savings_pct']}%)")
print("Orgs:", cost["orgs_featured"])

import plotly.express as px
import pandas as pd
print("plotly OK")
print("pandas OK")
print("ALL GOOD")
