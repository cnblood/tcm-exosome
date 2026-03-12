import streamlit as st
import pandas as pd
import plotly.express as px
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

@st.cache_resource
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

@st.cache_data(ttl=600)
def load(table):
    client = get_supabase()
    if not client:
        return pd.DataFrame()
    try:
        res = client.table(table).select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except:
        return pd.DataFrame()

def render_gene_dashboard():
    st.markdown("# Genomics Analysis")
    st.caption("TCM × Exosome × Gene Network")

    genes_df = load("genes")
    mirna_df = load("mirna")
    cargo_df = load("exosome_cargo")
    hg_df = load("herb_gene_relations")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Genes", len(genes_df))
    c2.metric("miRNA", len(mirna_df))
    c3.metric("Cargo", len(cargo_df))
    c4.metric("Herb-Gene", len(hg_df))

    tab1, tab2, tab3, tab4 = st.tabs(["Genes", "Herb-Gene Network", "miRNA & Cargo", "Pathways"])

    with tab1:
        st.markdown("### Gene List")
        if not genes_df.empty:
            cols = [c for c in ["gene_symbol","gene_name","chromosome","ncbi_gene_id","uniprot_id"] if c in genes_df.columns]
            st.dataframe(genes_df[cols], use_container_width=True, hide_index=True)
        else:
            st.info("No gene data.")

    with tab2:
        st.markdown("### Herb-Gene Relations")
        if not hg_df.empty:
            cols = [c for c in ["herb_name","gene_symbol","interaction_type","mechanism","confidence_score"] if c in hg_df.columns]
            st.dataframe(hg_df[cols], use_container_width=True, hide_index=True)
            if "herb_name" in hg_df.columns and "gene_symbol" in hg_df.columns:
                fig = px.scatter(hg_df, x="herb_name", y="gene_symbol",
                                 color="interaction_type" if "interaction_type" in hg_df.columns else None,
                                 size_max=15, title="Herb-Gene Interaction Map")
                fig.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="white")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No herb-gene data.")

    with tab3:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### miRNA")
            if not mirna_df.empty:
                cols = [c for c in ["mirna_id","source","function_note","is_exosome_cargo"] if c in mirna_df.columns]
                st.dataframe(mirna_df[cols], use_container_width=True, hide_index=True)
            else:
                st.info("No miRNA data.")
        with col_r:
            st.markdown("### Exosome Cargo")
            if not cargo_df.empty:
                cols = [c for c in ["cargo_name","cargo_type","tcm_herb","target_gene","biological_effect"] if c in cargo_df.columns]
                st.dataframe(cargo_df[cols], use_container_width=True, hide_index=True)
            else:
                st.info("No cargo data.")

    with tab4:
        pathway_df = load("pathway_enrichment")
        if not pathway_df.empty:
            cols = [c for c in ["herb_name","pathway_name","enrichment_score","p_value","gene_list"] if c in pathway_df.columns]
            st.dataframe(pathway_df[cols], use_container_width=True, hide_index=True)
            if "pathway_name" in pathway_df.columns and "enrichment_score" in pathway_df.columns:
                fig = px.bar(pathway_df.sort_values("enrichment_score", ascending=False).head(20),
                             x="enrichment_score", y="pathway_name", orientation="h",
                             color="herb_name" if "herb_name" in pathway_df.columns else None,
                             title="Top Enriched Pathways")
                fig.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="white", height=500)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pathway data.")