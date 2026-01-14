import asyncio
from datetime import datetime, timezone

import discord
from discord import ui

from access_control import SOBERANTE_ROLE_ID, has_admin_role, has_citizen_role
from bill_helpers import find_bill_by_id_sync, get_bill_embed, get_next_bill_number
from bill_workflow import finalize_bill, notify_councilors_new_vote
from constants import DOMAINS, SPAN, get_display_status
from settings import MONARCH_ROLE_ID, REQUIRED_CO_SPONSORS_DEFAULT, VOTING_CHANNEL_ID


class BillConsole(ui.View):
    def __init__(self, bill_id: str):
        super().__init__(timeout=None)
        self.bill_id = bill_id

        # Get bill status to conditionally show buttons
        _, bill = find_bill_by_id_sync(bill_id)
        if bill:
            status = bill.get('status', 'Pending')

            # Show sponsor and co-sponsor buttons when Awaiting Sponsor
            if status == 'Awaiting Sponsor':
                self.add_item(SponsorButton())
                self.add_item(CoSponsorButton())
                self.add_item(ToggleConfidentialityButton())

            # Show co-sponsor button only when Pending
            elif status == 'Pending':
                self.add_item(CoSponsorButton())
                self.add_item(ToggleConfidentialityButton())

            # Show voting dropdown only when Voting or Vetoed (no confidentiality toggle during voting)
            elif status in ('Voting', 'Vetoed'):
                self.add_item(VotingActionSelect(bill_id))

            # Show Soberante actions when bill is Passed (enact as law or veto)
            elif status == 'Passed':
                self.add_item(SoberanteActionSelect())

    def _get(self):
        return find_bill_by_id_sync(self.bill_id)

    async def _refresh(self, interaction):
        _, bill = self._get()
        if not bill:
            return
        try:
            # Recreate view with updated button state
            new_view = BillConsole(self.bill_id)
            # Fetch the message fresh to avoid race conditions
            channel = interaction.channel
            if channel and interaction.message:
                try:
                    message = await channel.fetch_message(interaction.message.id)
                    await message.edit(embed=get_bill_embed(bill), view=new_view)
                except Exception:
                    # If fetch fails, try direct edit
                    await interaction.message.edit(embed=get_bill_embed(bill), view=new_view)
        except Exception as e:
            print(f"[WARN] Bill refresh failed: {e}")
            pass

    def _is_sponsor(self, user_id: int) -> bool:
        _, bill = self._get()
        if not bill:
            return False
        return bill.get('sponsorId') == user_id

    def _is_monarch(self, interaction: discord.Interaction) -> bool:
        if MONARCH_ROLE_ID == 0:
            return True
        if not hasattr(interaction.user, "roles"):
            return False
        return any(getattr(r, "id", 0) == MONARCH_ROLE_ID for r in interaction.user.roles)


class SponsorDomainSelect(ui.Select):
    def __init__(self, bill_id: str):
        self.bill_id = bill_id
        options = [
            discord.SelectOption(label=domain, value=domain, emoji="📋")
            for domain in DOMAINS
        ]
        super().__init__(placeholder="Select your Domain/Role as Sponsor...", options=options, custom_id=f"sponsor_domain_{bill_id}")

    async def callback(self, interaction: discord.Interaction):
        selected_domain = self.values[0]

        # Get bill from database
        ref, bill = find_bill_by_id_sync(self.bill_id)
        if not ref or not bill:
            return await interaction.response.send_message("Edict not found.", ephemeral=True)

        uid = interaction.user.id

        # Get next bill number
        bill_number = get_next_bill_number()

        # Update title to include R.C. number
        original_title = bill.get('title', 'Untitled')
        bill_title = original_title
        if bill_number and not original_title.startswith('R.C.'):
            bill_title = f"R.C. {bill_number:03d} - {original_title}"

        # Claim sponsorship and advance to Voting
        updates = {
            'sponsorId': uid,
            'sponsorTag': interaction.user.mention,
            'sponsorDomain': selected_domain,
            'status': 'Voting',
            'votingStartAt': datetime.now(timezone.utc),
        }

        if bill_number:
            updates['title'] = bill_title
            updates['billNumber'] = bill_number

        await asyncio.to_thread(lambda: ref.update(updates))
        await interaction.response.send_message(f"✅ You are now the Sponsor with **{selected_domain}** role!", ephemeral=True)

        # Move bill to voting channel if configured
        try:
            # Wrap blocking .get() call
            updated_bill = await asyncio.to_thread(lambda: ref.get().to_dict())
            channel_id = bill.get('channelId')
            message_id = bill.get('messageId')

            if VOTING_CHANNEL_ID and interaction.guild and channel_id and message_id:
                voting_channel = interaction.guild.get_channel(VOTING_CHANNEL_ID)
                old_channel = interaction.guild.get_channel(channel_id)

                if voting_channel and old_channel and voting_channel.id != channel_id:
                    # Delete old message
                    try:
                        old_message = await old_channel.fetch_message(message_id)
                        await old_message.delete()
                    except Exception:
                        pass

                    # Post to voting channel
                    new_message = await voting_channel.send(
                        embed=get_bill_embed(updated_bill),
                        view=BillConsole(bill_id=self.bill_id),
                    )
                    await asyncio.to_thread(lambda: ref.update({'messageId': new_message.id, 'channelId': voting_channel.id}))
                    # Notify councilors about new vote
                    await notify_councilors_new_vote(interaction.guild, updated_bill, voting_channel)
        except Exception as e:
            print(f"[WARN] Could not move bill to voting channel: {e}")


class SponsorDomainSelectView(ui.View):
    def __init__(self, bill_id: str):
        super().__init__(timeout=180)
        self.add_item(SponsorDomainSelect(bill_id))


class SponsorButton(ui.Button):
    def __init__(self):
        super().__init__(label="👤 Claim Sponsorship", style=discord.ButtonStyle.primary, custom_id="btn_sponsor")

    async def callback(self, interaction: discord.Interaction):
        view: BillConsole = self.view
        ref, bill = view._get()
        if not ref or not bill:
            return await interaction.response.send_message("Edict not found or database unavailable.", ephemeral=True)
        if bill.get('status') != 'Awaiting Sponsor':
            return await interaction.response.send_message("Sponsorship already claimed.", ephemeral=True)
        if bill.get('sponsorId'):
            return await interaction.response.send_message("This edict already has a sponsor.", ephemeral=True)

        uid = interaction.user.id
        co = bill.get('coSponsors', [])
        if uid in co:
            return await interaction.response.send_message("You already co-sponsored this edict. Cannot be both sponsor and co-sponsor.", ephemeral=True)

        # Show domain selector for sponsor
        bill_id = bill.get('id')
        await interaction.response.send_message(
            "**Select Your Domain/Role as Sponsor**\nChoose which domain you represent or select Soberante:",
            view=SponsorDomainSelectView(bill_id),
            ephemeral=True,
        )


class DomainSelect(ui.Select):
    def __init__(self, bill_id: str):
        self.bill_id = bill_id
        options = [
            discord.SelectOption(label=domain, value=domain, emoji="📋")
            for domain in DOMAINS
        ]
        super().__init__(placeholder="Select your Domain role...", options=options, custom_id=f"domain_select_{bill_id}")

    async def callback(self, interaction: discord.Interaction):
        selected_domain = self.values[0]

        # Get bill from database
        ref, bill = find_bill_by_id_sync(self.bill_id)
        if not ref or not bill:
            return await interaction.response.send_message("Edict not found.", ephemeral=True)

        uid = interaction.user.id
        sponsor_id = bill.get('sponsorId')
        if sponsor_id == uid:
            return await interaction.response.send_message("Sponsor cannot co-sponsor.", ephemeral=True)

        # Check if already co-sponsored
        co_sponsors = bill.get('coSponsorDetails', [])
        if any(cs.get('userId') == uid for cs in co_sponsors):
            return await interaction.response.send_message("You already co-sponsored this edict.", ephemeral=True)

        # Add co-sponsor with domain
        co_sponsors.append({
            'userId': uid,
            'mention': interaction.user.mention,
            'domain': selected_domain,
        })

        updates = {'coSponsorDetails': co_sponsors}

        # Also update old coSponsors list for backwards compatibility
        co_ids = [cs['userId'] for cs in co_sponsors]
        updates['coSponsors'] = co_ids

        # Advance to voting with 2 co-sponsors
        required = bill.get('requiredCoSponsors', REQUIRED_CO_SPONSORS_DEFAULT)
        status_changed_to_voting = False
        if len(co_sponsors) >= required:
            # Get next bill number
            bill_number = get_next_bill_number()
            if bill_number:
                # Update title to include R.C. number
                original_title = bill.get('title', 'Untitled')
                if not original_title.startswith('R.C.'):
                    updates['title'] = f"R.C. {bill_number:03d} - {original_title}"
                    updates['billNumber'] = bill_number

            updates['status'] = 'Voting'
            updates['votingStartAt'] = datetime.now(timezone.utc)
            status_changed_to_voting = True

        await asyncio.to_thread(lambda: ref.update(updates))
        await interaction.response.send_message(f"✅ Co-sponsorship recorded for **{selected_domain}**!", ephemeral=True)

        # Refresh or move the bill message
        try:
            channel_id = bill.get('channelId')
            message_id = bill.get('messageId')
            # Wrap blocking .get() call
            updated_bill = await asyncio.to_thread(lambda: ref.get().to_dict())

            if channel_id and message_id and interaction.guild:
                old_channel = interaction.guild.get_channel(channel_id)

                # If status changed to Voting, move to voting channel
                if status_changed_to_voting and VOTING_CHANNEL_ID:
                    voting_channel = interaction.guild.get_channel(VOTING_CHANNEL_ID)
                    if voting_channel and voting_channel.id != channel_id:
                        # Delete old message
                        if old_channel:
                            try:
                                old_message = await old_channel.fetch_message(message_id)
                                await old_message.delete()
                            except Exception:
                                pass

                        # Post to voting channel
                        new_message = await voting_channel.send(
                            embed=get_bill_embed(updated_bill),
                            view=BillConsole(bill_id=self.bill_id),
                        )
                        await asyncio.to_thread(lambda: ref.update({'messageId': new_message.id, 'channelId': voting_channel.id}))
                        # Notify councilors about new vote
                        await notify_councilors_new_vote(interaction.guild, updated_bill, voting_channel)
                        return

                # Otherwise just update the existing message
                if old_channel:
                    bill_message = await old_channel.fetch_message(message_id)
                    await bill_message.edit(embed=get_bill_embed(updated_bill), view=BillConsole(bill_id=self.bill_id))
        except Exception as e:
            print(f"[WARN] Could not refresh bill message: {e}")


class DomainSelectView(ui.View):
    def __init__(self, bill_id: str):
        super().__init__(timeout=180)
        self.add_item(DomainSelect(bill_id))


class CoSponsorButton(ui.Button):
    def __init__(self):
        super().__init__(label="🤝 Add Co-Sponsorship", style=discord.ButtonStyle.success, custom_id="btn_cosponsor")

    async def callback(self, interaction: discord.Interaction):
        view: BillConsole = self.view

        # RESPOND IMMEDIATELY to avoid timeout
        await interaction.response.send_message("⏳ Loading co-sponsorship...", ephemeral=True)

        ref, bill = view._get()
        if not ref or not bill:
            return await interaction.edit_original_response(content="Edict not found or database unavailable.")

        status = bill.get('status')
        if status not in ('Awaiting Sponsor', 'Pending'):
            return await interaction.edit_original_response(content="Not open for co-sponsorship.")

        uid = interaction.user.id
        sponsor_id = bill.get('sponsorId')
        if sponsor_id == uid:
            return await interaction.edit_original_response(content="Sponsor cannot co-sponsor.")

        # Check if already co-sponsored (check both old and new format)
        co_sponsors = bill.get('coSponsorDetails', [])
        if any(cs.get('userId') == uid for cs in co_sponsors):
            return await interaction.edit_original_response(content="You already co-sponsored this edict.")

        # Show domain selector
        bill_id = bill.get('id')
        await interaction.edit_original_response(
            content="**Select Your Domain Role**\nChoose which domain you represent as co-sponsor:",
            view=DomainSelectView(bill_id),
        )


class VotingActionSelect(ui.Select):
    def __init__(self, bill_id: str):
        self.bill_id = bill_id
        options = [
            discord.SelectOption(label=SPAN['YES'], value="yes"),
            discord.SelectOption(label=SPAN['NO'], value="no"),
            discord.SelectOption(label=SPAN['ABSTAIN'], value="abstain"),
            discord.SelectOption(label="Finalize Bill", value="finalize"),
        ]
        super().__init__(
            placeholder="Select voting action...",
            options=options,
            custom_id=f"vote_action_{bill_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        view: BillConsole = self.view
        action = self.values[0]

        # RESPOND IMMEDIATELY to avoid timeout
        if action == "finalize":
            await interaction.response.send_message("🏁 Finalizing bill...", ephemeral=True)
        else:
            await interaction.response.send_message("⏳ Recording vote...", ephemeral=True)

        ref, bill = view._get()
        if not ref or not bill:
            return await interaction.edit_original_response(content="Edict not found or database unavailable.")

        # Handle finalize action
        if action == "finalize":
            # ONLY Soberante can finalize
            if not view._is_monarch(interaction):
                return await interaction.edit_original_response(content="Only Soberante can finalize bills.")

            success, message = await finalize_bill(ref, bill, interaction.guild, interaction.channel, is_auto=False)
            await interaction.edit_original_response(content=f"{'✅' if success else '❌'} {message}")
            await view._refresh(interaction)
            return

        # Handle voting actions
        if not has_citizen_role(interaction):
            return await interaction.edit_original_response(content="Only Consejeros Reales can vote on bills.")

        if bill.get('status') not in ('Voting', 'Vetoed'):
            return await interaction.edit_original_response(content="Voting is not open.")

        uid = interaction.user.id
        votes = bill.get('votes', {'yes': [], 'no': [], 'abstain': []})

        # Remove user from all vote categories
        votes['yes'] = [x for x in votes.get('yes', []) if x != uid]
        votes['no'] = [x for x in votes.get('no', []) if x != uid]
        votes['abstain'] = [x for x in votes.get('abstain', []) if x != uid]

        # Add to selected category
        if action == "yes" and uid not in votes['yes']:
            votes['yes'].append(uid)
            await interaction.edit_original_response(content=f"✅ Voted **{SPAN['YES']}**")
        elif action == "no" and uid not in votes['no']:
            votes['no'].append(uid)
            await interaction.edit_original_response(content=f"❌ Voted **{SPAN['NO']}**")
        elif action == "abstain" and uid not in votes['abstain']:
            votes['abstain'].append(uid)
            await interaction.edit_original_response(content=f"⚪ Recorded **{SPAN['ABSTAIN']}**")

        await asyncio.to_thread(lambda: ref.update({'votes': votes}))
        await view._refresh(interaction)


class SoberanteActionSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Enact as Law", value="enact"),
            discord.SelectOption(label="Veto", value="veto"),
        ]
        super().__init__(
            placeholder="👑 Soberante Actions...",
            options=options,
            custom_id="soberante_action_select",
        )

    async def callback(self, interaction: discord.Interaction):
        view: BillConsole = self.view
        action = self.values[0]

        # RESPOND IMMEDIATELY to avoid timeout
        if action == "enact":
            await interaction.response.send_message("📜 Enacting bill as law...", ephemeral=True)
        else:
            await interaction.response.send_message("🛑 Vetoing bill...", ephemeral=True)

        # ONLY Soberante can use this dropdown
        if not view._is_monarch(interaction):
            return await interaction.edit_original_response(content="Only Soberante can enact or veto bills.")

        ref, bill = view._get()
        if not ref or not bill:
            return await interaction.edit_original_response(content="Edict not found or database unavailable.")

        if bill.get('status') != 'Passed':
            return await interaction.edit_original_response(content="Only passed bills can be enacted or vetoed.")

        # Handle enact action
        if action == "enact":
            # LOG who enacted the bill
            bill_id = bill.get('id', 'UNKNOWN')
            user_tag = f"{interaction.user.name}#{interaction.user.discriminator}" if interaction.user.discriminator != "0" else interaction.user.name
            print(f"[ENACT LAW] Bill {bill_id} enacted as law by {user_tag} (ID: {interaction.user.id})")

            # Update status to Bill is Now Law
            await asyncio.to_thread(lambda: ref.update({'status': 'Bill is Now Law'}))

            bill_type = bill.get('billType', 'STANDARD')
            display_status = get_display_status('Bill is Now Law', bill_type)
            await interaction.edit_original_response(content=f"✅ Bill has been enacted as **{display_status}** by {interaction.user.mention}!")

        # Handle veto action
        elif action == "veto":
            # Update status to Vetoed and add note
            await asyncio.to_thread(lambda: ref.update({
                'status': 'Vetoed',
                'vetoNote': '🛑 Bill vetoed by Soberante. Requires 2/3 override.',
            }))

            await interaction.edit_original_response(content="🛑 Bill has been **vetoed** by Soberante!")

        await view._refresh(interaction)


class ToggleConfidentialityButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔒 Toggle Confidentiality", style=discord.ButtonStyle.secondary, custom_id="btn_toggle_conf")

    async def callback(self, interaction: discord.Interaction):
        view: BillConsole = self.view

        # RESPOND IMMEDIATELY to avoid timeout
        await interaction.response.send_message("⏳ Toggling confidentiality...", ephemeral=True)

        ref, bill = view._get()
        if not ref or not bill:
            return await interaction.edit_original_response(content="Edict not found or database unavailable.")

        # Cannot change confidentiality once voting has started
        status = bill.get('status')
        if status in ('Voting', 'Vetoed', 'Passed', 'Failed', 'Bill is Now Law'):
            return await interaction.edit_original_response(content="⚠️ Cannot change confidentiality once voting has started.")

        # Only sponsor or proposer can toggle confidentiality
        uid = interaction.user.id
        sponsor_id = bill.get('sponsorId')
        proposer_id = bill.get('proposerId')

        if uid != sponsor_id and uid != proposer_id:
            return await interaction.edit_original_response(content="Only the sponsor or proposer can toggle confidentiality.")

        current_vis = bill.get('visibility', 'PUBLIC')
        new_vis = 'CONFIDENTIAL' if current_vis == 'PUBLIC' else 'PUBLIC'
        await asyncio.to_thread(lambda: ref.update({'visibility': new_vis}))

        vis_emoji = "🔒" if new_vis == 'CONFIDENTIAL' else "🔓"
        await interaction.edit_original_response(content=f"{vis_emoji} Voting is now **{new_vis}**")
        await view._refresh(interaction)


class EnactAsLawButton(ui.Button):
    def __init__(self):
        super().__init__(label="📜 Enact as Law", style=discord.ButtonStyle.success, custom_id="btn_enact_law")

    async def callback(self, interaction: discord.Interaction):
        try:
            view: BillConsole = self.view

            # RESPOND IMMEDIATELY to avoid timeout
            await interaction.response.send_message("📜 Enacting bill as law...", ephemeral=True)

            is_soberante = False
            if hasattr(interaction.user, "roles"):
                is_soberante = any(getattr(r, "id", 0) == SOBERANTE_ROLE_ID for r in interaction.user.roles)

            if not is_soberante:
                return await interaction.edit_original_response(content=f"❌ Only <@&{SOBERANTE_ROLE_ID}> (Soberante) can enact bills as Law.")

            ref, bill = view._get()
            if not ref or not bill:
                return await interaction.edit_original_response(content="Edict not found or database unavailable.")

            if bill.get('status') != 'Passed':
                return await interaction.edit_original_response(content="Only passed bills can be enacted as Law.")

            # LOG who enacted the bill
            bill_id = bill.get('id', 'UNKNOWN')
            user_tag = f"{interaction.user.name}#{interaction.user.discriminator}" if interaction.user.discriminator != "0" else interaction.user.name
            print(f"[ENACT LAW] Bill {bill_id} enacted as law by {user_tag} (ID: {interaction.user.id})")

            # Update status to Bill is Now Law
            await asyncio.to_thread(lambda: ref.update({'status': 'Bill is Now Law'}))

            bill_type = bill.get('billType', 'STANDARD')
            display_status = get_display_status('Bill is Now Law', bill_type)
            await interaction.edit_original_response(content=f"✅ Bill has been enacted as **{display_status}** by {interaction.user.mention}!")
            await view._refresh(interaction)
        except Exception as e:
            print(f"[ERR] EnactAsLawButton callback failed: {e}")
            import traceback
            traceback.print_exc()
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
                else:
                    await interaction.edit_original_response(content=f"❌ Error: {e}")
            except Exception:
                pass


class VetoPassedBillButton(ui.Button):
    def __init__(self):
        super().__init__(label="🛑 Veto", style=discord.ButtonStyle.danger, custom_id="btn_veto_passed")

    async def callback(self, interaction: discord.Interaction):
        view: BillConsole = self.view

        # RESPOND IMMEDIATELY to avoid timeout
        await interaction.response.send_message("🛑 Vetoing bill...", ephemeral=True)

        # Only Monarch (Soberante) or Administrador can veto
        if not (view._is_monarch(interaction) or has_admin_role(interaction)):
            return await interaction.edit_original_response(content="Only Soberante or Administrador can veto bills.")

        ref, bill = view._get()
        if not ref or not bill:
            return await interaction.edit_original_response(content="Edict not found or database unavailable.")

        if bill.get('status') != 'Passed':
            return await interaction.edit_original_response(content="Only passed bills can be vetoed.")

        # Update status to Vetoed and add note
        await asyncio.to_thread(lambda: ref.update({
            'status': 'Vetoed',
            'vetoNote': '🛑 Bill vetoed by Soberante. Requires 2/3 override.',
        }))

        await interaction.edit_original_response(content="🛑 Bill has been **vetoed** by Soberante!")
        await view._refresh(interaction)
