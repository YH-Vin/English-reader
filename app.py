import streamlit as st
from openai import OpenAI
import json
import datetime
import base64
import zlib

# -----------------------------------------------------------------------------
# 1. 极简主义视觉配置 (CSS Injection)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="DeepRead Pro", page_icon="📘", layout="wide")

# 自定义 CSS：去除杂乱边框，使用苹果风/Notion风的极简设计
custom_css = """
<style>
    /* 隐藏 Streamlit 默认的汉堡菜单和页脚 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 全局字体优化 */
    .stApp {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* 标题样式 */
    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.05em !important;
        color: #111 !important;
    }

    /* 按钮美化：扁平化设计 */
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 10px 24px !important;
        transition: transform 0.1s;
    }
    div.stButton > button:active {
        transform: scale(0.98);
    }
    
    /* 结果展示区的排版优化 */
    hr {
        margin: 2em 0 !important;
        border: none !important;
        border-top: 1px solid #eaeaea !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 会话状态与核心逻辑
# -----------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "user_level" not in st.session_state:
    st.session_state.user_level = "Intermediate"

def get_api_key():
    if "ALIYUN_API_KEY" in st.secrets:
        return st.secrets["ALIYUN_API_KEY"]
    return None

# --- 存档/读档核心功能 ---
def generate_save_token(data):
    """压缩并编码历史记录"""
    if not data: return ""
    try:
        json_str = json.dumps(data)
        compressed = zlib.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    except: return ""

def load_save_token(token):
    """解码并恢复历史记录"""
    try:
        decoded = base64.b64decode(token)
        json_str = zlib.decompress(decoded).decode('utf-8')
        return json.loads(json_str)
    except: return None

# --- AI 分析核心功能 ---
def analyze_text_pro(client, text, level, model):
    prompt = f"""
    You are an elite English Linguistics Professor. Analyze the provided text for a student at level: {level}.
    
    GOAL: Produce a structured learning guide like a high-quality textbook.
    
    OUTPUT FORMAT: Return STRICT JSON with these keys:
    1. "main_idea": Concise summary (2-3 sentences).
    2. "explanation": List of objects (keys: "title", "original", "meaning"). Focus on deep comprehension.
    3. "grammar": List of objects (keys: "title", "original", "breakdown"). Explain syntax/structure.
    4. "vocabulary": List of objects (keys: "word", "ipa", "definition", "context"). Max 6 hard words. Include IPA pronunciation.

    Original Text:
    {text}
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a JSON-speaking Linguistics Professor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 3. 侧边栏布局 (设置 & 备份)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key
    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input("API Key", type="password", placeholder="Paste Aliyun Key here")
        if not api_key:
            st.caption("⚠️ Key required to start.")
    
    st.divider()
    
    # Level Selection
    st.subheader("👤 User Level")
    st.session_state.user_level = st.selectbox(
        "Select your target level:",
        ["Beginner (A1-A2)", "Intermediate (B1-B2)", "Advanced (C1-C2)"],
        index=1
    )
    
    st.divider()
    
    # === 💾 存档黑科技 ===
    with st.expander("💾 Backup / Restore", expanded=False):
        st.caption("Use this token to save/load your progress across sessions.")
        
        # 导出
        st.markdown("**Export Token**")
        if st.session_state.history:
            token = generate_save_token(st.session_state.history)
            st.code(token, language="text")
            st.caption("👆 Copy this code to your notes.")
        else:
            st.info("No history to save yet.")
            
        st.markdown("---")
        
        # 导入
        st.markdown("**Import Token**")
        restore_token = st.text_input("Paste token here:", label_visibility="collapsed")
        if st.button("🔄 Restore Data", use_container_width=True):
            data = load_save_token(restore_token)
            if data:
                st.session_state.history = data
                st.toast("✅ Data restored successfully!", icon="🎉")
                st.rerun()
            else:
                st.error("Invalid token.")

# -----------------------------------------------------------------------------
# 4. 主界面 (Tabs)
# -----------------------------------------------------------------------------
st.title("📘 DeepRead Pro")
st.caption("Your AI-Powered Linguistics Tutor")

tab_analysis, tab_library = st.tabs(["✨ Deep Analysis", "📚 My Library"])

# === Tab 1: 深度分析 ===
with tab_analysis:
    # --- 📱 手机端提示 (插入在这里) ---
    st.markdown(
        """
        <div style='background-color: #fff0f0; padding: 10px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 20px;'>
            <strong style='color: #d8000c;'>⚠️ 手机用户请注意：</strong>
            <span style='color: #333;'>请点击页面左上角的 <b>></b> 箭头展开侧边栏输入 Key，或者在浏览器菜单中选择<b>“请求桌面网站”</b>以获得最佳体验。</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    # -------------------------------
    col_in, col_out = st.columns([1, 1.1])
    
    with col_in:
        st.markdown("#### Input Text")
        source_text = st.text_area(
            "Enter text to analyze...", 
            height=350, 
            placeholder="Paste English text here (e.g. from The Economist, NYT)..."
        )
        
        c1, c2 = st.columns([2, 1])
        with c1:
            model = st.selectbox("Model", ["qwen-plus", "qwen-max"], label_visibility="collapsed")
        with c2:
            analyze_btn = st.button("Analyze 🚀", type="primary", use_container_width=True)

    with col_out:
        st.markdown("#### Insight")
        result_box = st.container()

    # 触发逻辑
    if analyze_btn:
        if not api_key:
            st.toast("🚫 Please enter API Key first.")
        elif not source_text:
            st.toast("✍️ Please enter some text.")
        else:
            with result_box:
                with st.spinner("Analyzing structure, grammar, and context..."):
                    client = OpenAI(api_key=api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
                    data = analyze_text_pro(client, source_text, st.session_state.user_level, model)
                    
                    if "error" in data:
                        st.error(f"Error: {data['error']}")
                    else:
                        # -----------------------------------------------
                        # 构建完美的 Markdown 输出 (The Textbook Style)
                        # -----------------------------------------------
                        md_content = f"### **Main Idea**\n{data['main_idea']}\n\n"
                        
                        md_content += "---\n### **Detailed Explanation**\n\n"
                        for i, item in enumerate(data['explanation'], 1):
                            md_content += f"**{i}. {item['title']}**\n"
                            md_content += f"> *Original: \"{item['original']}\"*\n\n"
                            md_content += f"*   **Meaning:** {item['meaning']}\n\n"
                        
                        md_content += "---\n### **Grammar Breakdown**\n\n"
                        for i, item in enumerate(data['grammar'], 1):
                            md_content += f"**{i}. {item['title']}**\n"
                            md_content += f"> *\"{item['original']}\"*\n\n"
                            md_content += f"*   **Analysis:** {item['breakdown']}\n\n"
                            
                        md_content += "---\n### **Vocabulary**\n\n"
                        for i, item in enumerate(data['vocabulary'], 1):
                            md_content += f"**{i}. {item['word']}** `{item.get('ipa', '')}`\n"
                            md_content += f"*   **Def:** {item['definition']}\n"
                            md_content += f"*   **Ctx:** {item['context']}\n\n"

                        # 展示结果
                        st.markdown(md_content)
                        
                        # 自动存入历史
                        record = {
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "original": source_text,
                            "markdown": md_content
                        }
                        st.session_state.history.insert(0, record)
                        st.toast("✅ Analysis saved to Library!", icon="💾")

# === Tab 2: 历史资料库 ===
with tab_library:
    st.markdown("#### 🗂️ Knowledge Base")
    
    if not st.session_state.history:
        st.info("No records found. Go to 'Deep Analysis' to start.")
    else:
        # 工具栏
        col_tools, _ = st.columns([1, 3])
        with col_tools:
            if st.button("🗑️ Clear All History"):
                st.session_state.history = []
                st.rerun()

        st.divider()
        
        # 导出选择逻辑
        selected_records = []
        for i, note in enumerate(st.session_state.history):
            with st.container():
                # 使用两列布局：复选框 + 折叠面板
                c_check, c_content = st.columns([0.05, 0.95])
                with c_check:
                    # 垂直居中稍微有点难，直接放这里
                    if st.checkbox("", key=f"check_{i}"):
                        selected_records.append(note)
                with c_content:
                    with st.expander(f"📅 {note['time']} - {note['original'][:50]}..."):
                        st.markdown(note['markdown'])
            st.divider() # 分割线
            
        # 浮动/底部导出按钮
        if selected_records:
            st.success(f"Selected {len(selected_records)} notes.")
            
            # 生成最终的 Markdown 文件内容
            final_export = f"# DeepRead Study Notes\nGenerated: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
            for note in selected_records:
                final_export += f"## Record: {note['time']}\n"
                final_export += f"{note['markdown']}\n"
                final_export += "\n========================================\n\n"
            
            st.download_button(
                label="📥 Download Markdown (Print-Ready)",
                data=final_export,
                file_name=f"DeepRead_Notes_{datetime.datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                type="primary"
            )
    # 简单的清空逻辑
def clear_text():
    st.session_state.source_text = ""

# 在 text_area 绑定 key
source_text = st.text_area(..., key="source_text")
st.button("🗑️ 清空文本", on_click=clear_text)
