import sys

sys.path.insert(0, '/home/ubuntu/.local/lib/python3.8/site-packages')

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def koneksi():
    host_env = os.getenv("HOST")
    user_env = os.getenv("USER")
    pass_env = os.getenv("PASSWORD")
    db_env = os.getenv("DATABASE")

    conn = mysql.connector.connect(
        host = host_env,
        user = user_env,
        password = pass_env,
        database = db_env)
    
    return conn