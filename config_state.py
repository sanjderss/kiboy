import json
import os
import aiofiles

STATE_FILE = "data/bot_state.json"

async def save_state(account_email, state_data):
    """
    Menyimpan status terakhir dari bot agar tidak terhapus dan error saat crash.
    """
    os.makedirs("data", exist_ok=True)
    
    current_state = {}
    if os.path.exists(STATE_FILE):
        try:
            async with aiofiles.open(STATE_FILE, mode='r') as f:
                content = await f.read()
                current_state = json.loads(content)
        except Exception:
            pass
            
    current_state[account_email] = state_data
    
    try:
        async with aiofiles.open(STATE_FILE, mode='w') as f:
            await f.write(json.dumps(current_state, indent=4))
        return True
    except Exception as e:
        print(f"Gagal menyimpan state: {e}")
        return False

async def load_state(account_email):
    """
    Memuat status terakhir bot berdasarkan email. Berguna untuk resume otomatis.
    """
    if not os.path.exists(STATE_FILE):
        return None
        
    try:
        async with aiofiles.open(STATE_FILE, mode='r') as f:
            content = await f.read()
            states = json.loads(content)
            return states.get(account_email)
    except Exception:
        return None
