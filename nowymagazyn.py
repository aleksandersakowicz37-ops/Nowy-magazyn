import streamlit as st
from supabase import create_client, Client

def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

st.set_page_config(page_title="Magazyn", layout="wide")
sb = get_supabase()

tab1, tab2, tab3 = st.tabs(["Produkty", "Ruchy", "Stany"])

# --- TAB: Produkty ---
with tab1:
    st.subheader("Dodaj produkt")

    with st.form("add_product", clear_on_submit=True):
        sku = st.text_input("SKU", placeholder="np. ABC-001")
        name = st.text_input("Nazwa", placeholder="np. Śruba M8")
        unit = st.text_input("Jednostka", value="szt")
        submitted = st.form_submit_button("Dodaj")

        if submitted:
            if not sku or not name:
                st.error("SKU i nazwa są wymagane.")
            else:
                sb.table("products").insert(
                    {"sku": sku, "name": name, "unit": unit}
                ).execute()
                st.success("Dodano produkt.")

    st.divider()
    st.subheader("Lista produktów")

    products = (
        sb.table("products")
        .select("id,sku,name,unit,created_at")
        .order("created_at", desc=True)
        .execute()
    )
    dfp = pd.DataFrame(products.data)
    st.dataframe(dfp, use_container_width=True)

# --- TAB: Ruchy ---
with tab2:
    st.subheader("Dodaj ruch magazynowy")

    products = (
        sb.table("products")
        .select("id,sku,name,unit")
        .order("name")
        .execute()
    )
    df = pd.DataFrame(products.data)

    if df.empty:
        st.warning("Najpierw dodaj produkty.")
    else:
        df["label"] = df["name"] + " (" + df["sku"] + ")"
        chosen = st.selectbox("Produkt", df["label"].tolist())
        product_id = df.loc[df["label"] == chosen, "id"].iloc[0]

        move_type = st.selectbox("Typ ruchu", ["IN", "OUT", "ADJ"])
        qty = st.number_input("Ilość", min_value=0.01, value=1.0, step=1.0)
        note = st.text_input("Notatka (opcjonalnie)")

        if st.button("Zapisz ruch"):
            sb.table("stock_moves").insert(
                {
                    "product_id": product_id,
                    "move_type": move_type,
                    "qty": qty,
                    "note": note,
                }
            ).execute()
            st.success("Zapisano ruch.")

    st.divider()
    st.subheader("Ostatnie ruchy")

    moves = (
        sb.table("stock_moves")
        .select("created_at,move_type,qty,note,product_id")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    dfm = pd.DataFrame(moves.data)
    st.dataframe(dfm, use_container_width=True)

# --- TAB: Stany ---
with tab3:
    st.subheader("Stany magazynowe")

    bal = sb.from_("stock_balance").select("sku,name,unit,balance").order("name").execute()
    dfb = pd.DataFrame(bal.data)
    st.dataframe(dfb, use_container_width=True)
