import os

# Set these in Replit (Tools → Secrets):
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "YOUR_DISCORD_BOT_TOKEN")
FIREBASE_CONFIG_PATH = os.getenv("FIREBASE_CONFIG_PATH", "/tmp/serviceAccount.json")
MONARCH_ROLE_ID = int(os.getenv("MONARCH_ROLE_ID", "0"))  # 0 = disable monarch role check
PROPOSED_CHANNEL_ID = int(os.getenv("PROPOSED_CHANNEL_ID", "0"))  # 0 = post proposed bills in creation channel
VOTING_CHANNEL_ID = int(os.getenv("VOTING_CHANNEL_ID", "0"))  # 0 = post voting bills in creation channel
VOTE_NOTIFICATION_CHANNEL_ID = int(os.getenv("VOTE_NOTIFICATION_CHANNEL_ID", "0"))  # 0 = send notifications to voting channel
PRIVATE_RESULTS_CHANNEL_ID = int(os.getenv("PRIVATE_RESULTS_CHANNEL_ID", "0"))  # 0 = same channel
EMBED_THUMBNAIL_URL = os.getenv("EMBED_THUMBNAIL_URL", "")  # optional logo URL

# Custom Emojis - Your custom Discord emojis for commodities
IRON_EMOJI = "<:iron:1429196084512559204>"  # Custom iron emoji
ESSENCE_EMOJI = "<:essence:1429197999183101952>"  # Custom essence orb emoji
DIAMOND_EMOJI = "<:dimmies:1429198036508344490>"  # Custom diamond emoji
GOLD_EMOJI = "<:gold:1429253820592033862>"  # Custom gold emoji
EMERALD_EMOJI = "<:emerald:1429703329004388487>"  # Custom emerald emoji
SNITCH_EMOJI = "<:snitch:1429196934350114958>"  # Custom snitch emoji
PEARL_EMOJI = "<:pearl:1428919990194536458>"  # Custom pearl emoji

# Block Emojis - CivMC Block commodities (traded alongside ingots/units)
DIAMOND_BLOCK_EMOJI = "<:dimmiebloc:1437911575859298596>"  # Diamond block
IRON_BLOCK_EMOJI = "<:ironbloc:1429840781983612952>"  # Iron block
GOLD_BLOCK_EMOJI = "<:goldbloc:1429840925001257083>"  # Gold block
EMERALD_BLOCK_EMOJI = "<:emeraldbloc:1429855518083645472>"  # Emerald block

BILL_COLLECTION_NAME = os.getenv("BILL_COLLECTION_NAME", "royal_council_bills")
REQUIRED_CO_SPONSORS_DEFAULT = int(os.getenv("REQUIRED_CO_SPONSORS", "0"))
MIN_VOTES_TO_FINALIZE = int(os.getenv("MIN_VOTES_TO_FINALIZE", "2"))  # Minimum votes required for manual finalization
TOTAL_CONSEJEROS = int(os.getenv("TOTAL_CONSEJEROS", "8"))  # Total number of councilors for 2/3 majority calculations

# CivMC Nation Management Features
POS_CHANNEL_ID = int(os.getenv("POS_CHANNEL_ID", "1407144090587627601"))  # Channel for POS alerts
SNITCH_LOG_CHANNEL_ID = int(os.getenv("SNITCH_LOG_CHANNEL_ID", "1407144090587627601"))  # Channel for parsing snitch logs
WARRANT_CHANNEL_ID = int(os.getenv("WARRANT_CHANNEL_ID", "1424559866319605800"))  # Citizens-only warrant channel
COURT_CHANNEL_ID = int(os.getenv("COURT_CHANNEL_ID", "1424491901779841024"))  # Court proceedings channel (legacy)
COURT_STATUS_CHANNEL_ID = int(os.getenv("COURT_STATUS_CHANNEL_ID", "1424569753887969371"))  # Court status updates channel
LAWYER_NOTIFICATIONS_CHANNEL_ID = int(os.getenv("LAWYER_NOTIFICATIONS_CHANNEL_ID", "1424528652623679628"))  # Uses court cases channel by default
# Unified court cases channel (all cases go here, differentiated by color)
COURT_CASES_CHANNEL_ID = int(os.getenv("COURT_CASES_CHANNEL_ID", "1424528652623679628"))  # All cases channel
# Legacy channel IDs (kept for backward compatibility)
CIVIL_CASES_CHANNEL_ID = COURT_CASES_CHANNEL_ID
CRIMINAL_CASES_CHANNEL_ID = COURT_CASES_CHANNEL_ID

UNIVERSAL_CITIZEN_ROLE_ID = 1410066045493841951  # Universal role given to ALL citizens (primary & secondary)
CITIZEN_ROLE_ID = 1406754801458610467  # Base citizen role given to ALL citizens (both primary and secondary)
SECONDARY_CITIZEN_ROLE_ID = 1424217649386360852  # Additional role given ONLY to secondary/dual citizens
RESIDENT_ROLE_ID = 1407066117633081447  # Role given to residents (non-citizens)
REFERENDUM_CHANNEL_ID = int(os.getenv("REFERENDUM_CHANNEL_ID", "1406728392568602654"))  # Channel for state referendums
REFERENDUM_VOTER_ROLE_ID = int(os.getenv("REFERENDUM_VOTER_ROLE_ID", "1410766073594380419"))  # Role allowed to vote on referendums
ATTORNEY_ROLE_ID = int(os.getenv("ATTORNEY_ROLE_ID", "1426053471592906812"))  # Discord role for Attorneys (Lawyer)
PUBLIC_DEFENDER_ROLE_ID = int(os.getenv("PUBLIC_DEFENDER_ROLE_ID", "1426054167344189480"))  # Discord role for Public Defenders
STATE_PROSECUTOR_ROLE_ID = int(os.getenv("STATE_PROSECUTOR_ROLE_ID", "1426053914595430513"))  # Discord role for State Prosecutors (Prosecutor)

# Collection names for new features
CITIZENS_COLLECTION = "florabi_citizens"
WARRANTS_COLLECTION = "florabi_warrants"
PEARLS_COLLECTION = "florabi_pearls"
SNITCH_LOGS_COLLECTION = "florabi_snitch_logs"
COURT_CASES_COLLECTION = "florabi_court_cases"
CRIMINAL_RECORDS_COLLECTION = "florabi_criminal_records"
PORTAL_PANELS_COLLECTION = "florabi_portal_panels"
LAWYERS_COLLECTION = "florabi_lawyers"
REFERENDUMS_COLLECTION = "florabi_referendums"
BILL_COUNTER_COLLECTION = "florabi_bill_counter"
BETTING_EVENTS_COLLECTION = "florabi_betting_events"
BETTING_BETS_COLLECTION = "florabi_betting_bets"
BETTING_LEADERBOARD_COLLECTION = "florabi_betting_leaderboard"
STOCK_ORDERS_COLLECTION = "florabi_stock_orders"  # Pending stock purchases
BANK_ACCOUNTS_COLLECTION = "florabi_bank_accounts"  # Bank accounts for citizens
BANK_TRANSACTIONS_COLLECTION = "florabi_bank_transactions"  # All bank transactions
TREASURY_BONDS_COLLECTION = "florabi_treasury_bonds"  # Treasury bonds for state investment
ESSENCE_CERTIFICATES_COLLECTION = "florabi_essence_certificates"  # Tradeable essence certificates
MARKET_PRICES_COLLECTION = "florabi_market_prices"  # Live commodity pricing
PROPERTIES_COLLECTION = "florabi_properties"  # Land registry and property ownership
PROPERTY_LISTINGS_COLLECTION = "florabi_property_listings"  # Properties for sale on the marketplace
PROPERTY_VALUES_COLLECTION = "florabi_property_values"  # Property value history tracking
ECONOMIC_CYCLES_COLLECTION = "florabi_economic_cycles"  # Market boom/bust cycles
MORTGAGES_COLLECTION = "florabi_mortgages"  # Property loans and financing
PROPERTY_IMPROVEMENTS_COLLECTION = "florabi_property_improvements"  # Property upgrades and development

# Florabís Regions and Districts/Cities
FLORABIS_REGIONS = {
    "Flora Region": [
        ("Ciudad de Victoria", "Victoria City"),
        ("Hypertomia", "Rico's"),
    ],
    "San Alejandro Region": [
        ("San Alejandro Norte", "North"),
        ("Söderville", "Historical City/District"),
        ("San Alejandro Sur", "South"),
        ("Latice", None),
    ],
    "Wizard Region": [
        ("Distrito Mágico", "Wizard District"),
    ],
}

# Flat list of all cities for quick lookup
ALL_CITIES = []
for region, cities in FLORABIS_REGIONS.items():
    for city_name, alt_name in cities:
        ALL_CITIES.append((region, city_name, alt_name))
CONTRACTS_COLLECTION = "florabi_contracts"  # Government contracts and public works
CONTRACT_BIDS_COLLECTION = "florabi_contract_bids"  # Bids on government contracts
ECONOMIC_REPORTS_COLLECTION = "florabi_economic_reports"  # Historical economic data
PANEL_JOBS_COLLECTION = "florabi_panel_jobs"  # Job queue for async panel posting
PEARL_PANELS_COLLECTION = "florabi_pearl_panels"  # Pearl panel message tracking for re-registration
