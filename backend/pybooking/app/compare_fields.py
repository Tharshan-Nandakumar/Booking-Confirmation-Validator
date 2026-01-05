from collections import defaultdict
from app.models.models import (
    ComparisonItem,
    ExtractedFields,
    MatchStatus,
    ScreenshotClassification,
    ScreenshotResult,
)


def gather_values_from_screenshots(
    screenshots: list[ScreenshotResult],
    field: str,
) -> dict[str, list[str]]:
    """
    Returns a mapping of extracted information for the field from all given screenshots:
    {
        extracted_value: [screenshot_id, ...]
    }
    """

    grouped: dict[str, list[str]] = defaultdict(list)

    for screenshot in screenshots:
        value = getattr(screenshot.extraction, field)
        if value != "unclear":
            grouped[str(value)].append(screenshot.screenshot_id)

    return dict(grouped)

def compare_fields(screenshots: list[ScreenshotResult]) -> list[ComparisonItem]:
    initial_screenshots = [
        s for s in screenshots
        if s.classification == ScreenshotClassification.INITIAL_QUOTE
    ]
    final_screenshots = [
        s for s in screenshots
        if s.classification == ScreenshotClassification.FINAL_BOOKING
    ]

    items: list[ComparisonItem] = []

    for field in (
        "hotel_name",
        "check_in",
        "check_out",
        "guests",
        "total_price",
    ):
        initial_values = gather_values_from_screenshots(initial_screenshots, field)
        final_values = gather_values_from_screenshots(final_screenshots, field)

        # Default placeholders
        initial_val = "unclear"
        final_val = "unclear"

        # --- UNCLEAR: missing or conflicting values ---
        if len(initial_values) != 1 or len(final_values) != 1:
            status = MatchStatus.UNCLEAR
            explanation = (
                f"Could not determine a single confident value for {field} "
                f"on both initial and final screenshots."
            )
            evidence = [
                *[sid for ids in initial_values.values() for sid in ids],
                *[sid for ids in final_values.values() for sid in ids],
            ]

        else:
            # Exactly one value on each side
            initial_val, initial_ids = next(iter(initial_values.items()))
            final_val, final_ids = next(iter(final_values.items()))

            if initial_val == final_val:
                status = MatchStatus.MATCH
                explanation = f"Values are identical for '{field}'."
            else:
                status = MatchStatus.MISMATCH
                explanation = (
                    f"Initial value '{initial_val}' differs from "
                    f"final value '{final_val}'."
                )

            evidence = initial_ids + final_ids

        items.append(
            ComparisonItem(
                field=field,
                initial_value=initial_val,
                final_value=final_val,
                status=status,
                explanation=explanation,
                evidence=evidence,
            )
        )

    return items
