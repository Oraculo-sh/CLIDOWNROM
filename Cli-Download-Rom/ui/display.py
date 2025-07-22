from utils.localization import _

def display_search_results(results):
    """
    Exibe os resultados da busca formatados numa tabela.
    """
    if not results:
        print(f"\n{_('search_no_results')}")
        return

    headers = {
        "index": "#",
        "title": _("table_header_title"),
        "platform": _("table_header_platform"),
        "regions": _("table_header_regions")
    }

    col_widths = {key: len(value) for key, value in headers.items()}
    for i, result in enumerate(results):
        col_widths["index"] = max(col_widths["index"], len(str(i + 1)))
        col_widths["title"] = max(col_widths["title"], len(result.get("title", "")))
        col_widths["platform"] = max(col_widths["platform"], len(result.get("platform", "")))
        col_widths["regions"] = max(col_widths["regions"], len(", ".join(result.get("regions", []))))

    header_line = (
        f"{headers['index']:<{col_widths['index']}} | "
        f"{headers['title']:<{col_widths['title']}} | "
        f"{headers['platform']:<{col_widths['platform']}} | "
        f"{headers['regions']:<{col_widths['regions']}}"
    )
    separator = "-" * len(header_line)

    print(f"\n{_('search_results_title')}")
    print(separator)
    print(header_line)
    print(separator)

    for i, result in enumerate(results):
        index_str = str(i + 1)
        title = result.get("title", "N/A")
        platform = result.get("platform", "N/A")
        regions = ", ".join(result.get("regions", []))

        row = (
            f"{index_str:<{col_widths['index']}} | "
            f"{title:<{col_widths['title']}} | "
            f"{platform:<{col_widths['platform']}} | "
            f"{regions:<{col_widths['regions']}}"
        )
        print(row)

    print(separator)
    print(f"\n{_('search_select_prompt')}")