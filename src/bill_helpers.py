import math
from datetime import datetime, timezone

import discord
from firebase_admin import firestore

from constants import SPAN, get_display_status
from firestore_setup import db
from settings import (
    BILL_COLLECTION_NAME,
    BILL_COUNTER_COLLECTION,
    DIAMOND_EMOJI,
    EMBED_THUMBNAIL_URL,
    EMERALD_EMOJI,
    ESSENCE_EMOJI,
    GOLD_EMOJI,
    IRON_EMOJI,
    REQUIRED_CO_SPONSORS_DEFAULT,
)
from timezone_utils import EST
from google.cloud.firestore_v1.base_query import FieldFilter


def find_bill_by_id_sync(bill_id: str):
    if not db:
        return None, None
    q = db.collection(BILL_COLLECTION_NAME).where(filter=FieldFilter('id', '==', bill_id)).limit(1)
    for doc in q.stream():
        return doc.reference, doc.to_dict()
    return None, None


def get_next_bill_number():
    """Get the next sequential bill number using atomic increment."""
    if not db:
        return None

    counter_ref = db.collection(BILL_COUNTER_COLLECTION).document('counter')

    @firestore.transactional
    def increment_counter(transaction):
        snapshot = counter_ref.get(transaction=transaction)
        if snapshot.exists:
            current = snapshot.get('lastNumber')
            next_number = current + 1
        else:
            next_number = 1

        transaction.set(counter_ref, {'lastNumber': next_number})
        return next_number

    # Transaction operations are synchronous, so no need to wrap increment_counter itself
    # The transaction context handles atomicity
    transaction = db.transaction()
    return increment_counter(transaction)


def vote_counts(votes_dict):
    yes = len(votes_dict.get('yes', []))
    no = len(votes_dict.get('no', []))
    abstain = len(votes_dict.get('abstain', []))
    total_yes_no = yes + no
    return yes, no, abstain, total_yes_no


def two_thirds_threshold(total):
    return math.floor((2 * total) / 3) + 1


def int_to_roman(num):
    """Convert integer to Roman numeral."""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1,
    ]
    syms = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I",
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num


def parse_reward_with_emojis(reward_text: str) -> str:
    """Parse reward text and add commodity emojis based on bank commodities."""
    if not reward_text or reward_text == "No bounty":
        return "No bounty"

    # Convert to lowercase for matching
    reward_lower = reward_text.lower().strip()

    # Match specific commodity keywords (check for common CivMC formats)
    # Pattern: digits followed by optional space and commodity abbreviation (tolerates punctuation)
    import re

    # Use word boundaries (\b) to avoid matching within words, but allow punctuation after
    if re.search(r'\d+\s*d\b', reward_lower) or 'diamond' in reward_lower:
        return f"{DIAMOND_EMOJI} {reward_text}"
    if 'essence' in reward_lower or re.search(r'\d+\s*es\b', reward_lower):
        return f"{ESSENCE_EMOJI} {reward_text}"
    if 'gold' in reward_lower or re.search(r'\d+\s*g(?:ld)?\b', reward_lower):
        return f"{GOLD_EMOJI} {reward_text}"
    if 'iron' in reward_lower or re.search(r'\d+\s*i(?:ron)?\b', reward_lower):
        return f"{IRON_EMOJI} {reward_text}"
    if 'emerald' in reward_lower or re.search(r'\d+\s*em(?:erald)?\b', reward_lower):
        return f"{EMERALD_EMOJI} {reward_text}"
    # If no commodity detected, just return original text
    return reward_text


def results_embed(guild, bill):
    votes = bill.get('votes', {'yes': [], 'no': [], 'abstain': []})
    passed = bill.get('status') in ('Passed', 'Bill is Now Law')
    title = f"Approved: {bill.get('title','(Untitled)')}" if passed else f"Failed: {bill.get('title','(Untitled)')}"

    is_confidential = bill.get('visibility', 'PUBLIC') == 'CONFIDENTIAL'
    sponsor_tag = "Anonymous" if is_confidential else bill.get('sponsorTag', 'Unknown')
    bill_text = bill.get('text', '').strip()

    description = f"Introduced by: {sponsor_tag}\n\n{bill_text}"

    em = discord.Embed(
        title=title,
        description=description[:4000],
        color=discord.Color.green() if passed else discord.Color.red(),
    )

    if EMBED_THUMBNAIL_URL:
        try:
            em.set_thumbnail(url=EMBED_THUMBNAIL_URL)
        except Exception:
            pass

    def mentions(ids):
        return "\n".join(f"{tag}" for tag in (ids or [])) if ids else "None"

    support_list = mentions([f"<@{u}>" for u in votes.get('yes', [])])
    oppose_list = mentions([f"<@{u}>" for u in votes.get('no', [])])
    abstain_list = mentions([f"<@{u}>" for u in votes.get('abstain', [])])

    # Calculate and show result
    yes, no, abstain, total_yes_no = vote_counts(votes)
    voting_threshold = bill.get('votingThreshold', 'SIMPLE_MAJORITY')
    status = bill.get('status')

    # Check if this was a veto override
    if status == 'Bill is Now Law' and bill.get('vetoNote'):
        required = two_thirds_threshold(max(total_yes_no, 1))
        result_text = f"⚔️ **Veto Overridden with 2/3 Majority** ({yes}/{total_yes_no}, needed {required})"
    elif status == 'Failed' and bill.get('vetoNote'):
        required = two_thirds_threshold(max(total_yes_no, 1))
        result_text = f"🛡️ **Veto Upheld** ({yes}/{total_yes_no}, needed {required} to override)"
    elif voting_threshold == 'SIMPLE_MAJORITY':
        result_text = f"✅ **Simple Majority Achieved** ({yes}/{total_yes_no})" if passed else f"❌ **No Simple Majority** ({yes}/{total_yes_no})"
    elif voting_threshold == 'TWO_THIRDS_VOTES':
        required = two_thirds_threshold(max(total_yes_no, 1))
        result_text = f"✅ **2/3 Majority Achieved** ({yes}/{total_yes_no}, needed {required})" if passed else f"❌ **2/3 Majority Not Met** ({yes}/{total_yes_no}, needed {required})"
    elif voting_threshold == 'THREE_FOURTHS_VOTES':
        required = math.ceil(total_yes_no * 3 / 4)
        result_text = f"✅ **3/4 Majority Achieved** ({yes}/{total_yes_no}, needed {required})" if passed else f"❌ **3/4 Majority Not Met** ({yes}/{total_yes_no}, needed {required})"
    else:
        result_text = f"✅ **Vote Passed** ({yes}/{total_yes_no})" if passed else f"❌ **Vote Failed** ({yes}/{total_yes_no})"

    em.add_field(name="Result", value=result_text, inline=False)
    em.add_field(name="✅ Support", value=support_list, inline=False)
    em.add_field(name="❌ Oppose", value=oppose_list, inline=False)
    em.add_field(name="⚪ Abstain", value=abstain_list, inline=False)

    vis = bill.get('visibility', 'PUBLIC')
    vis_text = 'PUBLIC' if vis == 'PUBLIC' else 'CONFIDENTIAL'

    # Display voting threshold based on bill configuration
    voting_threshold = bill.get('votingThreshold', 'SIMPLE_MAJORITY')
    bill_type = bill.get('billType', 'STANDARD')

    if bill.get('status') == 'Vetoed':
        threshold_text = "2/3 MAJORITY REQUIRED TO OVERRIDE VETO"
    elif voting_threshold == 'TWO_THIRDS_VOTES':
        threshold_text = "2/3 MAJORITY OF VOTES REQUIRED"
    elif voting_threshold == 'THREE_FOURTHS_VOTES':
        threshold_text = "3/4 MAJORITY OF VOTES REQUIRED"
    elif voting_threshold == 'TWO_THIRDS_ALL_CONSEJEROS':
        threshold_text = "2/3 MAJORITY OF ALL CONSEJEROS REQUIRED"
    else:
        threshold_text = "SIMPLE MAJORITY REQUIRED"

    now_utc = datetime.now(timezone.utc)
    now_est = now_utc.astimezone(EST)
    timestamp = now_est.strftime('%m/%d/%y, %I:%M %p EST')
    em.set_footer(text=f"{vis_text} - {threshold_text} | {timestamp}")
    return em


def get_bill_embed(bill):
    title = f"**{bill.get('title','Untitled')}**"

    # Color based on bill status
    status = bill.get('status')
    if status == 'Bill is Now Law':
        color = discord.Color.gold()  # Gold for enacted laws
    elif status == 'Passed':
        color = discord.Color.green()  # Green for passed bills
    elif status in ['Failed', 'Vetoed']:
        color = discord.Color.red()  # Red for failed/vetoed bills
    else:
        color = discord.Color.from_str("#794966")  # Purple for active/pending bills

    text = bill.get('text', '')
    preview = text[:2000] + ('...' if len(text) > 2000 else '')

    em = discord.Embed(
        title=title,
        description=f"*{preview}*",
        color=color,
    )

    status = bill.get('status', 'Unknown')
    bill_type = bill.get('billType', 'STANDARD')
    display_status = get_display_status(status, bill_type)
    required = bill.get('requiredCoSponsors', REQUIRED_CO_SPONSORS_DEFAULT)
    current = len(bill.get('coSponsors', []))
    visibility = "Public" if bill.get('visibility', 'PUBLIC') == 'PUBLIC' else "Confidential"
    category = bill.get('category', 'General')

    category_display = category

    em.add_field(name="Status", value=display_status, inline=True)
    em.add_field(name="Category", value=category_display, inline=True)
    em.add_field(name="Visibility", value=visibility, inline=True)

    # Show sponsorship in separate row
    sponsorship_value = "Active" if bill.get('sponsorId') or current > 0 else "None"
    em.add_field(name="Sponsorship", value=sponsorship_value, inline=True)

    # Show veto note if bill is vetoed
    if status == 'Vetoed' and bill.get('vetoNote'):
        em.add_field(name="Veto Status", value=bill.get('vetoNote'), inline=False)

    # Show sponsor and co-sponsor details with domains
    sponsorship_list = []
    is_confidential = bill.get('visibility', 'PUBLIC') == 'CONFIDENTIAL'

    # Add sponsor if exists
    sponsor_id = bill.get('sponsorId')
    if sponsor_id:
        if is_confidential:
            sponsor_display = "Anonymous"
        else:
            sponsor_display = bill.get('sponsorTag', f"<@{sponsor_id}>")
        sponsor_domain = bill.get('sponsorDomain', 'Soberante')
        domain_short = sponsor_domain.split('(')[0].strip()
        sponsorship_list.append(f"**Sponsor:** {sponsor_display} - *{domain_short}*")

    # Add co-sponsors if exist
    co_sponsor_details = bill.get('coSponsorDetails', [])
    if co_sponsor_details:
        for cs in co_sponsor_details:
            if is_confidential:
                mention = "Anonymous"
            else:
                mention = cs.get('mention', f"<@{cs.get('userId')}>")
            domain = cs.get('domain', 'Unknown Domain')
            domain_short = domain.split('(')[0].strip()
            sponsorship_list.append(f"**Co-Sponsor:** {mention} - *{domain_short}*")

    if sponsorship_list:
        em.add_field(name="Sponsorship Details", value="\n".join(sponsorship_list), inline=False)

    votes = bill.get('votes', {'yes': [], 'no': [], 'abstain': []})
    yes, no, abstain, total = vote_counts(votes)
    if bill.get('status') in ('Voting', 'Vetoed'):
        visibility = bill.get('visibility', 'PUBLIC')

        if visibility == 'CONFIDENTIAL':
            # Hide voter identities for confidential votes
            yes_list = f"{yes} vote(s)" if yes > 0 else "None yet"
            no_list = f"{no} vote(s)" if no > 0 else "None yet"
            abstain_list = f"{abstain} vote(s)" if abstain > 0 else "None yet"
        else:
            # Show voter mentions for public votes (vertical list like results)
            yes_mentions = [f"<@{uid}>" for uid in votes.get('yes', [])]
            no_mentions = [f"<@{uid}>" for uid in votes.get('no', [])]
            abstain_mentions = [f"<@{uid}>" for uid in votes.get('abstain', [])]

            yes_list = "\n".join(yes_mentions) if yes_mentions else "None yet"
            no_list = "\n".join(no_mentions) if no_mentions else "None yet"
            abstain_list = "\n".join(abstain_mentions) if abstain_mentions else "None yet"

        em.add_field(name=f"{SPAN['YES']} ({yes})", value=yes_list, inline=False)
        em.add_field(name=f"{SPAN['NO']} ({no})", value=no_list, inline=False)
        em.add_field(name=f"{SPAN['ABSTAIN']} ({abstain})", value=abstain_list, inline=False)

        if bill.get('status') == 'Voting':
            em.add_field(name="Threshold", value="Simple Majority (>50%)", inline=True)
        else:
            need = two_thirds_threshold(max(total, 1))
            em.add_field(name="Override Needed", value=f"2/3 majority: {need} {SPAN['YES']}", inline=True)

    if EMBED_THUMBNAIL_URL:
        try:
            em.set_thumbnail(url=EMBED_THUMBNAIL_URL)
        except Exception:
            pass

    created_at = bill.get('createdAt')
    sponsor_tag = bill.get('sponsorTag')
    proposer_tag = bill.get('proposerTag', 'Unknown')
    is_confidential = bill.get('visibility', 'PUBLIC') == 'CONFIDENTIAL'

    if is_confidential:
        # Hide sponsor/proposer identity for confidential bills
        attribution = "Anonymous"
    elif sponsor_tag:
        attribution = f"Sponsored by {sponsor_tag}"
    else:
        attribution = f"Proposed by {proposer_tag}"

    if isinstance(created_at, datetime):
        created_at_est = created_at.astimezone(EST)
        footer_text = f"Edict #{bill.get('id','???')} • {attribution} • {created_at_est.strftime('%b %d, %Y')}"
    else:
        footer_text = f"Edict #{bill.get('id','???')} • {attribution}"
    em.set_footer(text=footer_text)

    return em
