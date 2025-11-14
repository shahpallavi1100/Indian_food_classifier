# streamlit_app/app.py
import os
import sys
import textwrap
import uuid
import streamlit as st
from PIL import Image
from streamlit.components.v1 import html as st_html

# add project root so src.* imports work
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from src.predict import predict_image
from src.nutrition import NUTRITION_DB

# ---------------- Config ----------------
st.set_page_config(page_title="Indian Food Classifier", layout="wide", page_icon="🍽️")
# ---------------- Helpers ----------------
def safe_nutrition_card(per100: dict, ps: dict, theme: str) -> str:
    card_bg = "#FFEED6" if theme == "dark" else "#ffffff"
    border = "#F5CBA7" if theme == "dark" else "#e8c8a8"
    text = "#4A2C2A" if theme == "dark" else "#222222"
    html = textwrap.dedent(f"""
    <div style="background:{card_bg}; padding:20px; border-radius:14px; border:2px solid {border}; color:{text}; max-width:980px; margin:auto; line-height:1.6;">
        <h4 style="margin:0 0 8px 0;">Per 100g</h4>
        <div style="font-size:15px;">
            <b>🔥 Calories:</b> {per100.get('calories', '-')} kcal<br>
            <b>🍗 Protein:</b> {per100.get('protein', '-')} g<br>
            <b>🥔 Carbs:</b> {per100.get('carbs', '-')} g<br>
            <b>🧈 Fat:</b> {per100.get('fat', '-')} g<br>
            <b>🌾 Fiber:</b> {per100.get('fiber', '-')} g<br>
        </div>
        <div style="height:12px;"></div>
        <h4 style="margin:0 0 8px 0;">Per Serving ({ps.get('serving','-')})</h4>
        <div style="font-size:15px;">
            <b>🔥 Calories:</b> {ps.get('calories', '-')} kcal<br>
            <b>🍗 Protein:</b> {ps.get('protein', '-')} g<br>
            <b>🥔 Carbs:</b> {ps.get('carbs', '-')} g<br>
            <b>🧈 Fat:</b> {ps.get('fat', '-')} g<br>
            <b>🌾 Fiber:</b> {ps.get('fiber', '-')} g<br>
        </div>
    </div>
    """)
    return html

def chartjs_donut_html(values, labels, colors, title, theme):
    """
    Build isolated Chart.js donut snippet. Use .format to avoid f-string brace confusion.
    """
    canvas_id = "c_" + uuid.uuid4().hex[:8]
    data_vals = ",".join(str(v) for v in values)
    labels_js = ",".join([f"'{l}'" for l in labels])
    colors_js = ",".join([f"'{c}'" for c in colors])
    text_color = "#ffffff" if theme == "dark" else "#111111"

    tpl = textwrap.dedent("""
    <div style="width:200px; margin:auto; text-align:center;">
      <canvas id="{cid}" width="200" height="200"></canvas>
      <div style="text-align:center; margin-top:6px; color:{text_color}; font-weight:700;">{title}</div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
    (function(){{
        const ctx = document.getElementById('{cid}').getContext('2d');
        const data = [{data_vals}];
        const labels = [{labels}];
        const colors = [{colors}];
        const cfg = {{
            type: 'doughnut',
            data: {{
                datasets: [{{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 0,
                    hoverOffset: 8
                }}],
                labels: labels
            }},
            options: {{
                cutout: '72%',
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{ enabled: true }}
                }},
                animation: {{
                    animateRotate: true,
                    duration: 900,
                    easing: 'easeOutQuart'
                }}
            }}
        }};
        new Chart(ctx, cfg);
    }})();
    </script>
    """)
    return tpl.format(cid=canvas_id, data_vals=data_vals, labels=labels_js, colors=colors_js, text_color=text_color, title=title)

def macro_bar_html(value, color, label, max_cap=100, theme="dark"):
    pct = min(100, int(round((value / max_cap) * 100))) if max_cap > 0 else 0
    container_bg = "rgba(255,255,255,0.04)" if theme == "dark" else "rgba(0,0,0,0.06)"
    text_color = "#ffffff" if theme == "dark" else "#111111"
    html = textwrap.dedent(f"""
    <div style="width:92%; max-width:920px; margin:auto; color:{text_color};">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <div style="font-weight:600;">{label}</div>
        <div style="font-weight:700;">{value} g</div>
      </div>
      <div style="height:8px;"></div>
      <div style="background:{container_bg}; border-radius:12px; height:14px; overflow:hidden;">
        <div class="fill" style="height:100%; width:{pct}%; background:{color}; border-radius:12px; transition: width 900ms cubic-bezier(.2,.9,.2,1);"></div>
      </div>
    </div>
    """)
    return html

MACRO_COLORS = {"Protein":"#2ECC71", "Carbs":"#3498DB", "Fat":"#E67E22", "Fiber":"#9B59B6"}

# ---------------- Theme control ----------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Render a hidden checkbox (Streamlit) that we toggle with the floating button.
# Keeping Streamlit checkbox ensures state and rerun work properly.
col_main, col_toggle = st.columns([9,1])
with col_toggle:
    theme_checked = st.checkbox("", value=(st.session_state.theme == "dark"), key="theme_bool", help="Toggle theme (hidden control)")
# update session state
st.session_state.theme = "dark" if theme_checked else "light"

# ---------------- Prepare CSS values ----------------
bg_color = "var(--dark-bg)" if st.session_state.theme == "dark" else "var(--light-bg)"
text_color = "#FFFFFF" if st.session_state.theme == "dark" else "#111111"
muted_color = "#b9bdc2" if st.session_state.theme == "dark" else "#666666"
pred_card_bg = "linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01))" if st.session_state.theme == "dark" else "linear-gradient(180deg, rgba(0,0,0,0.02), rgba(0,0,0,0.01))"
accent = "#F4D03F"

# ---------------- Global CSS (escape braces correctly) ----------------
BASE_CSS = f"""
<style>
:root {{
  --dark-bg: #0f1113;
  --dark-panel: #121416;
  --muted: #b9bdc2;
  --accent: {accent};
  --card-dark: #FFEED6;
  --card-dark-border: #F5CBA7;
  --card-text-dark: #4A2C2A;
  --light-bg: #f7f7f7;
  --light-panel: #ffffff;
  --light-muted: #666666;
}}

/* app background + font */
[data-testid="stAppViewContainer"] {{
    background: {bg_color};
    color: {text_color};
    transition: background 300ms ease, color 300ms ease;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    padding: 12px 18px;
}}

/* header */
h1,h2,h3,h4 {{ margin:6px 0; }}
.small-muted {{ color: {muted_color}; font-size:13px; }}

/* prediction card */
.pred-card {{
  background: {pred_card_bg};
  padding:18px; border-radius:14px; border:1px solid rgba(0,0,0,0.06);
  transition: transform .18s ease, box-shadow .18s ease;
}}
.pred-card:hover {{ transform: translateY(-6px); box-shadow: 0 14px 30px rgba(0,0,0,0.45); }}

/* comp-box */
.comp-box {{ padding:18px; border-radius:12px; }}

/* responsive grid */
.grid-2 {{ display:grid; grid-template-columns: 1fr 360px; gap:28px; align-items:start; }}
@media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} .nutri-card {{ width:96%; }} }}

/* footer */
.footer {{ text-align:center; color:gray; padding-top:22px; font-size:14px; }}

/* ---- Toggle hidden (we use floating button to toggle) ---- */
div[data-testid="stCheckbox"] {{ display:inline-block; opacity:0; height:0; width:0; margin:0; padding:0; }}

.float-toggle-btn {{
  position: fixed;
  top: 18px;
  right: 18px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: {('linear-gradient(135deg,#ffd27a,#f4d03f)' if st.session_state.theme=='dark' else '#FFF')};
  color: {('#111' if st.session_state.theme=='dark' else '#111')};
  display: grid;
  place-items: center;
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  cursor: pointer;
  transition: transform .18s ease, box-shadow .18s ease, background .25s ease;
  z-index: 9999;
  border: 2px solid rgba(255,255,255,0.04);
}}
.float-toggle-btn:hover {{ transform: translateY(-6px) scale(1.03); box-shadow: 0 18px 40px rgba(0,0,0,0.45); }}

/* inner icon */
.float-toggle-btn .icon {{
  font-size:22px;
  transition: transform .28s ease;
}}
.float-toggle-btn:hover .icon {{ transform: rotate(-12deg) scale(1.08); }}

/* macrobars fill tweak for smoother animation */
.fill {{ will-change: width; }}

/* small buttons */
.stButton>button {{
  border-radius:10px; padding:8px 12px; transition: transform .12s ease;
}}
.stButton>button:hover {{ transform: translateY(-3px); }}

/* utility */
.center {{ text-align:center; }}
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)

# ---------------- Floating Round Button (calls hidden checkbox click) ----------------
# The button triggers JS to click the hidden Streamlit checkbox.
# When clicked, Streamlit will receive the change and rerun (so session_state updates).
floating_html = textwrap.dedent(f"""
<div class="float-toggle-btn" onclick="(function(){{
  const cb = document.querySelector('input[id^=\"theme_bool\"]');
  if(cb) cb.click();
}})();">
  <div class="icon">{"🌙" if st.session_state.theme=="dark" else "🌞"}</div>
</div>
""")
st.markdown(floating_html, unsafe_allow_html=True)

# ---------------- Header ----------------
st.markdown(textwrap.dedent(f"""
<div style="display:flex; justify-content:space-between; align-items:center;">
  <div>
    <h1 style="color: {'#F4D03F' if st.session_state.theme=='dark' else '#b8872b'}; margin:0;">🍽️ Indian Food Recognition & Nutrition Analyzer</h1>
    <p class="small-muted" style="margin:4px 0 10px 0;">Upload a food image → Predict the dish → View advanced nutrition visuals</p>
  </div>
  <div style="text-align:right;">
    <div style="font-size:13px; color: {muted_color};">Theme</div>
  </div>
</div>
<hr style="border-color: rgba(255,255,255,0.04); margin-top:8px;">
"""), unsafe_allow_html=True)

# ---------------- Sidebar Menu ----------------
menu = st.sidebar.radio("Select Feature", ["🔍 Food Recognition", "🥗 Calorie Calculator", "⚖️ Food Comparison"])

# ================== PAGE: FOOD RECOGNITION ==================
if menu == "🔍 Food Recognition":
    st.markdown(textwrap.dedent(f"""
    <div style="text-align:center;">
      <h2 style="margin-bottom:6px; color: {'#F4D03F' if st.session_state.theme=='dark' else '#b8872b'};">📤 Upload a Food Image</h2>
      <p class="small-muted">Supported formats: JPG, JPEG, PNG</p>
    </div>
    """), unsafe_allow_html=True)

    uploaded_file = st.file_uploader("", type=["jpg","jpeg","png"], key="food_upload_main")

    if uploaded_file:
        img = Image.open(uploaded_file).convert("RGB")

        # two-column layout: image preview + right info
        left, right = st.columns([1,1.2])
        with left:
            st.markdown("<p class='small-muted'>Preview</p>", unsafe_allow_html=True)
            st.image(img, use_column_width=True)

        with right:
            with st.spinner("Analyzing image… 🔍"):
                dish, confidence, nutrition = predict_image(img)

            st.markdown(textwrap.dedent(f"""
            <div class="pred-card">
              <h3 style="margin:0; color:#FADBD8;">🍽️ Predicted Dish: <b style='color:{"#fff" if st.session_state.theme=='dark' else "#111"}'>{dish}</b></h3>
              <p style="margin:6px 0 0 0; font-size:15px; color:#F5B7B1;">🔥 Confidence: <b>{confidence*100:.2f}%</b></p>
              <p class="small-muted" style="margin-top:8px;">Tip: Scroll to see nutrition, macro charts and animated bars</p>
            </div>
            """), unsafe_allow_html=True)

            # health tag
            if nutrition:
                cal_100 = nutrition["per100g"].get("calories", 0)
                if cal_100 < 150:
                    tag_icon, tag_text, tag_color = "🟢", "Healthy", "#2ECC71"
                elif cal_100 < 300:
                    tag_icon, tag_text, tag_color = "🟡", "Moderate", "#F1C40F"
                else:
                    tag_icon, tag_text, tag_color = "🔴", "Unhealthy", "#E74C3C"
                st.markdown(f"<h4 style='margin-top:12px;'>Health Tag: <span style='color:{tag_color};'>{tag_icon} {tag_text}</span></h4>", unsafe_allow_html=True)

        # Nutrition visuals
        st.markdown("<h3 style='margin-top:18px; color: inherit;'>🥗 Nutrition Card</h3>", unsafe_allow_html=True)

        if nutrition:
            per100 = nutrition["per100g"]
            ps = nutrition["per_serving"]

            # left: nutrition card
            st.markdown(safe_nutrition_card(per100, ps, st.session_state.theme), unsafe_allow_html=True)

            # macro slices
            p = float(per100.get("protein", 0))
            c = float(per100.get("carbs", 0))
            f = float(per100.get("fat", 0))
            fi = float(per100.get("fiber", 0))
            total = max(1.0, p + c + f + fi)
            p_pct = int(round((p/total)*100))
            c_pct = int(round((c/total)*100))
            f_pct = int(round((f/total)*100))
            fi_pct = int(round((fi/total)*100))

            # Chart area: combine 4 donuts horizontally (rendered via components.html)
            charts_html = "<div style='display:flex; gap:16px; flex-wrap:wrap; align-items:center; justify-content:center;'>"
            charts_html += chartjs_donut_html([p_pct, 100-p_pct], ["Protein","rest"], [MACRO_COLORS["Protein"], ("rgba(255,255,255,0.06)" if st.session_state.theme=='dark' else "rgba(0,0,0,0.06)")], "Protein", st.session_state.theme)
            charts_html += chartjs_donut_html([c_pct, 100-c_pct], ["Carbs","rest"], [MACRO_COLORS["Carbs"], ("rgba(255,255,255,0.06)" if st.session_state.theme=='dark' else "rgba(0,0,0,0.06)")], "Carbs", st.session_state.theme)
            charts_html += chartjs_donut_html([f_pct, 100-f_pct], ["Fat","rest"], [MACRO_COLORS["Fat"], ("rgba(255,255,255,0.06)" if st.session_state.theme=='dark' else "rgba(0,0,0,0.06)")], "Fat", st.session_state.theme)
            charts_html += chartjs_donut_html([fi_pct, 100-fi_pct], ["Fiber","rest"], [MACRO_COLORS["Fiber"], ("rgba(255,255,255,0.06)" if st.session_state.theme=='dark' else "rgba(0,0,0,0.06)")], "Fiber", st.session_state.theme)
            charts_html += "</div>"
            st_html(charts_html, height=340)

            # Macro bars (animated)
            bars_html = "<div style='width:95%; max-width:980px; margin:18px auto 6px auto;'>"
            bars_html += macro_bar_html(p, MACRO_COLORS["Protein"], "Protein", max_cap=50, theme=st.session_state.theme)
            bars_html += "<div style='height:10px;'></div>"
            bars_html += macro_bar_html(c, MACRO_COLORS["Carbs"], "Carbs", max_cap=120, theme=st.session_state.theme)
            bars_html += "<div style='height:10px;'></div>"
            bars_html += macro_bar_html(f, MACRO_COLORS["Fat"], "Fat", max_cap=60, theme=st.session_state.theme)
            bars_html += "<div style='height:10px;'></div>"
            bars_html += macro_bar_html(fi, MACRO_COLORS["Fiber"], "Fiber", max_cap=30, theme=st.session_state.theme)
            bars_html += "</div>"

            # animation script: ensure bar fills animate after rendering
            bars_html += textwrap.dedent("""
            <script>
            (function(){
              // Add small timeout to trigger transitions
              setTimeout(()=> {
                const fills = document.querySelectorAll('.fill');
                fills.forEach((el) => {
                  const w = el.style.width;
                  el.style.width = '0%';
                  setTimeout(()=> el.style.width = w, 80);
                });
              }, 80);
            })();
            </script>
            """)
            st_html(bars_html, height=300)

    else:
        st.info("Upload an image to analyze a dish.")

# ================== PAGE: CALORIE CALCULATOR ==================
elif menu == "🥗 Calorie Calculator":
    st.markdown("<h2 style='color: var(--accent);'>🥗 Total Meal Calorie Calculator</h2>", unsafe_allow_html=True)
    st.markdown("<p class='small-muted'>Type to filter foods and select servings.</p>", unsafe_allow_html=True)
    col_search, col_reset = st.columns([4,1])
    with col_search:
        query = st.text_input("Search for food:", "")
    with col_reset:
        if st.button("Reset"):
            st.experimental_rerun()

    matches = [k for k in sorted(NUTRITION_DB.keys()) if query.lower() in k.lower()]
    total = 0
    chosen = {}
    if not matches:
        st.info("No matches found.")
    else:
        for food in matches:
            cols = st.columns([3,1,1])
            cols[0].markdown(f"**{food}** — {NUTRITION_DB[food]['per_serving']['serving']}")
            qty = cols[1].number_input(f"qty_{food}", 0, 10, 0, key=f"qty_{food}")
            if qty > 0:
                cal = NUTRITION_DB[food]['per_serving']['calories'] * qty
                chosen[food] = cal
                total += cal
            cols[2].write("")
    if st.button("Calculate Total"):
        st.success(f"### 🔥 Total Calories: **{total} kcal**")
        if chosen:
            st.subheader("Breakdown")
            for k,v in chosen.items():
                st.write(f"🍛 {k}: {v} kcal")

# ================== PAGE: COMPARISON ==================
elif menu == "⚖️ Food Comparison":
    st.markdown("<h2 style='color: var(--accent);'>⚖️ Compare Two Foods</h2>", unsafe_allow_html=True)
    st.markdown("<p class='small-muted'>Choose two foods and compare per-100g nutrition.</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        f1 = st.selectbox("Food A", list(NUTRITION_DB.keys()), key="cmp1")
    with c2:
        f2 = st.selectbox("Food B", list(NUTRITION_DB.keys()), key="cmp2")
    if f1 and f2:
        A = NUTRITION_DB[f1]["per100g"]
        B = NUTRITION_DB[f2]["per100g"]
        colA, colB = st.columns(2)
        with colA:
            st.markdown(textwrap.dedent(f"""
            <div class='comp-box' style='background:#E8F8F5; padding:18px; border-radius:12px;'>
                <h4 style='margin-top:0'>{f1} (Per 100g)</h4>
                <b>Calories:</b> {A['calories']} kcal<br>
                <b>Protein:</b> {A['protein']} g<br>
                <b>Carbs:</b> {A['carbs']} g<br>
                <b>Fat:</b> {A['fat']} g<br>
                <b>Fiber:</b> {A['fiber']} g<br>
            </div>
            """), unsafe_allow_html=True)
        with colB:
            st.markdown(textwrap.dedent(f"""
            <div class='comp-box' style='background:#FEF5E7; padding:18px; border-radius:12px;'>
                <h4 style='margin-top:0'>{f2} (Per 100g)</h4>
                <b>Calories:</b> {B['calories']} kcal<br>
                <b>Protein:</b> {B['protein']} g<br>
                <b>Carbs:</b> {B['carbs']} g<br>
                <b>Fat:</b> {B['fat']} g<br>
                <b>Fiber:</b> {B['fiber']} g<br>
            </div>
            """), unsafe_allow_html=True)

# ---------------- Footer ----------------
st.markdown(textwrap.dedent("""
<br><br>
<hr>
<p class='footer'>Created with ❤️ by <b>Pallavi</b> </p>
"""), unsafe_allow_html=True)
