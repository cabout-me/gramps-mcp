"""
Utility functions for gramps_mcp.
"""

from markdownify import markdownify as md

from .models.api_calls import ApiCalls


def html_to_markdown(html: str) -> str:
    """
    Convert HTML content to Markdown format.

    Args:
        html: HTML string to convert

    Returns:
        Markdown formatted string
    """
    if not html or not html.strip():
        return ""

    return md(html, heading_style="ATX")


async def get_gramps_id_from_handle(
    client, obj_class: str, obj_handle: str, tree_id: str
) -> str:
    """
    Convert an object handle to its gramps_id using the appropriate API call.

    Args:
        client: GrampsWebAPIClient instance
        obj_class: Object class/type (e.g., "person", "family", "source")
        obj_handle: Object handle to convert
        tree_id: Tree identifier

    Returns:
        Gramps ID if found, otherwise the original handle
    """
    try:
        obj_class_lower = obj_class.lower()

        if obj_class_lower == "person":
            obj_info = await client.make_api_call(
                api_call=ApiCalls.GET_PERSON,
                params=None,
                tree_id=tree_id,
                handle=obj_handle,
            )
        elif obj_class_lower == "family":
            obj_info = await client.make_api_call(
                api_call=ApiCalls.GET_FAMILY,
                params=None,
                tree_id=tree_id,
                handle=obj_handle,
            )
        elif obj_class_lower == "event":
            obj_info = await client.make_api_call(
                api_call=ApiCalls.GET_EVENT,
                params=None,
                tree_id=tree_id,
                handle=obj_handle,
            )
        elif obj_class_lower == "place":
            obj_info = await client.make_api_call(
                api_call=ApiCalls.GET_PLACE,
                params=None,
                tree_id=tree_id,
                handle=obj_handle,
            )
        elif obj_class_lower == "source":
            obj_info = await client.make_api_call(
                api_call=ApiCalls.GET_SOURCE,
                params=None,
                tree_id=tree_id,
                handle=obj_handle,
            )
        elif obj_class_lower == "citation":
            obj_info = await client.make_api_call(
                api_call=ApiCalls.GET_CITATION,
                params=None,
                tree_id=tree_id,
                handle=obj_handle,
            )
        elif obj_class_lower == "media":
            obj_info = await client.make_api_call(
                api_call=ApiCalls.GET_MEDIA_ITEM,
                params=None,
                tree_id=tree_id,
                handle=obj_handle,
            )
        elif obj_class_lower == "note":
            obj_info = await client.make_api_call(
                api_call=ApiCalls.GET_NOTE,
                params=None,
                tree_id=tree_id,
                handle=obj_handle,
            )
        elif obj_class_lower == "repository":
            obj_info = await client.make_api_call(
                api_call=ApiCalls.GET_REPOSITORY,
                params=None,
                tree_id=tree_id,
                handle=obj_handle,
            )
        else:
            return obj_handle

        if obj_info and "gramps_id" in obj_info:
            return obj_info["gramps_id"]
        else:
            return obj_handle

    except Exception:
        # If we can't resolve it, just return the handle
        return obj_handle
