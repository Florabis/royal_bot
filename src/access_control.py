import os

import discord
from google.cloud.firestore_v1.base_query import FieldFilter

from firestore_setup import db
from settings import CITIZENS_COLLECTION, SNITCH_LOGS_COLLECTION, UNIVERSAL_CITIZEN_ROLE_ID

# ========================================
# ADMIN & CITIZEN TRACKING SYSTEM
# ========================================

ADMIN_ROLE_ID = 1424247988750123088
MAGISTRATE_ROLE_ID = 1412219625927868517  # Florabís Magistrates (Court Magistrates)
REPORTER_ROLE_ID = int(os.getenv("REPORTER_ROLE_ID", "0"))  # News reporters who can observe court threads
SOBERANTE_ROLE_ID = 1407064681226440885
WARRANT_MANAGER_ROLE_ID = 1410062792672809083
BANCQUERO_ROLE_ID = 1429923363013226526  # Bancquero - Financial Management Role
TREASURY_MANAGER_ROLE_ID = 1428548017258238023  # Treasury Manager - Banking oversight
WARRANT_MANAGER_ROLE_2_ID = 1410082540643025060
# Government Role Aliases for Website Sync
ROYAL_COUNCILOR_ROLE_ID = 1410063508321861742  # Consejero Reales - Royal Councilors
ALCALDE_MAYOR_ROLE_ID = WARRANT_MANAGER_ROLE_ID  # Alcalde Mayor = Warrant Manager
CAPITAN_ROLE_ID = WARRANT_MANAGER_ROLE_2_ID  # Capitán de la Guardia
BETTING_MANAGER_ROLE_ID = 1429189199713796167


def has_admin_role(interaction: discord.Interaction) -> bool:
    """Check if user has the admin role (ID: 1424247988750123088)."""
    if not hasattr(interaction.user, "roles"):
        return False
    return any(getattr(r, "id", 0) == ADMIN_ROLE_ID for r in interaction.user.roles)


def has_magistrate_role(interaction: discord.Interaction) -> bool:
    """Check if user has the magistrate role or admin role."""
    if not hasattr(interaction.user, "roles"):
        return False
    return any(getattr(r, "id", 0) in [ADMIN_ROLE_ID, MAGISTRATE_ROLE_ID] for r in interaction.user.roles)


def has_warrant_role(interaction: discord.Interaction) -> bool:
    """Check if user has warrant management permissions (Admin, Magistrate, Soberante, or Warrant Manager)."""
    if not hasattr(interaction.user, "roles"):
        return False
    return any(
        getattr(r, "id", 0) in [
            ADMIN_ROLE_ID,
            MAGISTRATE_ROLE_ID,
            SOBERANTE_ROLE_ID,
            WARRANT_MANAGER_ROLE_ID,
            WARRANT_MANAGER_ROLE_2_ID,
        ]
        for r in interaction.user.roles
    )


def is_citizen(user_id: int) -> bool:
    """Check if a user is registered as a citizen in the database."""
    if not db:
        return False
    q = db.collection(CITIZENS_COLLECTION).where(filter=FieldFilter('userId', '==', user_id)).limit(1)
    for _ in q.stream():
        return True
    return False


def has_citizen_role(interaction: discord.Interaction) -> bool:
    """Check if user has voting role (Consejero Reales or Soberante)."""
    # Voting allowed roles
    voting_role_ids = [ROYAL_COUNCILOR_ROLE_ID, SOBERANTE_ROLE_ID]

    if not hasattr(interaction.user, "roles"):
        return False

    # Check if user has any of the voting roles
    return any(getattr(r, "id", 0) in voting_role_ids for r in interaction.user.roles)


def is_citizen_by_role(interaction: discord.Interaction) -> bool:
    """Check if user has the universal citizen Discord role."""
    if not hasattr(interaction.user, "roles"):
        return False
    # Check for universal citizen role that ALL citizens should have
    return any(getattr(r, "id", 0) == UNIVERSAL_CITIZEN_ROLE_ID for r in interaction.user.roles)


def has_snitch_hit(ign: str) -> bool:
    """Check if IGN has at least one snitch hit logged (exact match)."""
    if not db:
        return False
    q = db.collection(SNITCH_LOGS_COLLECTION).where(filter=FieldFilter('player', '==', ign)).limit(1)
    for _ in q.stream():
        return True
    return False
