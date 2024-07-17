import os

from ayon_server.actions import SimpleActionManifest
from ayon_server.entities import ProjectEntity

IDENTIFIER_PREFIX = "application.launch."


def get_items_for_app_groups(groups):
    label_by_name = {}
    icon_by_name = {}
    for group in groups:
        group_name = group["name"]
        group_label = group["label"] or group_name
        icon_name = group["icon"]
        if icon_name:
            icon_name = os.path.basename(icon_name)

        for variant in group["variants"]:
            variant_name = variant["name"]
            if not variant_name:
                continue
            variant_label = variant["label"] or variant_name
            full_name = f"{group_name}/{variant_name}"
            full_label = f"{group_label} {variant_label}"
            label_by_name[full_name] = full_label
            icon_by_name[full_name] = icon_name

    return [
        {
            "value": full_name,
            "label": label_by_name[full_name],
            "icon": icon_by_name[full_name],
        }
        for full_name in sorted(label_by_name)
    ]


async def get_action_manifests(addon, project_name, variant):
    if not project_name:
        return []

    project_entity = await ProjectEntity.load(project_name)
    project_apps = project_entity.original_attributes.get("applications", [])

    settings_model = await addon.get_studio_settings(variant=variant)
    app_settings = settings_model.dict()["applications"]
    app_groups = app_settings.pop("additional_apps")
    for group_name, value in app_settings.items():
        value["name"] = group_name
        app_groups.append(value)

    output = []
    for item in get_items_for_app_groups(app_groups):
        app_full_name = item["value"]
        if app_full_name not in project_apps:
            continue

        icon = None
        if item["icon"]:
            icon = {
                "type": "url",
                "url": "{addon_url}/public/icons/" + item["icon"],
            }
        output.append(
            SimpleActionManifest(
                identifier=f"{IDENTIFIER_PREFIX}{app_full_name}",
                label=item["label"],
                category="Applications",
                icon=icon,
                order=100,
                entity_type="task",
                entity_subtypes=None,
                allow_multiselection=False,
            )
        )
    return output