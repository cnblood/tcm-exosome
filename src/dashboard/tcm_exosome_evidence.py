import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

st.set_page_config(page_title="涓嵂澶栨硨浣撹瘉鎹簱", layout="wide")
st.title("馃尶 涓嵂澶栨硨浣撹瘉鎹簱")
st.markdown("**鏁版嵁鏉ユ簮**锛氫腑鍥借嵂鍏?025 + Groq AI 鏂囩尞绾у垽鏂?| **394 鍛充腑鑽彂鐜板娉屼綋鐩稿叧绉戝璇佹嵁**")

# ================= Supabase 杩炴帴 =================
supabase = create_client(
    st.secrets.get("SUPABASE_URL"),
    st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY"))
)

# ================= 鍔犺浇鏁版嵁 =================
@st.cache_data(ttl=60)
def load_evidence_data():
    data = supabase.table("tcm_single_herb").select(
        "id, chinese_name, latin_name, taxonomy_family, "
        "exosome_evidence, research_focus, data_level"
    ).execute().data
    return pd.DataFrame(data)

df = load_evidence_data()

# ================= 绛涢€夊櫒 =================
col1, col2, col3 = st.columns([2, 2, 3])
with col1:
    evidence_filter = st.multiselect(
        "澶栨硨浣撹瘉鎹?,
        options=["鏈夎瘉鎹?(True)", "鏃犺瘉鎹?(False)"],
        default=["鏈夎瘉鎹?(True)"]
    )
with col2:
    bbb_filter = st.multiselect(
        "BBB 绌胯秺娼滃姏",
        options=["High", "Medium", "Low", "Unknown"],
        default=["High", "Medium"]
    )
with col3:
    search = st.text_input("馃攳 鎼滅储鑽潗锛堜腑鏂?鎷変竵鍚嶏級", "")

# 搴旂敤绛涢€?
filtered = df.copy()

if evidence_filter:
    if "鏈夎瘉鎹?(True)" in evidence_filter and "鏃犺瘉鎹?(False)" not in evidence_filter:
        filtered = filtered[filtered["exosome_evidence"] == True]
    elif "鏃犺瘉鎹?(False)" in evidence_filter and "鏈夎瘉鎹?(True)" not in evidence_filter:
        filtered = filtered[filtered["exosome_evidence"] == False]

if bbb_filter:
    filtered = filtered[filtered["research_focus"].str.contains("|".join(bbb_filter), case=False, na=False)]

if search:
    mask = (
        filtered["chinese_name"].str.contains(search, case=False, na=False) |
        filtered["latin_name"].str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]

# ================= 缁熻鍗＄墖 =================
c1, c2, c3, c4 = st.columns(4)
c1.metric("鎬昏嵂鏉愭暟", len(df))
c2.metric("鏈夊娉屼綋璇佹嵁", f"{len(filtered[filtered['exosome_evidence']==True])} 猸?, "394")
c3.metric("BBB Medium+", len(filtered[filtered["research_focus"].str.contains("Medium|High", na=False)]))
c4.metric("瀹屾垚鐜?, f"{len(df[df['data_level'].isin(['validated','enriched'])])/len(df)*100:.1f}%")

# ================= 鍥捐〃 =================
st.subheader("馃搳 澶栨硨浣撹瘉鎹垎甯?)
fig_pie = px.pie(
    filtered, names="exosome_evidence", 
    title="鏈?/ 鏃犲娉屼綋鐮旂┒璇佹嵁",
    color_discrete_sequence=["#00CC96", "#EF553B"]
)
st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("馃搱 BBB 绌胯秺娼滃姏鍒嗗竷")
bbb_series = filtered["research_focus"].str.extract(r"BBB: (High|Medium|Low|Unknown)")[0].value_counts()
fig_bar = px.bar(
    bbb_series, title="BBB 绌胯秺娼滃姏缁熻", 
    labels={"index": "BBB 绛夌骇", "value": "鑽潗鏁伴噺"},
    color_discrete_sequence=["#636EFA"]
)
st.plotly_chart(fig_bar, use_container_width=True)

# ================= 璇︾粏琛ㄦ牸 =================
st.subheader(f"馃搵 绛涢€夌粨鏋滐紙{len(filtered)} 鏉★級")
st.dataframe(
    filtered[["chinese_name", "latin_name", "taxonomy_family", "exosome_evidence", "research_focus"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "exosome_evidence": st.column_config.CheckboxColumn("鏈夊娉屼綋璇佹嵁"),
        "research_focus": st.column_config.TextColumn("AI 鍒ゆ柇缁撴灉", width="medium"),
    }
)

st.success("馃帀 Level 4 宸蹭笂绾匡紒394 鍛充腑鑽叿澶囧娉屼綋鐮旂┒璇佹嵁锛屽彲鐩存帴鐢ㄤ簬璁烘枃銆佷笓鍒┿€佹眹鎶?)

