from ..utils.api.request import L4API


async def get_anne_player_out():
    return "\n".join(str(item) for item in (await L4API.get_anne_player())[1:]).strip()
