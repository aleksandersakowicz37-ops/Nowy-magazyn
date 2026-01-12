import os
from supabase import create_client, Client

def get_supabase() -> Client:
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"] # anon key lub service role (ostrożnie)
return create_client(url, key)
