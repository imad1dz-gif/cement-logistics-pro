import plotly
import streamlit as st
import pandas as pd
import plotly.express as px
# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="Cement Logistics PRO", layout="wide")

# حقن كود CSS للتصميم النيومورفي (Silver-Blue)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #e0e5ec; font-family: 'Inter', sans-serif; }
    
    /* الكروت البارزة */
    .neu-card {
        background: #e0e5ec;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 8px 8px 15px #a3b1c6, -8px -8px 15px #ffffff;
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* الكروت الغائرة (لـ Top 3) */
    .neu-pressed {
        background: #e0e5ec;
        border-radius: 15px;
        padding: 15px;
        box-shadow: inset 6px 6px 12px #a3b1c6, inset -6px -6px 12px #ffffff;
        margin-bottom: 12px;
        border: none;
    }

    .stat-label { color: #64748b; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-value { color: #1e293b; font-size: 1.7rem; font-weight: 800; margin-top: 5px; }
    .top-res-name { color: #3b82f6; font-weight: 700; font-size: 0.9rem; }
    .top-res-val { color: #1e293b; font-weight: 800; font-size: 1.1rem; }
    
    /* تنسيق القائمة الجانبية */
    [data-testid="stSidebar"] { background-color: #e0e5ec; border-right: none; box-shadow: inset -5px 0px 10px #a3b1c6; }
    </style>
""", unsafe_allow_html=True)

# 2. قاموس الاختصارات للمنتجات
PROD_MAP = {
    "CHAMIL - Palette / Ciment à usages courants en Palette de 2,2 Tn": "CH-PAL 2.2",
    "CHAMIL - Palette / Ciment à usages courants en Palette de 2,15 Tn": "CH-PAL 2.15",
    "CEM I \\52.5 N SARIE - VRAC": "SAR-VRAC",
    "CEM II/A-L 42.5 N CHAMIL - VRAC": "CHAM-VRAC"
}

def get_short(name):
    return PROD_MAP.get(str(name), str(name)[:15])

# 3. دالة حساب الكمية بالمعامل (للمبلتن فقط)
def calc_qty_factor(row, col_name='Quantité Réservée'):
    qty = row[col_name] if pd.notnull(row[col_name]) else 0
    prod = str(row['Produit'])
    if "2.2" in prod: return qty * 2.2
    if "2.15" in prod: return qty * 2.15
    return qty

# 4. معالجة البيانات والتحميل
uploaded_file = st.sidebar.file_uploader("📂 ارفع ملف Moniteur de Chargement", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # تحويل التواريخ
    df['Date Permis_dt'] = pd.to_datetime(df['Date Permis'], errors='coerce')
    df['Date Heure Entrée'] = pd.to_datetime(df['Date Heure Entrée'], errors='coerce')
    df['Date Heure Sortie'] = pd.to_datetime(df['Date Heure Sortie'], errors='coerce')
    df['Date Heure Permis'] = pd.to_datetime(df['Date Heure Permis'], errors='coerce')
    
    # قائمة اختيار التاريخ (الفلتر)
    available_dates = sorted(df['Date Permis_dt'].dropna().dt.date.unique(), reverse=True)
    target_date = st.sidebar.selectbox("📅 اختر تاريخ التقرير (Filter)", available_dates)
    
    # تصفية البيانات الأساسية
    df_f = df[df['Date Permis_dt'].dt.date == target_date].copy()

    if not df_f.empty:
        # --- حساب المؤشرات (KPIs) ---
        
        # مؤشر Reliquats
        mask_rel = df_f["Position File D'attente"].astype(str).str.contains('-', na=False)
        reliquats_val = df_f[mask_rel].apply(calc_qty_factor, axis=1).sum()

        # مؤشر Total Reservations (الكل بالمعامل + Reliquats)
        total_res_val = df_f.apply(calc_qty_factor, axis=1).sum() + reliquats_val

        # مؤشر In Progress (Permis, Entrée بالمعامل)
        mask_ip = df_f['Etat Réservation'].isin(['Permis', 'Entrée'])
        ip_val = df_f[mask_ip].apply(calc_qty_factor, axis=1).sum()

        # مؤشر Delivered & Qty Shipped (مفوتر خام)
        mask_del = df_f['Etat Réservation'].isin(['Livrée', 'Réceptionné'])
        delivered_val = df_f[mask_del]['Quantité Facturée'].sum()

        # حساب GIGO و YIGO بالدقائق
        gigo_df = df_f[mask_del].dropna(subset=['Date Heure Sortie', 'Date Heure Entrée'])
        avg_gigo = (gigo_df['Date Heure Sortie'] - gigo_df['Date Heure Entrée']).dt.total_seconds().mean() / 60 if not gigo_df.empty else 0
        
        yigo_df = df_f[mask_del].dropna(subset=['Date Heure Sortie', 'Date Heure Permis'])
        avg_yigo = (yigo_df['Date Heure Sortie'] - yigo_df['Date Heure Permis']).dt.total_seconds().mean() / 60 if not yigo_df.empty else 0

        # --- العرض: الصف الأول (الكروت الأساسية) ---
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="neu-card"><div class="stat-label">Total Reservations</div><div class="stat-value">{total_res_val:,.1f}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="neu-card"><div class="stat-label">In Progress</div><div class="stat-value">{ip_val:,.1f}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="neu-card"><div class="stat-label">Delivered</div><div class="stat-value">{delivered_val:,.1f}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="neu-card"><div class="stat-label">Reliquats (-)</div><div class="stat-value" style="color:#ef4444;">{reliquats_val:,.1f}</div></div>', unsafe_allow_html=True)

        # --- العرض: الصف الثاني (Performance + Top 3) ---
        st.write("---")
        col_perf, col_top = st.columns([1.5, 2.5])

        with col_perf:
            st.markdown('<div class="stat-label" style="text-align:center; margin-bottom:15px;">⏱️ Performance Metrics</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="neu-card"><div class="stat-label">Avg GIGO</div><div class="stat-value">{avg_gigo:.0f} <small>min</small></div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="neu-card"><div class="stat-label">Avg YIGO</div><div class="stat-value">{avg_yigo:.0f} <small>min</small></div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="neu-card"><div class="stat-label">Qty Shipped</div><div class="stat-value">{delivered_val:,.1f}</div></div>', unsafe_allow_html=True)

        with col_top:
            st.markdown('<div class="stat-label" style="margin-bottom:15px;">🏆 Top 3 Reservations (Day)</div>', unsafe_allow_html=True)
            top_3 = df_f.nlargest(3, 'Quantité Réservée')
            max_val = top_3['Quantité Réservée'].max() if not top_3.empty else 1
            
            for _, row in top_3.iterrows():
                short_prod = get_short(row['Produit'])
                client = str(row['Client'])[:20]
                progress = (row['Quantité Réservée'] / max_val) * 100
                st.markdown(f"""
                    <div class="neu-pressed">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span class="top-res-name">{short_prod}</span>
                            <span class="top-res-val">{row['Quantité Réservée']:,.1f} Tn</span>
                        </div>
                        <div style="color:#64748b; font-size: 0.8rem; margin-bottom: 8px;">Client: {client}</div>
                        <div style="background: #cfd6e1; border-radius: 10px; height: 8px; width: 100%;">
                            <div style="background: #3b82f6; height: 8px; width: {progress}%; border-radius: 10px;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # --- الرسم البياني النهائي ---
        st.write("---")
        df_f['Short_Prod'] = df_f['Produit'].apply(get_short)
        fig = px.bar(df_f, x='Short_Prod', y='Quantité Réservée', color='Etat Réservation',
                     barmode='group', template="plotly_white", title="Product Distribution (Shortened Names)")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, width='stretch')

        # حفظ البيانات للجلسة لتعمل صفحات التقارير والمقارنة
        st.session_state['main_df'] = df
    else:
        st.warning(f"لا توجد بيانات متاحة لتاريخ {target_date}")
else:

    st.info("👋 بانتظار رفع ملف الإكسيل للبدء في التحليل...")
