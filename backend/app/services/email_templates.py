def render_bundle_submitted(
    project_name: str,
    bundle_name: str,
    submitter_name: str,
    review_url: str,
) -> tuple[str, str]:
    subject = "[FERRY] Bundle submitted for approval"
    body = (
        f"{project_name}\n\n{bundle_name}\n\n{submitter_name}\n\nReview:\n{review_url}"
    )
    return subject, body


def render_output_released(
    project_name: str,
    bundle_name: str,
    results_url: str,
) -> tuple[str, str]:
    subject = "[FERRY] Results available"
    body = f"{project_name}\n\n{bundle_name}\n\nResults:\n{results_url}"
    return subject, body
