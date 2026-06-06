"""DRF permissions for team-scoped dashboard and API access."""

from rest_framework.permissions import BasePermission

from teams.tenant import bind_request_team


class HasTeamContext(BasePermission):
    """
    Allow access when ``request.team`` is set (JWT membership or X-API-Key).

    JWT is applied **after** Django middleware, so ``TeamMiddleware`` often does
    not see ``request.user`` yet. This permission calls ``bind_request_team`` to
    attach ``request.team`` from the authenticated user's membership (same logic
    as WhatsApp-preferring team selection).

    Webhook paths skip TeamMiddleware team resolution; those views use AllowAny
    and must not rely on this permission.
    """

    message = "Authentication with a team membership or valid API key is required."

    def has_permission(self, request, view) -> bool:
        return bind_request_team(request)
