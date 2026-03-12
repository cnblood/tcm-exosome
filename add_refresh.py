import os

filepath = "src/dashboard/app.py"
with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
    code = f.read()

# 1. 注入强制刷新按钮（加在侧边栏）
if "st.cache_data.clear()" not in code and "with st.sidebar:" in code:
    code = code.replace(
        "with st.sidebar:", 
        "with st.sidebar:\n    if st.button('🔄 强制刷新数据 (Clear Cache)'):\n        st.cache_data.clear()\n        st.rerun()\n"
    )

with open(filepath, "w", encoding="utf-8") as f:
    f.write(code)

print("✅ 刷新按钮注入成功！马上重新打包！")
