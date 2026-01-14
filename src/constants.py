import discord

# ---------- CONSTANTS ----------
BILL_STATUSES = {
    'AWAITING_SPONSOR': 'Awaiting Sponsor',
    'PENDING': 'Pending',
    'VOTING': 'Voting',
    'PASSED': 'Passed',
    'VETOED': 'Vetoed',
    'LAW': 'Bill is Now Law',
    'FAILED': 'Failed',
}
STATUS_EMOJIS = {
    'Awaiting Sponsor': '🔍',
    'Pending': '📝',
    'Voting': '🗳️',
    'Passed': '✅',
    'Vetoed': '🛑',
    'Bill is Now Law': '📜 Enact as Law',
    'Failed': '❌',
}

# Only these Spanish tokens in the UI
SPAN = {
    "YES": "Sí",
    "NO": "No",
    "ABSTAIN": "Abstención",
    "COUNCILOR": "Consejero Reales",
    "SOVEREIGN": "Soberante",
    "DOMAINS": "Domains (Dominios)",
}


# Display status helper - maps internal status to user-friendly text
def get_display_status(status: str, bill_type: str = None) -> str:
    """Convert internal status to display text based on bill type."""
    if status == 'Bill is Now Law':
        if bill_type == 'CONSTITUTIONAL_AMENDMENT':
            return 'Constitutional Law'
        return 'State Law'
    return status


# Court System Translations (EN, ES, FR, DE)
COURT_TRANSLATIONS = {
    "en": {
        "court_panel_title": "⚖️ FLORABÍS STATE JUDICIARY",
        "court_panel_desc": "*Access court services, file cases, or register as legal counsel*",
        "file_case": "📋 File Case",
        "register_lawyer": "👨‍⚖️ Register as Lawyer",
        "view_lawyers": "📜 View Lawyers",
        "search_cases": "🔍 Search Cases",
        "criminal_case": "⚖️ Criminal Case",
        "civil_case": "📄 Civil Case",
        "normal_severity": "Normal",
        "serious_severity": "Serious",
        "case_type": "Case Type",
        "severity": "Severity",
        "defendant_ign": "Defendant IGN",
        "defendant_ign_placeholder": "Enter defendant's in-game name",
        "charges": "Charges/Complaint",
        "charges_placeholder": "Describe the charges or complaint",
        "evidence": "Evidence",
        "evidence_placeholder": "Links, screenshots, witness testimony, etc.",
        "case_filed": "✅ Case Filed Successfully",
        "case_id": "Case ID",
        "thread": "Thread",
        "check_thread": "Check your private courtroom thread for details",
        "courtroom_action_panel": "⚖️ COURTROOM ACTION PANEL",
        "use_buttons_below": "Use the buttons below to claim roles or take actions.",
        "claim_judge": "👨‍⚖️ Claim Judge",
        "claim_prosecutor": "⚔️ Claim Prosecutor",
        "claim_defense": "🛡️ Claim Defense",
        "join_counsel": "👔 Join as Counsel",
        "file_motion": "📝 File Motion",
        "request_evidence": "🔍 Request Evidence",
        "close_case": "🔒 Close Case",
        "attorney": "Attorney",
        "public_defender": "Public Defender",
        "state_prosecutor": "State Prosecutor",
        "lawyer_type": "Lawyer Type",
        "your_ign": "Your IGN",
        "ign_placeholder": "Enter your in-game name",
        "registered_lawyer": "✅ Registered as Legal Counsel",
        "bar_number": "Bar Number",
        "type": "Type",
        "already_registered": "⚠️ Already Registered",
        "already_lawyer": "You are already registered as a lawyer",
        "no_courtroom_thread": "❌ No courtroom thread found for this case.",
        "error": "❌ Error",
        "db_unavailable": "Database not available",
        "admin_only": "Only administrators can use this command",
        "magistrate_only": "Only administrators and magistrates can use this command",
    },
    "es": {
        "court_panel_title": "⚖️ PODER JUDICIAL DE FLORABÍS",
        "court_panel_desc": "*Accede a servicios judiciales, presenta casos o regístrate como abogado*",
        "file_case": "📋 Presentar Caso",
        "register_lawyer": "👨‍⚖️ Registrarse como Abogado",
        "view_lawyers": "📜 Ver Abogados",
        "search_cases": "🔍 Buscar Casos",
        "criminal_case": "⚖️ Caso Criminal",
        "civil_case": "📄 Caso Civil",
        "normal_severity": "Normal",
        "serious_severity": "Grave",
        "case_type": "Tipo de Caso",
        "severity": "Gravedad",
        "defendant_ign": "IGN del Acusado",
        "defendant_ign_placeholder": "Ingrese el nombre en juego del acusado",
        "charges": "Cargos/Queja",
        "charges_placeholder": "Describa los cargos o queja",
        "evidence": "Evidencia",
        "evidence_placeholder": "Enlaces, capturas, testimonio, etc.",
        "case_filed": "✅ Caso Presentado Exitosamente",
        "case_id": "ID del Caso",
        "thread": "Hilo",
        "check_thread": "Revise su hilo privado de sala para detalles",
        "courtroom_action_panel": "⚖️ PANEL DE ACCIÓN DE SALA",
        "use_buttons_below": "Use los botones para reclamar roles o tomar acciones.",
        "claim_judge": "👨‍⚖️ Reclamar Juez",
        "claim_prosecutor": "⚔️ Reclamar Fiscal",
        "claim_defense": "🛡️ Reclamar Defensa",
        "join_counsel": "👔 Unirse como Abogado",
        "file_motion": "📝 Presentar Moción",
        "request_evidence": "🔍 Solicitar Evidencia",
        "close_case": "🔒 Cerrar Caso",
        "attorney": "Abogado",
        "public_defender": "Defensor Público",
        "state_prosecutor": "Fiscal del Estado",
        "lawyer_type": "Tipo de Abogado",
        "your_ign": "Su IGN",
        "ign_placeholder": "Ingrese su nombre en juego",
        "registered_lawyer": "✅ Registrado como Abogado",
        "bar_number": "Número de Matrícula",
        "type": "Tipo",
        "already_registered": "⚠️ Ya Registrado",
        "already_lawyer": "Ya está registrado como abogado",
        "no_courtroom_thread": "❌ No se encontró hilo de sala para este caso.",
        "error": "❌ Error",
        "db_unavailable": "Base de datos no disponible",
        "admin_only": "Solo los administradores pueden usar este comando",
        "magistrate_only": "Solo administradores y magistrados pueden usar este comando",
    },
    "fr": {
        "court_panel_title": "⚖️ SYSTÈME JUDICIAIRE DE FLORABÍS",
        "court_panel_desc": "*Accédez aux services judiciaires, déposez des affaires ou inscrivez-vous comme avocat*",
        "file_case": "📋 Déposer une Affaire",
        "register_lawyer": "👨‍⚖️ S'inscrire comme Avocat",
        "view_lawyers": "📜 Voir les Avocats",
        "search_cases": "🔍 Rechercher des Affaires",
        "criminal_case": "⚖️ Affaire Criminelle",
        "civil_case": "📄 Affaire Civile",
        "normal_severity": "Normal",
        "serious_severity": "Grave",
        "case_type": "Type d'Affaire",
        "severity": "Gravité",
        "defendant_ign": "IGN du Défendeur",
        "defendant_ign_placeholder": "Entrez le nom en jeu du défendeur",
        "charges": "Accusations/Plainte",
        "charges_placeholder": "Décrivez les accusations ou la plainte",
        "evidence": "Preuves",
        "evidence_placeholder": "Liens, captures d'écran, témoignages, etc.",
        "case_filed": "✅ Affaire Déposée avec Succès",
        "case_id": "ID de l'Affaire",
        "thread": "Fil",
        "check_thread": "Consultez votre fil de salle d'audience privé pour plus de détails",
        "courtroom_action_panel": "⚖️ PANNEAU D'ACTION DE SALLE",
        "use_buttons_below": "Utilisez les boutons ci-dessous pour revendiquer des rôles ou prendre des mesures.",
        "claim_judge": "👨‍⚖️ Revendiquer Juge",
        "claim_prosecutor": "⚔️ Revendiquer Procureur",
        "claim_defense": "🛡️ Revendiquer Défense",
        "join_counsel": "👔 Rejoindre comme Avocat",
        "file_motion": "📝 Déposer une Motion",
        "request_evidence": "🔍 Demander des Preuves",
        "close_case": "🔒 Fermer l'Affaire",
        "attorney": "Avocat",
        "public_defender": "Défenseur Public",
        "state_prosecutor": "Procureur de l'État",
        "lawyer_type": "Type d'Avocat",
        "your_ign": "Votre IGN",
        "ign_placeholder": "Entrez votre nom en jeu",
        "registered_lawyer": "✅ Inscrit comme Avocat",
        "bar_number": "Numéro de Barreau",
        "type": "Type",
        "already_registered": "⚠️ Déjà Inscrit",
        "already_lawyer": "Vous êtes déjà inscrit comme avocat",
        "no_courtroom_thread": "❌ Aucun fil de salle d'audience trouvé pour cette affaire.",
        "error": "❌ Erreur",
        "db_unavailable": "Base de données non disponible",
        "admin_only": "Seuls les administrateurs peuvent utiliser cette commande",
        "magistrate_only": "Seuls les administrateurs et magistrats peuvent utiliser cette commande",
    },
    "de": {
        "court_panel_title": "⚖️ JUSTIZWESEN VON FLORABÍS",
        "court_panel_desc": "*Zugang zu Gerichtsdiensten, Fälle einreichen oder als Anwalt registrieren*",
        "file_case": "📋 Fall Einreichen",
        "register_lawyer": "👨‍⚖️ Als Anwalt Registrieren",
        "view_lawyers": "📜 Anwälte Ansehen",
        "search_cases": "🔍 Fälle Suchen",
        "criminal_case": "⚖️ Straffall",
        "civil_case": "📄 Zivilfall",
        "normal_severity": "Normal",
        "serious_severity": "Schwerwiegend",
        "case_type": "Falltyp",
        "severity": "Schweregrad",
        "defendant_ign": "IGN des Angeklagten",
        "defendant_ign_placeholder": "Geben Sie den Spielnamen des Angeklagten ein",
        "charges": "Anklagen/Beschwerde",
        "charges_placeholder": "Beschreiben Sie die Anklagen oder Beschwerde",
        "evidence": "Beweise",
        "evidence_placeholder": "Links, Screenshots, Zeugenaussagen, usw.",
        "case_filed": "✅ Fall Erfolgreich Eingereicht",
        "case_id": "Fall-ID",
        "thread": "Thread",
        "check_thread": "Überprüfen Sie Ihren privaten Gerichtssaal-Thread für Details",
        "courtroom_action_panel": "⚖️ GERICHTSSAAL-AKTIONSPANEL",
        "use_buttons_below": "Verwenden Sie die Schaltflächen unten, um Rollen zu beanspruchen oder Maßnahmen zu ergreifen.",
        "claim_judge": "👨‍⚖️ Richter Beanspruchen",
        "claim_prosecutor": "⚔️ Staatsanwalt Beanspruchen",
        "claim_defense": "🛡️ Verteidigung Beanspruchen",
        "join_counsel": "👔 Als Anwalt Beitreten",
        "file_motion": "📝 Antrag Einreichen",
        "request_evidence": "🔍 Beweise Anfordern",
        "close_case": "🔒 Fall Schließen",
        "attorney": "Anwalt",
        "public_defender": "Pflichtverteidiger",
        "state_prosecutor": "Staatsanwalt",
        "lawyer_type": "Anwaltstyp",
        "your_ign": "Ihr IGN",
        "ign_placeholder": "Geben Sie Ihren Spielnamen ein",
        "registered_lawyer": "✅ Als Anwalt Registriert",
        "bar_number": "Anwaltsnummer",
        "type": "Typ",
        "already_registered": "⚠️ Bereits Registriert",
        "already_lawyer": "Sie sind bereits als Anwalt registriert",
        "no_courtroom_thread": "❌ Kein Gerichtssaal-Thread für diesen Fall gefunden.",
        "error": "❌ Fehler",
        "db_unavailable": "Datenbank nicht verfügbar",
        "admin_only": "Nur Administratoren können diesen Befehl verwenden",
        "magistrate_only": "Nur Administratoren und Magistrate können diesen Befehl verwenden",
    },
}


# Helper function to get user's language preference from Discord locale
def get_user_language(interaction: discord.Interaction) -> str:
    """Auto-detect user's language from Discord client settings."""
    locale = str(interaction.locale)

    # Map Discord locales to our supported languages
    if locale.startswith('es'):
        return 'es'
    if locale.startswith('fr'):
        return 'fr'
    if locale.startswith('de'):
        return 'de'
    return 'en'


def t(interaction: discord.Interaction, key: str) -> str:
    """
    Get translated string based on user's Discord language.
    CRITICAL: Cascades to English if key missing/empty from target language (zero-tolerance requirement).
    Falls back to the key itself as last resort to prevent crashes.

    Treats both None and empty strings as missing to handle data issues gracefully.
    """
    lang = get_user_language(interaction)

    # Try target language first (treat empty strings as missing)
    translation = COURT_TRANSLATIONS.get(lang, {}).get(key)
    if not translation and lang != 'en':
        # Cascade to English if target language has None or empty string
        translation = COURT_TRANSLATIONS.get('en', {}).get(key)

    # Last resort: return key itself to prevent crashes
    return translation if translation else key


def get_translation_dict(lang: str) -> dict:
    """
    Get translation dictionary with cascading fallback for safe direct access.
    Returns a SafeTranslationDict that cascades missing/empty keys to English.

    CRITICAL: Use this instead of COURT_TRANSLATIONS.get() to ensure zero-tolerance safety.
    """

    class SafeTranslationDict(dict):
        """Dictionary that cascades to English for missing/empty keys."""

        def __init__(self, lang: str):
            super().__init__()
            self.lang = lang

        def get(self, key: str, default=None):
            # Try target language first
            translation = COURT_TRANSLATIONS.get(self.lang, {}).get(key)

            # Cascade to English if missing/empty and not already English
            if not translation and self.lang != 'en':
                translation = COURT_TRANSLATIONS.get('en', {}).get(key)

            # Use default or key as final fallback
            return translation if translation else (default if default is not None else key)

    return SafeTranslationDict(lang)


# Bilingual domain names (Spanish first, English in parentheses) + Soberante
DOMAINS = [
    "Soberante",
    "Defensa y Seguridad (Defense and Security)",
    "Obras e Infraestructura (Works and Infrastructure)",
    "Economía y Finanzas (Economy and Finance)",
    "Justicia y Ley (Justice and Law)",
    "Cultura y Patrimonio (Culture and Heritage)",
    "Agricultura y Recursos (Agriculture and Resources)",
    "Minería y Recursos Naturales (Mining and Natural Resources)",
    "Población y Asentamiento (Population and Settlement)",
]

# Bill categories based on Councilor domains
BILL_CATEGORIES = {
    "defense": "Defense and Security Councilor",
    "works": "Works and Infrastructure Councilor",
    "economy": "Economy and Finance Councilor",
    "justice": "Justice and Law Councilor",
    "culture": "Culture and Heritage Councilor",
    "agriculture": "Agriculture and Resources Councilor",
    "mining": "Mining and Natural Resources Councilor",
    "population": "Population and Settlement Councilor",
}

# Category emojis
CATEGORY_EMOJIS = {
    "Defense and Security Councilor": "🛡️",
    "Works and Infrastructure Councilor": "🏗️",
    "Economy and Finance Councilor": "💰",
    "Justice and Law Councilor": "⚖️",
    "Culture and Heritage Councilor": "🎭",
    "Agriculture and Resources Councilor": "🌾",
    "Mining and Natural Resources Councilor": "⛏️",
    "Population and Settlement Councilor": "👥",
}
