"""Resolve which team owns inbound traffic (multi-tenant routing)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from teams.models import Team

logger = logging.getLogger(__name__)


def get_default_team():
    """Fallback when a channel cannot resolve a team (single-tenant / dev)."""
    from teams.models import Team

    return Team.objects.order_by("created_at").first()


def team_for_whatsapp_phone_number_id(phone_number_id: str | None) -> Team | None:
    from teams.models import TeamWhatsAppConfig

    if not phone_number_id or not str(phone_number_id).strip():
        return None
    pid = str(phone_number_id).strip()
    cfg = (
        TeamWhatsAppConfig.objects.filter(
            phone_number_id=pid,
            is_active=True,
        )
        .select_related("team")
        .first()
    )
    return cfg.team if cfg else None


def team_for_messenger_page_id(page_id: str | None) -> Team | None:
    from teams.models import TeamMessengerConfig

    if not page_id or not str(page_id).strip():
        return None
    pid = str(page_id).strip()
    cfg = (
        TeamMessengerConfig.objects.filter(page_id=pid, is_active=True)
        .select_related("team")
        .first()
    )
    return cfg.team if cfg else None


def team_for_telegram_team_id(team_id) -> Team | None:
    from teams.models import Team

    try:
        return Team.objects.get(pk=team_id)
    except (Team.DoesNotExist, ValueError, TypeError):
        return None


def get_team_for_user(user):
    """Pick the dashboard team for this user.

    If the user belongs to multiple teams, prefer one with an **active WhatsApp**
    configuration (non-empty ``phone_number_id``), so ticket lists match inbound
    WhatsApp routing. Otherwise use the most recently joined membership.
    """
    from teams.models import TeamMembership, TeamWhatsAppConfig

    memberships = list(
        TeamMembership.objects.filter(user=user)
        .select_related("team")
        .order_by("-created_at")
    )
    if not memberships:
        return None
    for m in memberships:
        if (
            TeamWhatsAppConfig.objects.filter(team=m.team, is_active=True)
            .exclude(phone_number_id="")
            .exists()
        ):
            return m.team
    return memberships[0].team


def bind_request_team(request) -> bool:
    """Ensure ``request.team`` is set: API key (middleware), then JWT/session user.

    DRF authenticates JWT *after* Django middleware, so ``TeamMiddleware`` often
    leaves ``request.team`` unset for Bearer requests. Call this from
    ``HasTeamContext`` after authentication.
    """
    if getattr(request, "team", None) is not None:
        return True
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        team = get_team_for_user(user)
        if team is not None:
            request.team = team  # type: ignore[attr-defined]
            return True
    return False
