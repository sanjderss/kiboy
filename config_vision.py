import asyncio

class VisionRule:
    def __init__(self, name, keywords, action_function, log_message):
        self.name = name
        self.keywords = keywords
        self.action_function = action_function
        self.log_message = log_message

async def dummy_action(page, websocket):
    pass

# Di sinilah pengguna bisa dengan mudah menambahkan "config" baru jika AI melihat teks tertentu
# Misalnya AI melihat "install", maka aksi install akan dijalankan.
VISION_CONFIG_RULES = [
    {
        "state_name": "CHROME_FRE",
        "keywords": [["accept", "continue"], ["use", "without", "account"]],
        "action_log": "Menyetujui persyaratan Chrome..."
    },
    {
        "state_name": "CHROME_SYNC",
        "keywords": [["no", "thanks"]],
        "action_log": "Menolak sinkronisasi Chrome..."
    },
    {
        "state_name": "CHROME_PRIVACY",
        "keywords": [["enhanced", "privacy"], ["ad", "privacy"]],
        "action_log": "Menghadapi popup Privacy Chrome..."
    },
    {
        "state_name": "INSTALL_POPUP",
        "keywords": [["application?"], ["install this"]], # Salah satu sub-list harus terpenuhi
        "action_log": "Menekan tombol Install pada popup..."
    },
    {
        "state_name": "APP_STORE_DOWNLOADING",
        "keywords": [["installing"], ["downloading"], ["cancel"]],
        "action_log": "Sedang mendownload/menginstall aplikasi (Realtime Rendering)..."
    },
    {
        "state_name": "HOME_SCREEN",
        "keywords": [["guardianmaster"], ["devicemaster"], ["settings", "play", "store"]],
        "action_log": "Berada di Home Screen Android..."
    },
    {
        "state_name": "APP_INSTALLED",
        "keywords": [["app", "installed"], ["installed.", "done"]],
        "action_log": "Aplikasi telah selesai diinstal. Menunggu dibuka..."
    },
    {
        "state_name": "APP_STORE",
        "keywords": [["commonapps"], ["tools"], ["top charts"]],
        "action_log": "Berada di dalam App Store..."
    },
    {
        "state_name": "CHROME_MAIN",
        "keywords": [["search"], ["google"]],
        "action_log": "Berada di halaman utama pencarian Chrome..."
    }
]

def analyze_realtime_text(screen_text):
    """
    Meng-scan teks dari layar secara realtime dan mencocokkan dengan config.
    """
    for rule in VISION_CONFIG_RULES:
        for keyword_group in rule["keywords"]:
            if all(word in screen_text for word in keyword_group):
                return rule["state_name"]
    return "UNKNOWN"
