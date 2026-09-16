import streamlit as st
import requests
from PIL import Image
from pyzbar.pyzbar import decode

# --- Configuration de la page ---
st.set_page_config(page_title="CanScan App", page_icon="🇨🇦", layout="centered")

# --- Initialisation de la base locale en mémoire ---
if "db_locale" not in st.session_state:
    st.session_state.db_locale = {
        "0060383664145": {"product_name": "Jus d'orange local", "brands": "Sans Nom"},
        "060383664145": {"product_name": "Jus d'orange local", "brands": "Sans Nom"}
    }

# --- 1. Gestion des Langues ---
langue = st.sidebar.selectbox("🌐 Changer de langue / Language", ["Français", "English"])

txt = {
    "Français": {
        "titre_app": "🇨🇦 CanScan — Gestionnaire de Produits",
        "scan_title": "📸 Prenez une photo nette du code-barres",
        "search_manual": "## 🔍 Ou recherchez manuellement par texte / code",
        "input_label": "Entrez le nom d'un produit, une marque ou un code...",
        "input_placeholder": "Ex: 0060383664145, Jus d'orange, Sans Nom...",
        "found_local": "✅ Produit trouvé dans notre base locale !",
        "status_off": "⏳ Recherche sur Open Food Facts Canada...",
        "found_off": "🎉 Produit récupéré depuis Open Food Facts !",
        "btn_save_auto": "💾 Enregistrer dans la base locale",
        "save_success": "Produit ajouté à la base canadienne avec succès !",
        "error_not_found": "Désolé, ce produit n'est pas encore répertorié.",
        "add_manual_title": "### ➕ Ajouter ce produit manuellement",
        "form_name": "Nom du produit *",
        "form_brand": "Marque du produit",
        "form_submit": "Enregistrer le produit",
        "form_success": "Le produit '{name}' a été enregistré !",
        "form_error": "Le nom du produit est obligatoire.",
        "barcode_detected": "📋 Code-barres extrait de l'image :",
        "no_barcode": "❌ Aucun code-barres n'a pu être lu sur la photo. Assurez-vous qu'il soit bien droit, net et bien éclairé."
    },
    "English": {
        "titre_app": "🇨🇦 CanScan — Product Manager",
        "scan_title": "📸 Take a clear photo of the barcode",
        "search_manual": "## 🔍 Or search manually by text / barcode",
        "input_label": "Enter a product name, brand or barcode...",
        "input_placeholder": "Ex: 0060383664145, Orange juice, No Name...",
        "found_local": "✅ Product found in local database!",
        "status_off": "⏳ Searching Open Food Facts Canada...",
        "found_off": "🎉 Product retrieved from Open Food Facts!",
        "btn_save_auto": "💾 Save to local database",
        "save_success": "Product successfully added to the database!",
        "error_not_found": "Sorry, this product is not yet listed.",
        "add_manual_title": "### ➕ Add this product manually",
        "form_name": "Product Name *",
        "form_brand": "Product Brand",
        "form_submit": "Save Product",
        "form_success": "Product '{name}' has been saved!",
        "form_error": "Product name is required.",
        "barcode_detected": "📋 Barcode extracted from image:",
        "no_barcode": "❌ No barcode could be read from the photo. Make sure it is straight, sharp, and well-lit."
    }
}[langue]

# --- 2. Fonctions utilitaires ---
def format_barcode(barcode_str):
    clean_code = str(barcode_str).strip()
    if clean_code.startswith("00") and len(clean_code) == 13:
        return clean_code, clean_code[2:]
    elif clean_code.startswith("0") and len(clean_code) == 13:
        return clean_code, clean_code[1:]
    return clean_code, clean_code

def fetch_from_open_food_facts(barcode):
    url = f"https://openfoodfacts.org{barcode}.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                return data.get("product", {})
    except Exception:
        pass
    return None

# --- 3. Interface utilisateur ---
st.title(txt["titre_app"])
st.divider()

st.markdown(f"### {txt['scan_title']}")

# Prise de photo
img_file = st.camera_input("Prendre une photo")

barcode_detected = ""

if img_file is not None:
    # Analyse de la photo pour trouver le code-barres
    img = Image.open(img_file)
    decoded_objects = decode(img)
    
    if decoded_objects:
        # Code trouvé avec succès !
        barcode_detected = decoded_objects.data.decode("utf-8").strip()
        st.success(f"{txt['barcode_detected']} {barcode_detected}")
    else:
        st.error(txt["no_barcode"])

# Section Recherche Manuelle
st.markdown(txt["search_manual"])
manual_input = st.text_input(label=txt["input_label"], placeholder=txt["input_placeholder"])

# Priorité au code scanné, sinon saisie manuelle
code_to_search = barcode_detected if barcode_detected else manual_input

# --- 4. Traitement et Recherche ---
if code_to_search:
    ean_code, upc_code = format_barcode(code_to_search)
    produit_local = st.session_state.db_locale.get(ean_code) or st.session_state.db_locale.get(upc_code)
    
    if produit_local:
        st.success(txt["found_local"])
        st.subheader(f"{produit_local.get('product_name')} — {produit_local.get('brands')}")
    else:
        with st.spinner(txt["status_off"]):
            info_produit = fetch_from_open_food_facts(ean_code) or fetch_from_open_food_facts(upc_code)
        
        if info_produit:
            st.success(txt["found_off"])
            nom = info_produit.get("product_name", "Nom inconnu")
            marque = info_produit.get("brands", "Marque inconnue")
            st.subheader(f"{nom} — {marque}")
            
            if st.button(txt["btn_save_auto"]):
                st.session_state.db_locale[code_to_search] = {"product_name": nom, "brands": marque}
                st.success(txt["save_success"])
        else:
            st.error(f"{txt['error_not_found']} (Code: {code_to_search})")
            
            st.markdown(txt["add_manual_title"])
            with st.form("add_product_form"):
                new_name = st.text_input(txt["form_name"])
                new_brand = st.text_input(txt["form_brand"])
                submitted = st.form_submit_button(txt["form_submit"])
                
                if submitted:
                    if new_name:
                        st.session_state.db_locale[code_to_search] = {"product_name": new_name, "brands": new_brand}
                        st.success(txt["form_success"].format(name=new_name, code=code_to_search))
                    else:
                        st.error(txt["form_error"])
