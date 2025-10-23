# ui/app.py
import os, sys, json, re
from typing import Optional
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------- Ensure repo import path ----------
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# ---------- Engine imports ----------
from engine.io import load_excel, load_csv
from engine.validate import validate_columns
from engine.compute_core import compute_core
from engine.taxes import compute_vat, compute_zakat
from engine.export import to_json

# ---------- Streamlit config ----------
st.set_page_config(page_title="Rakeem", layout="wide")

# ---------- Custom CSS (RTL + badges + alerts RTL) ----------
st.markdown("""
<style>
.block-container {padding-top:1rem; padding-bottom:2rem;}
.rtl {direction: rtl; text-align: right;}
.kpi-card {background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:12px 14px;margin-bottom:10px}
.kpi-label{font-size:0.9rem;color:#64748b}
.kpi-value{font-weight:700;font-size:1.3rem}
.note{background:#fff7ed;border:1px dashed #fdba74;border-radius:10px;padding:10px 12px;margin:8px 0}
.hr{height:1px;background:#e5e7eb;margin:14px 0}
.chat-bubble{border:1px solid #e5e7eb;border-radius:14px;padding:10px 12px;margin:6px 0}
.chat-bubble.user{background:#ecfeff}
.chat-bubble.assistant{background:#f8fafc}

/* شيبس لعناوين Topic/Question/Answer/Source/Example — أصغر ومضبوطة */
.label-chip{
  display:inline-block;
  background:#eef2ff; color:#111827;
  border:1px solid #c7d2fe; border-radius:9999px;
  padding:2px 8px;             /* أصغر */
  font-size:.80rem;            /* أصغر */
  font-weight:700;
  line-height:1.1;             /* يمنع التداخل */
  margin:0 6px 6px 0;          /* فراغ أوضح بين الشيبسات */
  vertical-align:middle;
}

/* القوائم داخل البوكس تكون داخلية ومُبعدة عن الحافة */
.chat-bubble.rtl ul { 
  list-style-type: disc; 
  list-style-position: inside; 
  padding-right: 16px; 
  margin: 6px 0; 
}
.rtl ul {
  list-style-type: disc;
  list-style-position: inside;
  padding-right: 16px;
  margin: 6px 0;
}

/* صناديق التنبيه (info/warning/error) RTL داخل البوكس نفسه */
[data-testid="stAlert"] { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

def sar(x: float) -> str:
    try:
        return f"{float(x):,.0f} ريال"
    except Exception:
        return "—"

# ---------- Header ----------
st.title("ركيم — Rakeem (SME Financial Assistant) 🇸🇦")
st.markdown("""
<div class="rtl">
  <p><b>📂 ارفع ملفك المالي</b> لعرض مؤشرات الأداء، وحساب ضريبة القيمة المضافة والزكاة، مع رسوم بيانية مبسطة.</p>
  <div class="note">تنبيه: الأنواع المسموح بها: Excel (.xlsx) و CSV (.csv).</div>
</div>
<div class="hr"></div>
<p><b>📂Upload your financial file</b> to see key performance metrics, VAT and Zakat, with simple visual charts.</p>
<div class="note">Note: Supported formats are Excel (.xlsx) and CSV (.csv) only.</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.header("📂 رفع الملف المالي")
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel (.xlsx/.xls) or CSV", type=["xlsx", "xls", "csv"]
)
if uploaded_file is None:
    st.info("للبدء من فضلك ارفع الملف من الشريط الجانبي.")
    st.stop()

# ---------- Load file ----------
try:
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext in ("xlsx", "xls"):
        df_raw = load_excel(uploaded_file, sheet=0)
    elif ext == "csv":
        df_raw = load_csv(uploaded_file)
    else:
        st.error("صيغة الملف غير مدعومة.")
        st.stop()
except Exception as e:
    st.error(f"خطأ أثناء قراءة الملف: {e}")
    st.stop()

# ---------- Validate ----------
try:
    validate_columns(df_raw)
except Exception as e:
    st.error(f"خطأ في التحقق من الأعمدة: {e}")
    st.stop()

# ---------- Compute ----------
try:
    df = compute_core(df_raw)
except Exception as e:
    st.error(f"خطأ أثناء الحسابات الأساسية: {e}")
    st.stop()

try:
    net_vat = float(compute_vat(df))
except Exception:
    net_vat = 0.0
try:
    zakat_due = float(compute_zakat(df))
except Exception:
    zakat_due = 0.0

# ---------- Engine Output ----------
try:
    engine_json = to_json(df, include_rows=False)
    engine_output = json.loads(engine_json)
except Exception:
    engine_output = None

# ---------- KPIs ----------
total_revenue = float(df.get("revenue", pd.Series([0])).fillna(0).sum())
total_expenses = float(df.get("expenses", pd.Series([0])).fillna(0).sum())
total_profit   = float(df.get("profit", pd.Series([0])).fillna(0).sum())
total_cashflow = float(df.get("cash_flow", pd.Series([0])).fillna(0).sum())

k1, k2, k3, k4 = st.columns(4)
with k1: st.markdown(f'<div class="kpi-card rtl"><div class="kpi-label">إجمالي الإيرادات</div><div class="kpi-value">{sar(total_revenue)}</div></div>', unsafe_allow_html=True)
with k2: st.markdown(f'<div class="kpi-card rtl"><div class="kpi-label">إجمالي المصروفات</div><div class="kpi-value">{sar(total_expenses)}</div></div>', unsafe_allow_html=True)
with k3: st.markdown(f'<div class="kpi-card rtl"><div class="kpi-label">صافي الربح</div><div class="kpi-value">{sar(total_profit)}</div></div>', unsafe_allow_html=True)
with k4: st.markdown(f'<div class="kpi-card rtl"><div class="kpi-label">التدفق النقدي</div><div class="kpi-value">{sar(total_cashflow)}</div></div>', unsafe_allow_html=True)

t1, t2 = st.columns(2)
with t1: st.markdown(f'<div class="kpi-card rtl"><div class="kpi-label">صافي ضريبة القيمة المضافة</div><div class="kpi-value">{sar(net_vat)}</div></div>', unsafe_allow_html=True)
with t2: st.markdown(f'<div class="kpi-card rtl"><div class="kpi-label">الزكاة المستحقة</div><div class="kpi-value">{sar(zakat_due)}</div></div>', unsafe_allow_html=True)

# ---------- Summary (top section) ----------
date_min = pd.to_datetime(df["date"]).min() if "date" in df.columns else None
date_max = pd.to_datetime(df["date"]).max() if "date" in df.columns else None
st.markdown(f"""
<div class="rtl">
  <h4>📊 ملخص مالي مختصر</h4>
  <ul>
    <li>📈 إجمالي الإيرادات: <b>{sar(total_revenue)}</b></li>
    <li>💸 إجمالي المصروفات: <b>{sar(total_expenses)}</b></li>
    <li>💰 صافي الربح: <b>{sar(total_profit)}</b></li>
    <li>💧 التدفق النقدي: <b>{sar(total_cashflow)}</b></li>
    <li>🗓️ الفترة: <b>{date_min:%d-%m-%Y}</b> → <b>{date_max:%d-%m-%Y}</b></li>
  </ul>
</div>
""", unsafe_allow_html=True)

# ---------- Charts ----------
st.markdown('<div class="rtl"><h4>📈 الاتجاهات الشهرية</h4></div>', unsafe_allow_html=True)
tabs = st.tabs(["الإيرادات", "المصروفات", "الربح"])
with tabs[0]: st.plotly_chart(px.line(df, x="date", y="revenue", title="الإيرادات"), use_container_width=True)
with tabs[1]: st.plotly_chart(px.line(df, x="date", y="expenses", title="المصروفات"), use_container_width=True)
with tabs[2]: st.plotly_chart(px.line(df, x="date", y="profit", title="الربح"), use_container_width=True)

# ---------- Recommendations ----------
st.markdown('<div class="rtl"><h4>💡 توصيات تلقائية</h4></div>', unsafe_allow_html=True)
recs = []
avg_margin = float(df.get("profit_margin", pd.Series([0])).fillna(0).mean())
if avg_margin < 10: recs.append("هامش الربح منخفض (<10%) — راجع التسعير أو خفض المصروفات.")
if total_cashflow < 0: recs.append("التدفق النقدي سالب — فكّر في تمويل قصير الأجل أو تأجيل مصروفات غير ضرورية.")
if net_vat > 0: recs.append("هناك صافي VAT مستحق — احرص على تقديم الإقرار في الوقت المحدد.")
if zakat_due > 0: recs.append("يبدو أن الزكاة مستحقة — تحقق من الوعاء الزكوي واستعد للسداد.")
if recs:
    st.markdown('<div class="rtl">', unsafe_allow_html=True)
    for r in recs:
        st.info(r)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("لا توجد تحذيرات فورية بناءً على البيانات الحالية.")

# ---------- Details ----------
with st.expander("🧾 الجدول التفصيلي + المخرجات الخام"):
    st.dataframe(df)
    if engine_output:
        st.json(engine_output, expanded=False)

# ---------- Downloads ----------
left, right = st.columns(2)
if engine_output:
    left.download_button(
        "Download JSON (Engine Output)",
        data=json.dumps(engine_output, indent=2, ensure_ascii=False),
        file_name="rakeem_output.json",
        mime="application/json",
    )
csv_bytes = df.to_csv(index=False).encode("utf-8")
right.download_button(
    "Download CSV (computed)",
    data=csv_bytes,
    file_name="computed.csv",
    mime="text/csv",
)

# ===================== Chat Section =====================
st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
st.markdown('<div class="rtl"><h3>💬 المحادثة الذكية</h3></div>', unsafe_allow_html=True)

# نختار الباك-إند المتاح
_backend = None
try:
    from llm.run import chat_answer as _chain_chat_answer
    _backend = ("chain", _chain_chat_answer)
except Exception:
    try:
        from llm.simple_backend import answer as _simple_answer
        _backend = ("simple", _simple_answer)
    except Exception:
        _backend = None
        st.warning("⚠ لا يوجد باك-إند متاح للشات (Chain/Simple).")

def _df_ctx():
    for key in ("df","financial_df","computed_df","results_df"):
        if key in globals() and "DataFrame" in str(type(globals()[key])): return globals()[key]
        if key in st.session_state and "DataFrame" in str(type(st.session_state[key])): return st.session_state[key]
    return None

# تنسيق الكلمات داخل البادجات + إزالة الأقواس
def stylize_labels(text: str) -> str:
    if not isinstance(text, str):
        return text
    # إزالة الأقواس حول المفاتيح
    text = re.sub(r"\[\s*(Topic|Question|Answer|Example|Source)\s*\]", r"\1", text)
    # تحويل الكلمات إلى شيبس inline
    for lab in ["Topic", "Question", "Answer", "Example", "Source"]:
        text = re.sub(rf"\b{lab}\b", f'<span class="label-chip"><b>{lab}</b></span>', text)
    return text

# يحوّل سطر الملخص المالي داخل ردّ الشات لقائمة نقطية مرتّبة + يضيف الإيموجيز ويشيل النجوم من العنوان
def normalize_fin_summary(text: str) -> str:
    if not isinstance(text, str):
        return text

    # 1) تنسيق العنوان: شيل النجوم وحط عنوان نظيف وبولد مع 📊
    text = re.sub(
        r"\*+\s*ملخص\s+مالي\s+مختصر\s*[:\-–]*\s*\*+",
        r"<b>📊 ملخص مالي مختصر</b>",
        text
    )

    # 2) حوّل السطر المكدّس إلى قائمة نقطية
    pattern = (
        r"(إجمالي الإيرادات:\s*[^-\n]+)\s*-\s*"
        r"(إجمالي المصروفات:\s*[^-\n]+)\s*-\s*"
        r"(صافي الربح:\s*[^-\n]+)\s*-\s*"
        r"(التدفق النقدي:\s*[^-\n]+)"
    )
    def _to_list(m):
        items = [m.group(i) for i in range(1, 5)]
        lis = "".join(f"<li>{it}</li>" for it in items)
        return ('<ul style="list-style-type:disc; padding-right:16px; margin:6px 0;">'
                + lis + "</ul>")
    text = re.sub(pattern, _to_list, text)

    # 3) لو الفترة موجودة بعدها، خليها سطر مستقل واضح
    text = re.sub(
        r"(الفترة:\s*\d{2}-\d{2}-\d{4}\s*→\s*\d{2}-\d{2}-\d{4})",
        r'<div style="margin-top:0.2rem;"><b>\1</b></div>',
        text
    )

    # 4) أضف الإيموجيز للعناصر داخل النص (بعد ما سوّينا القائمة عشان ما نخرب الـ regex)
    text = text.replace("إجمالي الإيرادات:", "📈 إجمالي الإيرادات:")
    text = text.replace("إجمالي المصروفات:", "💸 إجمالي المصروفات:")
    text = text.replace("صافي الربح:", "💰 صافي الربح:")
    text = text.replace("التدفق النقدي:", "💧 التدفق النقدي:")

    return text

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role":"assistant","content":"مرحبًا! ارفعي الملف ثم اسألي عن الربحية أو الضريبة أو الزكاة."}
    ]

# عرض سجلّ المحادثة
for m in st.session_state.chat_messages:
    cls = "assistant" if m["role"] == "assistant" else "user"
    content = stylize_labels(m["content"]) if m["role"] == "assistant" else m["content"]
    st.markdown(f'<div class="chat-bubble {cls} rtl">{content}</div>', unsafe_allow_html=True)

# إدخال المستخدم
user_q = st.chat_input("اكتبي سؤالك هنا…")
if user_q:
    st.session_state.chat_messages.append({"role":"user","content":user_q})
    st.markdown(f'<div class="chat-bubble user rtl">{user_q}</div>', unsafe_allow_html=True)

    try:
        if not _backend:
            raise RuntimeError("لا يوجد باك-إند للشات.")
        mode, fn = _backend
        reply_text, sources = (fn(user_q, df=_df_ctx()) if mode=="simple"
                               else fn(user_q, df=_df_ctx()))

        # خزّن وعرِض الرد: ملخص مالي منسّق + شيبس أصغر
        st.session_state.chat_messages.append({"role":"assistant","content":reply_text})
        formatted_reply = normalize_fin_summary(reply_text)
        st.markdown(
            f'<div class="chat-bubble assistant rtl">{stylize_labels(formatted_reply)}</div>',
            unsafe_allow_html=True
        )

        # مصادر — مسافة مريحة + ZATCA كرابط بنفس شكل الشيب
        if sources:
            chip_parts = []
            for s in sources:
                label = s.strip()
                if label == "ZATCA":
                    chip_parts.append(
                        "<a href='https://zatca.gov.sa' target='_blank' "
                        "class='label-chip' style='text-decoration:none; color:inherit;'>"
                        "<b>ZATCA</b></a>"
                    )
                else:
                    chip_parts.append(
                        f"<span class='label-chip'><b>{label}</b></span>"
                    )
            chips = "".join(chip_parts)
            st.markdown(f"<div class='rtl'><b>المصادر:</b> {chips}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"تعذر توليد الرد: {e}")
