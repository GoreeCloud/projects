# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Parse instance telemetry consent without relying on string truthiness."""


def telemetry_opt_in(value: object) -> bool:
    """Permit metric collection only for explicitly affirmative consent.

    Form submissions are strings, where bool("False") would be True.
    Missing, unrecognized, repeated or otherwise invalid values fail closed.
    """
    if value is True:
        return True
    if not isinstance(value, str):
        return False
    return value.strip().casefold() in {"true", "on", "1"}
