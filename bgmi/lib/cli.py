def print_filter(followed_filter_obj: Filter) -> None:
    print_info(
        "Followed subtitle group: {}".format(
            ", ".join(x["name"] for x in Subtitle.get_subtitle_by_id(followed_filter_obj.subtitle.split(", ")))
            if followed_filter_obj.subtitle
            else "None"
        )
    )
    print_info(f"Include keywords: {followed_filter_obj.include}")
    print_info(f"Exclude keywords: {followed_filter_obj.exclude}")
    print_info(f"Regular expression: {followed_filter_obj.regex}")
