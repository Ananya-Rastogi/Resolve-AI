"""
Generator and validator for the Week 3 Comprehensive Evaluation Dataset.
Creates a versioned, reproducible dataset of 160 realistic customer-support tickets.
Includes validation/test split, zero data leakage against train.csv/test.csv,
and rigorous ground-truth annotations across classification, routing, and RAG retrieval.
"""
import json
import logging
from pathlib import Path
import random
from typing import Any, Dict, List
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_week3_dataset")

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DATASET_PATH = BASE_DIR / "eval" / "evaluation_dataset.json"
TRAIN_CSV_PATH = BASE_DIR / "data" / "train.csv"
TEST_CSV_PATH = BASE_DIR / "data" / "test.csv"
FAQS_CSV_PATH = BASE_DIR / "data" / "rag_faqs.csv"

# Deterministic priority and escalation rules matching production agents
def compute_ground_truth_priority(tier: str, sentiment: str) -> str:
    tier_scores = {"Platinum": 4, "Gold": 3, "Silver": 2, "Bronze": 1}
    sentiment_weight = 2 if sentiment.upper() == "NEGATIVE" else 1
    score = tier_scores.get(tier, 1) * sentiment_weight
    if score >= 6:
        return "High"
    elif score >= 3:
        return "Medium"
    else:
        return "Low"

def compute_ground_truth_team(topic: str) -> str:
    mapping = {
        "billing": "Finance Team",
        "shipping": "Logistics Team",
        "technical": "Tech Support",
        "other": "General Support",
    }
    return mapping.get(topic.lower(), "General Support")

def compute_ground_truth_escalation(tier: str, priority: str) -> str:
    if priority == "High" and tier in ["Platinum", "Gold"]:
        return "Escalated to Senior Manager"
    return "No Escalation Required"


# Curated ticket specifications: 40 per category = 160 total
TICKET_SPECS: List[Dict[str, Any]] = [
    # =========================================================================
    # BILLING (40 tickets)
    # =========================================================================
    # 1-10: Payment methods & failed payments (FAQ_001, FAQ_025)
    {"text": "Which credit cards and digital payment methods do you support?", "topic": "billing", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_001"], "facts": ["Accept major cards, wallets, and selected bank transfers"], "fallback": False, "review": False},
    {"text": "Can I pay using Google Pay or Apple Pay for my monthly bill?", "topic": "billing", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_001"], "facts": ["Accept major cards, wallets, and selected bank transfers"], "fallback": False, "review": False},
    {"text": "Do you accept bank wire transfer for invoice payments?", "topic": "billing", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_001"], "facts": ["Accept major cards, wallets, and selected bank transfers"], "fallback": False, "review": False},
    {"text": "My payment failed at checkout with an insufficient funds or bank restriction error.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_025"], "facts": ["Payments fail due to insufficient balance, bank restrictions, or network"], "fallback": False, "review": False},
    {"text": "Payment declined repeatedly even though my card details are totally valid.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_025"], "facts": ["Check bank restrictions, insufficient balance, or network"], "fallback": False, "review": False},
    {"text": "Why did my credit card transaction fail during checkout?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_025"], "facts": ["Bank restrictions or balance issues"], "fallback": False, "review": False},
    {"text": "Checkout payment keeps getting rejected by the payment gateway.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_025"], "facts": ["Payment gateway failure checks"], "fallback": False, "review": False},
    {"text": "Can I pay with Bitcoin or cryptocurrency on your store?", "topic": "billing", "sentiment": "POSITIVE", "tier": "Silver", "faqs": [], "facts": [], "fallback": True, "review": True},  # Unsupported
    {"text": "paymnt faild, plez help fix chekout error", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_025"], "facts": ["Typo query for payment failure"], "fallback": True, "review": False},
    {"text": "Accepted payment types?", "topic": "billing", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_001"], "facts": ["Major cards and wallets accepted"], "fallback": False, "review": False},

    # 11-20: Unexpected charges, breakdown, duplicate charges (FAQ_003, FAQ_010)
    {"text": "I see two identical charges for the same order on my credit card statement.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_010"], "facts": ["Contact support with transaction details so duplicate charge can be reviewed"], "fallback": False, "review": True},
    {"text": "I was billed twice for my purchase ORD-98124, please issue a credit.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_010"], "facts": ["Review duplicate charge with transaction details"], "fallback": False, "review": True},
    {"text": "Double charge showed up on my bank account for yesterday's order.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_010"], "facts": ["Duplicate charge review"], "fallback": False, "review": False},
    {"text": "Why was I charged extra fees on top of the listed product price?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_003"], "facts": ["Charges include taxes, shipping, discounts, or subscription fees"], "fallback": False, "review": False},
    {"text": "My monthly invoice is higher than expected, can you explain the breakdown?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_003"], "facts": ["Breakdown may include taxes, shipping, discounts, or fees"], "fallback": False, "review": False},
    {"text": "Unexplained surcharge added to my recent renewal statement.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_003"], "facts": ["Charges include taxes or subscription fees"], "fallback": False, "review": False},
    {"text": "chargd twise for same itm on visa card", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_010"], "facts": ["Typo query for duplicate charge"], "fallback": True, "review": False},
    {"text": "Duplicate debit transaction noticed on my account.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_010"], "facts": ["Duplicate charge review"], "fallback": False, "review": True},
    {"text": "Thank you for clarifying the additional tax line item on my receipt.", "topic": "billing", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_003"], "facts": ["Taxes and fees explanation"], "fallback": False, "review": False},
    {"text": "Why does my bill have extra taxes added to it?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_003"], "facts": ["Taxes and shipping charges"], "fallback": False, "review": False},

    # 21-30: Refund requests, timing, rejected refunds (FAQ_018, FAQ_028, FAQ_024)
    {"text": "How can I request a refund for an item that arrived damaged?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_018"], "facts": ["Request a refund from orders section by selecting eligible item"], "fallback": False, "review": False},
    {"text": "I canceled order ORD-12001 and want to submit a refund request.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_018"], "facts": ["Submit refund request in orders section"], "fallback": False, "review": False},
    {"text": "When will I receive my refund back into my banking account?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_028"], "facts": ["Refunds processed within 5 to 10 business days after approval"], "fallback": False, "review": False},
    {"text": "How many business days does it usually take for refund money to arrive?", "topic": "billing", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_028"], "facts": ["5 to 10 business days after approval"], "fallback": False, "review": False},
    {"text": "Customer support rejected my refund claim, what is the reason?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_024"], "facts": ["Rejected if item is not eligible or outside return window"], "fallback": False, "review": True},
    {"text": "Why was my return refund denied by the claims department?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_024"], "facts": ["Ineligibility or outside return window"], "fallback": False, "review": True},
    {"text": "My refund was rejected without explanation.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_024"], "facts": ["Item eligibility or return window expiration"], "fallback": False, "review": False},
    {"text": "I need my money returned immediately for my returned goods.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_018", "FAQ_028"], "facts": ["Request refund in orders section; 5-10 business days"], "fallback": False, "review": False},
    {"text": "Glad to see my refund is approved, looking forward to the funds.", "topic": "billing", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_028"], "facts": ["5 to 10 business days"], "fallback": False, "review": False},
    {"text": "Can I get an instant cash refund handed to me at a physical store?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": [], "facts": [], "fallback": True, "review": True},  # Unsupported policy

    # 31-40: Update billing info & download invoices (FAQ_014, FAQ_030)
    {"text": "Where can I download the official PDF invoice for last month's subscription?", "topic": "billing", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_030"], "facts": ["Invoices can be downloaded from account billing or order history"], "fallback": False, "review": False},
    {"text": "I need a copy of my billing receipt for company expense reporting.", "topic": "billing", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_030"], "facts": ["Download invoice from account billing section"], "fallback": False, "review": False},
    {"text": "How do I update the credit card number on file for future renewals?", "topic": "billing", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": ["FAQ_014"], "facts": ["Update billing information from account settings"], "fallback": False, "review": False},
    {"text": "My card expired, how do I change my billing payment details?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_014"], "facts": ["Update billing info in account settings"], "fallback": False, "review": False},
    {"text": "Need to update my company billing address and VAT registration number.", "topic": "billing", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_014"], "facts": ["Update in account settings"], "fallback": False, "review": False},
    {"text": "Download invoice PDF link is missing in my account dashboard.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_030"], "facts": ["Invoices downloaded from account billing section"], "fallback": False, "review": False},
    {"text": "Can you email me tax invoices for all purchases made this calendar year?", "topic": "billing", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": ["FAQ_030"], "facts": ["Account billing or order history download"], "fallback": False, "review": False},
    {"text": "Billing info update failed with database error code 500.", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_014"], "facts": ["Billing settings in account"], "fallback": True, "review": True},  # Multi-intent / tech error
    {"text": "Thanks for helping me locate my download invoice link so quickly!", "topic": "billing", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_030"], "facts": ["Invoices in account billing"], "fallback": False, "review": False},
    {"text": "Can you waive my 2-year contract early termination penalty fee?", "topic": "billing", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": [], "facts": [], "fallback": True, "review": True},  # Unsupported

    # =========================================================================
    # SHIPPING (40 tickets)
    # =========================================================================
    # 41-50: Delivery tracking & order status (FAQ_011, FAQ_020, FAQ_029)
    {"text": "Where is my package and how can I track its current location?", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_011", "FAQ_029"], "facts": ["Check order tracking page or account dashboard with tracking link"], "fallback": False, "review": False},
    {"text": "How do I track my shipment with tracking code TRK-9921?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_029"], "facts": ["Track order from account dashboard using tracking link"], "fallback": False, "review": False},
    {"text": "Has my order ORD-5541 been dispatched from the distribution warehouse yet?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_020"], "facts": ["Shipment status is available on order details page"], "fallback": False, "review": False},
    {"text": "Where can I check if my package has already shipped or is still pending?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": ["FAQ_020"], "facts": ["Shipment status on order details page"], "fallback": False, "review": False},
    {"text": "My package is three days late and tracking has not updated at all.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_011"], "facts": ["Check order tracking page or contact support with order ID"], "fallback": False, "review": False},
    {"text": "Courier tracking link says delivered but nothing is on my porch.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_011"], "facts": ["Contact support with order ID or check tracking page"], "fallback": False, "review": True},
    {"text": "Can you provide the courier tracking link for my recent order?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_029"], "facts": ["Tracking link in account dashboard"], "fallback": False, "review": False},
    {"text": "wher is my pakage it has not arived yet", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_011"], "facts": ["Typo query for order status"], "fallback": True, "review": False},
    {"text": "Appreciate the quick notification that my parcel was dispatched!", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_020"], "facts": ["Shipment status on order details page"], "fallback": False, "review": False},
    {"text": "Track order status for order ORD-7788.", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_029"], "facts": ["Track from account dashboard"], "fallback": False, "review": False},

    # 51-60: Shipping costs, transit times, express delivery (FAQ_007, FAQ_008, FAQ_021)
    {"text": "How many business days does standard ground delivery take to arrive?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_008"], "facts": ["Standard shipping usually takes 3 to 7 business days"], "fallback": False, "review": False},
    {"text": "What is the expected shipping time frame for domestic orders?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_008"], "facts": ["Standard shipping takes 3 to 7 business days depending on location"], "fallback": False, "review": False},
    {"text": "How much will shipping cost for delivery to a rural address?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_007"], "facts": ["Shipping cost is calculated at checkout based on location and method"], "fallback": False, "review": False},
    {"text": "Why are the delivery charges so expensive at the final checkout screen?", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_007"], "facts": ["Calculated at checkout based on location and method"], "fallback": False, "review": False},
    {"text": "Do you provide express or overnight delivery options for urgent packages?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": ["FAQ_021"], "facts": ["Express delivery is available in selected locations for eligible products"], "fallback": False, "review": False},
    {"text": "Can I expedite delivery to receive my shipment by tomorrow morning?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_021"], "facts": ["Express delivery available in selected locations"], "fallback": False, "review": False},
    {"text": "Package took 12 days to arrive which is much slower than 3 to 7 business days.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_008"], "facts": ["Standard shipping takes 3 to 7 business days"], "fallback": False, "review": False},
    {"text": "How much does shipping cost for heavy equipment orders?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_007"], "facts": ["Calculated at checkout"], "fallback": False, "review": False},
    {"text": "Can you guarantee same-day drone delivery to my private island?", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": [], "facts": [], "fallback": True, "review": True},  # Unsupported
    {"text": "Express delivery arrived ahead of schedule, wonderful service!", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": ["FAQ_021"], "facts": ["Express delivery in selected locations"], "fallback": False, "review": False},

    # 61-70: Returns process, return policy, return postage (FAQ_002, FAQ_004, FAQ_016)
    {"text": "What steps do I follow to return an item I ordered last week?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_002"], "facts": ["Start a return request from order history and follow return instructions"], "fallback": False, "review": False},
    {"text": "How do I initiate a product return through my online profile?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_002"], "facts": ["Start return request from order history"], "fallback": False, "review": False},
    {"text": "What is your official return policy and how long is the return window?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_016"], "facts": ["Eligible items can usually be returned within specified return window"], "fallback": False, "review": False},
    {"text": "How many days do I have to return an eligible product after delivery?", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_016"], "facts": ["Return within specified return window"], "fallback": False, "review": False},
    {"text": "Am I required to pay for the return shipping postage label myself?", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_004"], "facts": ["Return shipping depends on reason for return and product policy"], "fallback": False, "review": False},
    {"text": "Who covers return shipping fees when returning an unwanted item?", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_004"], "facts": ["Depends on reason for return and product policy"], "fallback": False, "review": False},
    {"text": "Return process was rejected because package was opened.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_016"], "facts": ["Eligible items within specified return window"], "fallback": False, "review": True},
    {"text": "I want to send back an incorrect size, do you provide prepaid labels?", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_002", "FAQ_004"], "facts": ["Return request from order history; shipping depends on policy"], "fallback": False, "review": False},
    {"text": "how to retrn item pleez", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_002"], "facts": ["Typo query for return request"], "fallback": True, "review": False},
    {"text": "Very happy with how smooth the return process worked.", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_002"], "facts": ["Return request from order history"], "fallback": False, "review": False},

    # 71-80: Delivery issues, damages, courier handoffs
    {"text": "The courier threw my parcel over the fence and damaged the product.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_002"], "facts": ["Start return request from order history"], "fallback": False, "review": True},
    {"text": "Package marked as signed for by resident but I was away on vacation.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_011"], "facts": ["Contact support with order ID"], "fallback": False, "review": True},
    {"text": "Delivery driver refused to bring package to my apartment door.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_011"], "facts": ["Order status and support inquiry"], "fallback": False, "review": False},
    {"text": "Can I change my delivery shipping address while the parcel is in transit?", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": [], "facts": [], "fallback": True, "review": True},  # Unsupported
    {"text": "Package arrived completely waterlogged and contents ruined.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_002"], "facts": ["Start return request from order history"], "fallback": False, "review": True},
    {"text": "Received shipping notification with an invalid tracking URL.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_029"], "facts": ["Track order from account dashboard"], "fallback": False, "review": False},
    {"text": "Thank you for the prompt dispatch and careful packaging.", "topic": "shipping", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_020"], "facts": ["Shipment details page"], "fallback": False, "review": False},
    {"text": "Shipment delayed at regional customs clearance facility.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_011"], "facts": ["Order tracking or contact support"], "fallback": True, "review": False},
    {"text": "Courier lost my order ORD-3319 entirely.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_011"], "facts": ["Contact support with order ID"], "fallback": False, "review": True},
    {"text": "My package was shipped but tracking shows no movement for a week.", "topic": "shipping", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_011", "FAQ_020"], "facts": ["Check order tracking or contact support"], "fallback": False, "review": False},

    # =========================================================================
    # TECHNICAL (40 tickets)
    # =========================================================================
    # 81-90: Password reset & account login (FAQ_013, FAQ_015)
    {"text": "I forgot my password and cannot sign in to my account.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_013"], "facts": ["Click forgot password on login page and follow email instructions"], "fallback": False, "review": False},
    {"text": "How do I trigger a password reset link for my login email?", "topic": "technical", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_013"], "facts": ["Click forgot password on login page"], "fallback": False, "review": False},
    {"text": "Why does the login portal say invalid credentials when my password is correct?", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_015"], "facts": ["Login issues due to incorrect credentials or account verification"], "fallback": False, "review": False},
    {"text": "I am locked out of my account due to failed authentication verification.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_015"], "facts": ["Incorrect credentials or verification issues"], "fallback": False, "review": True},
    {"text": "password reset email is not reaching my inbox or spam folder.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_013"], "facts": ["Click forgot password and follow email instructions"], "fallback": False, "review": False},
    {"text": "Cant log in to portal, says account suspended or unverifid", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_015"], "facts": ["Account verification issues"], "fallback": True, "review": False},
    {"text": "How do I reset my credentials securely?", "topic": "technical", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_013"], "facts": ["Forgot password instructions"], "fallback": False, "review": False},
    {"text": "Two-factor authentication code is rejected on every sign-in attempt.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_015"], "facts": ["Account verification issue"], "fallback": False, "review": False},
    {"text": "Thanks for helping me recover my locked login credentials.", "topic": "technical", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": ["FAQ_013"], "facts": ["Password reset recovery"], "fallback": False, "review": False},
    {"text": "Login page redirects in an infinite loop.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_015", "FAQ_009"], "facts": ["Login verification or refresh browser"], "fallback": False, "review": False},

    # 91-100: App errors, crashes, page loading (FAQ_009, FAQ_022)
    {"text": "The website shows a blank screen and loading error whenever I browse products.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_009"], "facts": ["Check internet connection, refresh page, or try another browser"], "fallback": False, "review": False},
    {"text": "How do I fix a loading spinner that never finishes on your web page?", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_009"], "facts": ["Check connection, refresh page, or try another browser"], "fallback": False, "review": False},
    {"text": "The mobile app keeps crashing immediately upon opening on iOS 18.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_022"], "facts": ["Update the app, clear cache, restart device, and try again"], "fallback": False, "review": False},
    {"text": "Android application freezes during navigation and forces close.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_022"], "facts": ["Update app, clear cache, restart device"], "fallback": False, "review": False},
    {"text": "Page loading fails with ERR_CONNECTION_TIMED_OUT.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_009"], "facts": ["Check internet connection, refresh, try another browser"], "fallback": False, "review": False},
    {"text": "App performance improved significantly after following your cache clear advice!", "topic": "technical", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_022"], "facts": ["Clear cache, restart, update app"], "fallback": False, "review": False},
    {"text": "mobyle app crashin all the time plez fix it", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_022"], "facts": ["Typo query for app crash"], "fallback": True, "review": False},
    {"text": "JavaScript console error Uncaught TypeError breaking checkout button.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_009"], "facts": ["Try another browser, refresh page"], "fallback": False, "review": True},
    {"text": "App not working after installing latest version 3.4.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_022"], "facts": ["Clear cache, restart device, try again"], "fallback": False, "review": False},
    {"text": "Website refreshed properly and cart is now displaying items.", "topic": "technical", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_009"], "facts": ["Refresh page / browser connection"], "fallback": False, "review": False},

    # 101-110: Contact tech support & account deletion (FAQ_005, FAQ_026)
    {"text": "How can I contact technical support directly for urgent developer assistance?", "topic": "technical", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_005"], "facts": ["Contact through live chat or support ticket submission"], "fallback": False, "review": False},
    {"text": "I need help from a support engineer to troubleshoot an API integration error.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_005"], "facts": ["Contact technical support through live chat or support ticket"], "fallback": False, "review": True},
    {"text": "How do I completely delete my account and remove my personal profile data?", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_026"], "facts": ["Request account deletion from privacy settings or by contacting support"], "fallback": False, "review": False},
    {"text": "I want my account permanently closed and personal data erased under GDPR.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_026"], "facts": ["Account deletion from privacy settings or contacting support"], "fallback": False, "review": True},
    {"text": "Where is the account termination option in profile settings?", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_026"], "facts": ["Privacy settings or contact support"], "fallback": False, "review": False},
    {"text": "Can I talk to a technical representative via phone or live chat?", "topic": "technical", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_005"], "facts": ["Live chat or support ticket submission"], "fallback": False, "review": False},
    {"text": "Technical support engineer resolved our webhook issue swiftly.", "topic": "technical", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": ["FAQ_005"], "facts": ["Live chat or ticket submission"], "fallback": False, "review": False},
    {"text": "Can you migrate my self-hosted SQL database into your cloud automatically?", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": [], "facts": [], "fallback": True, "review": True},  # Unsupported
    {"text": "delete acount plez", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_026"], "facts": ["Typo query for account deletion"], "fallback": True, "review": False},
    {"text": "Tech support chat option is grayed out on the portal.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_005"], "facts": ["Live chat or support ticket"], "fallback": False, "review": False},

    # 111-120: Edge cases, security, compatibility
    {"text": "Is this portal compatible with Linux running Firefox ESR?", "topic": "technical", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_009"], "facts": ["Browser compatibility checks"], "fallback": False, "review": False},
    {"text": "Session times out every 2 minutes while drafting a support ticket.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_015"], "facts": ["Login / session verification"], "fallback": False, "review": False},
    {"text": "Getting 403 Forbidden when accessing the user settings page.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_015"], "facts": ["Account verification or credentials"], "fallback": False, "review": False},
    {"text": "I suspect someone unauthorized logged into my user account from overseas.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_013", "FAQ_015"], "facts": ["Reset password and review verification"], "fallback": False, "review": True},
    {"text": "Can I install your mobile app on a jailbroken or rooted device?", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": [], "facts": [], "fallback": True, "review": True},  # Unsupported
    {"text": "Audio is not playing in video tutorial clips on the site.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_009"], "facts": ["Refresh browser or check connection"], "fallback": False, "review": False},
    {"text": "Browser extension interfering with form submission.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_009"], "facts": ["Try another browser or refresh"], "fallback": False, "review": False},
    {"text": "Great technical documentation for your developer endpoints!", "topic": "technical", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_005"], "facts": ["Technical support and resources"], "fallback": False, "review": False},
    {"text": "SSL certificate invalid error when connecting to your domain.", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_009"], "facts": ["Browser connection error"], "fallback": False, "review": True},
    {"text": "Can you provide root SSH credentials to your production database?", "topic": "technical", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": [], "facts": [], "fallback": True, "review": True},  # Highly unsupported

    # =========================================================================
    # OTHER (40 tickets)
    # =========================================================================
    # 121-130: Complaints & Escalations (FAQ_017, FAQ_019, FAQ_027)
    {"text": "I want to file a formal complaint regarding terrible customer service.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_027"], "facts": ["File a complaint through help center, live chat, or support ticket form"], "fallback": False, "review": True},
    {"text": "How do I register an official grievance with management?", "topic": "other", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_027"], "facts": ["Help center, live chat, or support ticket form"], "fallback": False, "review": False},
    {"text": "Can I escalate my unresolved complaint to a senior supervisor?", "topic": "other", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_017"], "facts": ["Unresolved complaints can be escalated to a senior support representative"], "fallback": False, "review": True},
    {"text": "I demand to speak to an executive manager immediately regarding my case.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_017"], "facts": ["Escalated to senior support representative"], "fallback": False, "review": True},
    {"text": "Where can I check the ongoing status of my filed complaint ticket?", "topic": "other", "sentiment": "NEGATIVE", "tier": "Silver", "faqs": ["FAQ_019"], "facts": ["Complaint status can be checked from support ticket section"], "fallback": False, "review": False},
    {"text": "Checking progress on previously submitted grievance number TKT-9901.", "topic": "other", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_019"], "facts": ["Checked from support ticket section"], "fallback": False, "review": False},
    {"text": "Agent was extremely rude and unhelpful on the phone yesterday.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_027"], "facts": ["File complaint via help center or ticket"], "fallback": False, "review": True},
    {"text": "want to fil complant abt poor servise", "topic": "other", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_027"], "facts": ["Typo query for complaint filing"], "fallback": True, "review": False},
    {"text": "Senior manager followed up and resolved my grievance quickly, thank you.", "topic": "other", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": ["FAQ_017"], "facts": ["Senior support representative follow-up"], "fallback": False, "review": False},
    {"text": "Where is my complaint update?", "topic": "other", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_019"], "facts": ["Support ticket section"], "fallback": False, "review": False},

    # 131-140: Product inquiries, specs, warranties (FAQ_006, FAQ_012, FAQ_023)
    {"text": "Does this electronic product include a manufacturer warranty?", "topic": "other", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_006"], "facts": ["Warranty details listed on product page under warranty information"], "fallback": False, "review": False},
    {"text": "What does the 1-year product warranty coverage include?", "topic": "other", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_006"], "facts": ["Listed on product page under warranty information"], "fallback": False, "review": False},
    {"text": "Is this laptop model currently in stock or sold out?", "topic": "other", "sentiment": "POSITIVE", "tier": "Gold", "faqs": ["FAQ_012"], "facts": ["Product availability shown on product page and may vary by location"], "fallback": False, "review": False},
    {"text": "How can I check inventory availability for item SKU-4412?", "topic": "other", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_012"], "facts": ["Shown on product page and may vary by location"], "fallback": False, "review": False},
    {"text": "Where can I find the complete hardware dimensions and technical specifications?", "topic": "other", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_023"], "facts": ["Product specifications available on product detail page"], "fallback": False, "review": False},
    {"text": "Are battery specifications and voltage requirements detailed on the listing?", "topic": "other", "sentiment": "POSITIVE", "tier": "Silver", "faqs": ["FAQ_023"], "facts": ["Available on product detail page"], "fallback": False, "review": False},
    {"text": "Product page does not show whether product has international warranty.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_006"], "facts": ["Warranty info on product page"], "fallback": False, "review": False},
    {"text": "Out of stock notification was sent for an item marked available.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": ["FAQ_012"], "facts": ["Availability on product page"], "fallback": False, "review": False},
    {"text": "Is this gadget in stock right now?", "topic": "other", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": ["FAQ_012"], "facts": ["Availability on product page"], "fallback": False, "review": False},
    {"text": "Found all hardware specs easily on the product page, great job.", "topic": "other", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": ["FAQ_023"], "facts": ["Specs on product detail page"], "fallback": False, "review": False},

    # 141-150: Multi-topic, edge complaints & Ambiguous inquiries
    {"text": "My package arrived late and customer service gave me completely contradictory answers.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_027"], "facts": ["File complaint through help center or ticket"], "fallback": True, "review": True},
    {"text": "The portal layout is confusing, cluttered, and difficult for non-technical users.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_027"], "facts": ["Feedback and complaint form"], "fallback": True, "review": False},
    {"text": "Returning to your service after a long absence, very impressed with the upgrades!", "topic": "other", "sentiment": "POSITIVE", "tier": "Silver", "faqs": [], "facts": [], "fallback": False, "review": False},
    {"text": "Need assistance regarding recent activity on my profile.", "topic": "other", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": [], "facts": [], "fallback": True, "review": True},  # Extremely vague
    {"text": "Help please.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Bronze", "faqs": [], "facts": [], "fallback": True, "review": True},  # Short ambiguous
    {"text": "Something went wrong with everything.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": [], "facts": [], "fallback": True, "review": True},  # Ambiguous
    {"text": "What are your physical office hours and corporate headquarters address?", "topic": "other", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": [], "facts": [], "fallback": True, "review": False},  # Unsupported
    {"text": "Do you sponsor collegiate coding hackathons or student clubs?", "topic": "other", "sentiment": "POSITIVE", "tier": "Silver", "faqs": [], "facts": [], "fallback": True, "review": False},  # Unsupported
    {"text": "Where is the CEO's personal direct phone number listed?", "topic": "other", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": [], "facts": [], "fallback": True, "review": True},  # Unsupported
    {"text": "General inquiry about partnership and vendor agreements.", "topic": "other", "sentiment": "POSITIVE", "tier": "Gold", "faqs": [], "facts": [], "fallback": True, "review": False},  # Unsupported

    # 151-160: Feedback, partnerships, edge cases
    {"text": "I really enjoy using your platform and wanted to share positive feedback!", "topic": "other", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": [], "facts": [], "fallback": False, "review": False},
    {"text": "Kudos to your customer support team for excellent service this week.", "topic": "other", "sentiment": "POSITIVE", "tier": "Silver", "faqs": [], "facts": [], "fallback": False, "review": False},
    {"text": "Your company is unethical and misleading customers with false claims.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Platinum", "faqs": ["FAQ_027"], "facts": ["File complaint through help center"], "fallback": False, "review": True},
    {"text": "Where can I submit general product feature suggestions?", "topic": "other", "sentiment": "POSITIVE", "tier": "Gold", "faqs": [], "facts": [], "fallback": True, "review": False},
    {"text": "Are you hiring remote technical support representatives in Europe?", "topic": "other", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": [], "facts": [], "fallback": True, "review": False},
    {"text": "Press inquiry from tech news outlet looking for an official quote.", "topic": "other", "sentiment": "POSITIVE", "tier": "Platinum", "faqs": [], "facts": [], "fallback": True, "review": True},
    {"text": "Can I get an NDA signed before discussing commercial licensing?", "topic": "other", "sentiment": "POSITIVE", "tier": "Gold", "faqs": [], "facts": [], "fallback": True, "review": True},
    {"text": "How do I become an affiliate marketer for your products?", "topic": "other", "sentiment": "POSITIVE", "tier": "Silver", "faqs": [], "facts": [], "fallback": True, "review": False},
    {"text": "Worst experience ever, closing all accounts immediately.", "topic": "other", "sentiment": "NEGATIVE", "tier": "Gold", "faqs": ["FAQ_026", "FAQ_027"], "facts": ["Account deletion and complaint filing"], "fallback": True, "review": True},
    {"text": "Thank you for the quick and polite response from your staff.", "topic": "other", "sentiment": "POSITIVE", "tier": "Bronze", "faqs": [], "facts": [], "fallback": False, "review": False},
]


def check_leakage_against_training(eval_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Inspect overlap between evaluation ticket texts and train.csv / test.csv."""
    train_texts = set()
    test_texts = set()

    if TRAIN_CSV_PATH.exists():
        df_train = pd.read_csv(TRAIN_CSV_PATH)
        train_texts = set(df_train["text"].astype(str).str.strip().str.lower())

    if TEST_CSV_PATH.exists():
        df_test = pd.read_csv(TEST_CSV_PATH)
        test_texts = set(df_test["text"].astype(str).str.strip().str.lower())

    exact_train_matches = []
    exact_test_matches = []

    for r in eval_records:
        clean_text = r["ticket_text"].strip().lower()
        if clean_text in train_texts:
            exact_train_matches.append(r["ticket_text"])
        if clean_text in test_texts:
            exact_test_matches.append(r["ticket_text"])

    return {
        "train_overlap_count": len(exact_train_matches),
        "test_overlap_count": len(exact_test_matches),
        "train_overlaps": exact_train_matches,
        "test_overlaps": exact_test_matches,
        "has_leakage": (len(exact_train_matches) > 0 or len(exact_test_matches) > 0),
    }


def generate_evaluation_dataset(seed: int = 42) -> List[Dict[str, Any]]:
    """Build, partition, and validate the 160-ticket evaluation dataset."""
    random.seed(seed)
    records = []

    # Assign deterministic split: 60 validation tickets (for threshold sweeps/tuning)
    # and 100 held-out test tickets (for final reporting)
    # Ensure balanced stratifications per topic
    topic_indices: Dict[str, List[int]] = {"billing": [], "shipping": [], "technical": [], "other": []}
    for idx, spec in enumerate(TICKET_SPECS):
        topic_indices[spec["topic"]].append(idx)

    val_indices = set()
    for topic, indices in topic_indices.items():
        # Pick 15 validation tickets per topic = 60 total
        rng = random.Random(seed + len(topic))
        chosen = rng.sample(indices, k=15)
        val_indices.update(chosen)

    for idx, spec in enumerate(TICKET_SPECS, 1):
        tier = spec["tier"]
        sentiment = spec["sentiment"]
        topic = spec["topic"]
        split = "val" if (idx - 1) in val_indices else "test"

        priority = compute_ground_truth_priority(tier, sentiment)
        team = compute_ground_truth_team(topic)
        escalation = compute_ground_truth_escalation(tier, priority)

        rec = {
            "ticket_id": f"EVAL-{idx:03d}",
            "ticket_text": spec["text"],
            "customer_tier": tier,
            "expected_topic": topic,
            "expected_sentiment": sentiment,
            "expected_priority": priority,
            "expected_team": team,
            "expected_escalation": escalation,
            "expected_faq_ids": spec["faqs"],
            "expected_resolution_facts": spec["facts"],
            "requires_fallback": spec["fallback"],
            "requires_human_review": spec["review"],
            "split": split,
        }
        records.append(rec)

    return records


def build_and_save():
    records = generate_evaluation_dataset()
    leakage = check_leakage_against_training(records)

    if leakage["has_leakage"]:
        raise ValueError(f"CRITICAL: Data leakage detected! {leakage}")

    logger.info(f"Generated {len(records)} evaluation tickets.")
    val_count = sum(1 for r in records if r["split"] == "val")
    test_count = sum(1 for r in records if r["split"] == "test")
    logger.info(f"Split breakdown: Validation={val_count}, Held-out Test={test_count}")
    logger.info(f"Leakage check: PASSED (0 train overlaps, 0 test overlaps)")

    with open(OUTPUT_DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    logger.info(f"Saved evaluation dataset to {OUTPUT_DATASET_PATH}")


if __name__ == "__main__":
    build_and_save()
