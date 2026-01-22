from datetime import datetime
import pandas as pd
from lib.data_io import load_df, save_df_and_commit

def log(action: str, user: str, detail: str):
    df = load_df("audit")
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "detail": detail,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_df_and_commit("audit", df, commit_msg=f"audit: {action}")
