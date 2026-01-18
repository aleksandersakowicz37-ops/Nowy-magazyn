import streamlit as st
import pandas as pd
from supabase import create_client, Client


# --- Supabase ---
def get_supabase() -> Client:
    # Streamlit Cloud -> Secrets
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)


st.set_page_config(page_title="Magazyn", layout="wide")
sb = get_supabase()

st.title("Magazyn")

# Szybki test połączenia (jak coś nie działa, zobaczysz od razu)
try:
    sb.table("products").select("id").limit(1).execute()
except Exception as e:
    st.error("❌ Nie mogę połączyć się z Supabase lub brak uprawnień.")
    st.caption("Sprawdź: SUPABASE_URL, SUPABASE_KEY (anon), oraz RLS na tabelach.")
    st.exception(e)
    st.stop()

tab1, tab2, tab3 = st.tabs(["Produkty", "Ruchy", "Stany"])


# =========================
# TAB 1: Produkty
# =========================
with tab1:
    st.header("Dodaj produkt")

    with st.form("add_product", clear_on_submit=True):
        sku = st.text_input("SKU", placeholder="np. ABC-001")
        name = st.text_input("Nazwa", placeholder="np. Śruba M8")
        unit = st.text_input("Jednostka", value="szt")
        submitted = st.form_submit_button("Dodaj")

        if submitted:
            if not sku or not name:
                st.error("SKU i nazwa są wymagane.")
            else:
                try:
                    sb.table("products").insert(
                        {"sku": sku.strip(), "name": name.strip(), "unit": unit.strip()}
                    ).execute()
                    st.success("✅ Dodano produkt.")
                except Exception as e:
                    st.error("❌ Nie udało się dodać produktu (np. SKU już istnieje).")
                    st.exception(e)

    st.divider()
    st.subheader("Lista produktów")

    try:
        products_resp = (
            sb.table("products")
            .select("id,sku,name,unit,created_at")
            .order("created_at", desc=True)
            .execute()
        )
        dfp = pd.DataFrame(products_resp.data)
        st.dataframe(dfp, use_container_width=True)
    except Exception as e:
        st.error("❌ Nie udało się pobrać listy produktów.")
        st.exception(e)


# =========================
# TAB 2: Ruchy
# =========================
with tab2:
    st.header("Dodaj ruch magazynowy")

    try:
        products_resp = (
            sb.table("products")
            .select("id,sku,name,unit")
            .order("name")
            .execute()
        )
        df = pd.DataFrame(products_resp.data)
    except Exception as e:
        st.error("❌ Nie udało się pobrać produktów.")
        st.exception(e)
        df = pd.DataFrame([])

    if df.empty:
        st.warning("Najpierw dodaj produkty w zakładce 'Produkty'.")
    else:
        df["label"] = df["name"] + " (" + df["sku"] + ")"
        chosen = st.selectbox("Produkt", df["label"].tolist())
        product_id = df.loc[df["label"] == chosen, "id"].iloc[0]

        move_type = st.selectbox("Typ ruchu", ["IN", "OUT", "ADJ"])
        qty = st.number_input("Ilość", min_value=0.01, value=1.0, step=1.0)
        note = st.text_input("Notatka (opcjonalnie)")

        if st.button("Zapisz ruch"):
            try:
                # Blokada: OUT nie może zejść poniżej zera
                if move_type == "OUT":
                    bal = (
                        sb.from_("stock_balance")
                        .select("balance")
                        .eq("product_id", product_id)
                        .execute()
                    )
                    current = float(bal.data[0]["balance"]) if bal.data else 0.0
                    if current < float(qty):
                        st.error(f"❌ Brak na stanie. Masz: {current}, próbujesz wydać: {qty}")
                        st.stop()

                sb.table("stock_moves").insert(
                    {
                        "product_id": product_id,
                        "move_type": move_type,
                        "qty": float(qty),
                        "note": note.strip() if note else None,
                    }
                ).execute()
                st.success("✅ Zapisano ruch.")
            except Exception as e:
                st.error("❌ Nie udało się zapisać ruchu.")
                st.exception(e)

    st.divider()
    st.subheader("Ostatnie ruchy (surowe)")

    try:
        moves_resp = (
            sb.table("stock_moves")
            .select("created_at,move_type,qty,note,product_id")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        dfm = pd.DataFrame(moves_resp.data)
        st.dataframe(dfm, use_container_width=True)
    except Exception as e:
        st.error("❌ Nie udało się pobrać ruchów.")
        st.exception(e)


# =========================
# TAB 3: Stany
# =========================
with tab3:
    st.header("Stany magazynowe")

    try:
        bal_resp = (
            sb.from_("stock_balance")
            .select("sku,name,unit,balance")
            .order("name")
            .execute()
        )
        dfb = pd.DataFrame(bal_resp.data)
        st.dataframe(dfb, use_container_width=True)
    except Exception as e:
        st.error("❌ Nie udało się pobrać stanów (sprawdź czy widok stock_balance istnieje).")
        st.exception(e)
