"""External endpoint URLs (SourceBans, Anne, Steam Workshop)."""

# Anne (电信服) SourceBans++
anne_ban = "https://sb.trygek.com/"
anne_ser = f"{anne_ban}l4d_stats/"
AnneRankApi = f"{anne_ser}ranking/index.php?type=coop"
AnnePlayerApi = f"{anne_ser}ranking/player.php?steamid="
AnneSearchApi = f"{anne_ser}/ranking/search.php"

# Steam Workshop detail lookup
WorkshopApi = "https://steamworkshopdownloader.io/api/details/file"
