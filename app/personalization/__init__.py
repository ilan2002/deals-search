"""Phase 2 and 3 interfaces: skin tone, sizing and virtual try-on.

Only the contracts live here for now, so the API and app can be designed
against them. Implementations (in-house models or paid APIs) plug in later.

User photos and body measurements are sensitive personal data under India's
DPDP Act 2023: collect them with explicit consent, store them encrypted, let
users delete them, and never use them for training without permission.
"""
