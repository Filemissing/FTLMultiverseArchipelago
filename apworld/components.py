from worlds.LauncherComponents import Component, Type, components, launch

def run_client(*args: str) -> None:
    from .client.launch import launch_client

    launch(launch_client, name="FTLMultiverse Client", args=args)

components.append(
    Component(
        "FTL: Multiverse Client",
        func=run_client,
        game_name="FTL: Multiverse",
        component_type=Type.CLIENT,
        supports_uri=True,
    )
)
