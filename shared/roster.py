"""
Scrollhouse Team Roster

Maps account-manager display names to their email addresses.
Extend this dict as new team members join.
"""

TEAM_ROSTER: dict[str, str] = {
    "Priya Sharma":     "shri25.work@gmail.com",
    "Arjun Mehta":      "arjun@scrollhouse.com",
    "Sneha Iyer":       "sneha@scrollhouse.com",
    "Rohan Kapoor":     "rohan@scrollhouse.com",
    "Ananya Desai":     "ananya@scrollhouse.com",
    "Vikram Singh":     "vikram@scrollhouse.com",
    "Meera Nair":       "meera@scrollhouse.com",
    "Karthik Rao":      "karthik@scrollhouse.com",
    "Aditi Gupta":      "aditi@scrollhouse.com",
    "Rahul Joshi":      "rahul@scrollhouse.com",
}


def get_am_email(name: str) -> str | None:
    """Return the email for *name* (case-insensitive match)."""
    normalised = {k.lower(): v for k, v in TEAM_ROSTER.items()}
    return normalised.get(name.strip().lower())
