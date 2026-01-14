import asyncio
import math
from datetime import datetime, timezone

from constants import SPAN
from bill_helpers import results_embed, two_thirds_threshold, vote_counts
from access_control import ROYAL_COUNCILOR_ROLE_ID
from settings import MIN_VOTES_TO_FINALIZE, PRIVATE_RESULTS_CHANNEL_ID, TOTAL_CONSEJEROS


async def finalize_bill(ref, bill, guild, source_channel, is_auto=False):
    """
    Finalize a bill's voting. Can be called from button or auto-finalization.
    Returns (success: bool, message: str)
    """
    status = bill.get('status')
    if status not in ('Voting', 'Vetoed'):
        return False, f"Cannot finalize while **{status}**."

    votes = bill.get('votes', {'yes': [], 'no': [], 'abstain': []})
    yes, no, _abstain, total_yes_no = vote_counts(votes)

    # For auto-finalization, skip minimum vote requirement
    if status == 'Voting':
        if not is_auto and total_yes_no < MIN_VOTES_TO_FINALIZE:
            return False, f"Need at least {MIN_VOTES_TO_FINALIZE} Yes/No votes to finalize."

        # Check voting threshold
        voting_threshold = bill.get('votingThreshold', 'SIMPLE_MAJORITY')

        # For auto-finalization, passed bills become law directly
        passed_status = 'Bill is Now Law' if is_auto else 'Passed'
        passed_note_suffix = " Bill is now law." if is_auto else " Awaiting Royal Assent."

        if voting_threshold == 'SIMPLE_MAJORITY':
            new_status = passed_status if yes > total_yes_no / 2 else 'Failed'
            note = f"✅ VOTE PASSED.{passed_note_suffix}" if new_status != 'Failed' else "❌ VOTE FAILED. No simple majority."
        elif voting_threshold == 'TWO_THIRDS_VOTES':
            required = two_thirds_threshold(max(total_yes_no, 1))
            new_status = passed_status if yes >= required else 'Failed'
            note = f"✅ VOTE PASSED with 2/3 majority ({yes}/{total_yes_no}).{passed_note_suffix}" if new_status != 'Failed' else f"❌ VOTE FAILED. Needed {required} votes, got {yes}."
        elif voting_threshold == 'THREE_FOURTHS_VOTES':
            required = math.ceil(total_yes_no * 3 / 4)
            new_status = passed_status if yes >= required else 'Failed'
            note = f"✅ VOTE PASSED with 3/4 majority ({yes}/{total_yes_no}).{passed_note_suffix}" if new_status != 'Failed' else f"❌ VOTE FAILED. Needed {required} votes, got {yes}."
        elif voting_threshold == 'TWO_THIRDS_ALL_CONSEJEROS':
            if TOTAL_CONSEJEROS > 0:
                total_consejeros = TOTAL_CONSEJEROS
                required = two_thirds_threshold(max(total_consejeros, 1))
                new_status = passed_status if yes >= required else 'Failed'
                note = f"✅ VOTE PASSED with 2/3 of all Consejeros ({yes}/{total_consejeros}).{passed_note_suffix}" if new_status != 'Failed' else f"❌ VOTE FAILED. Needed {required} of {total_consejeros} Consejeros, got {yes}."
            else:
                print(f"[WARN] Bill {bill.get('id')} requires 2/3 of ALL Consejeros but TOTAL_CONSEJEROS env var is not set. Falling back to 2/3 of votes cast.")
                required = two_thirds_threshold(max(total_yes_no, 1))
                new_status = passed_status if yes >= required else 'Failed'
                note = f"⚠️ VOTE PASSED with 2/3 of votes ({yes}/{total_yes_no}) - TOTAL_CONSEJEROS not configured.{passed_note_suffix}" if new_status != 'Failed' else f"⚠️ VOTE FAILED. Needed {required} of {total_yes_no} votes (TOTAL_CONSEJEROS not configured), got {yes}."
        else:
            new_status = passed_status if yes > total_yes_no / 2 else 'Failed'
            note = f"✅ VOTE PASSED.{passed_note_suffix}" if new_status != 'Failed' else "❌ VOTE FAILED. No simple majority."
    else:  # Vetoed
        required = two_thirds_threshold(max(total_yes_no, 1))
        if yes >= required:
            new_status = 'Bill is Now Law'
            note = f"⚔️ VETO OVERRIDDEN with {yes}/{total_yes_no} in favor."
        else:
            new_status = 'Failed'
            note = f"🛡️ VETO UPHELD (needed {required} {SPAN['YES']}; got {yes})."

    # Update database
    await asyncio.to_thread(lambda: ref.update({'status': new_status}))

    # Send results
    vis = bill.get('visibility', 'PUBLIC')
    embed = results_embed(guild, {**bill, 'status': new_status})
    target_channel = source_channel
    if vis == 'CONFIDENTIAL' and PRIVATE_RESULTS_CHANNEL_ID and guild:
        private = guild.get_channel(PRIVATE_RESULTS_CHANNEL_ID)
        if private:
            target_channel = private

    if target_channel:
        # Only show the embed - no separate note message
        if is_auto:
            await target_channel.send("⏰ **24-Hour Voting Period Ended**", embed=embed)
        else:
            await target_channel.send(embed=embed)

    return True, "Finalized."


async def notify_councilors_new_vote(guild, bill, voting_channel):
    """Notify all Royal Councilors via DM when a new bill enters voting."""
    try:
        if not guild:
            return

        councilor_role = guild.get_role(ROYAL_COUNCILOR_ROLE_ID)
        if not councilor_role:
            print("[NOTIFY] Royal Councilor role not found")
            return

        bill_title = bill.get('title', 'Untitled Bill')

        # Simple, brief notification
        notification = f"New bill ready for vote: **{bill_title}**"

        dm_count = 0
        for member in councilor_role.members:
            try:
                await member.send(notification)
                dm_count += 1
            except Exception as dm_error:
                print(f"[NOTIFY] Could not DM {member.display_name}: {dm_error}")

        print(f"[NOTIFY] Sent {dm_count} DM notifications for bill {bill_title}")
    except Exception as e:
        print(f"[NOTIFY] Error sending notifications: {e}")
