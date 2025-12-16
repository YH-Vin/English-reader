import streamlit as st
from openai import OpenAI
import json
import datetime
import base64
import zlib

# -----------------------------------------------------------------------------
# 1. 页面与视觉配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DeepRead Pro",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 修复后的 CSS (删除了导致文字看不见的输入框样式) ---
custom_css = """
<style>
    /* 全局字体优化 */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* 隐藏 Streamlit 默认头部和页脚 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 标题样式 */
    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
    }

    /* 按钮样式 - 保持扁平化 */
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        transition: transform 0.1s;
    }
    div.stButton > button:active {
        transform: scale(0.98);
    }
    
    /* 分割线 */
    hr {
        margin: 2em 0 !important;
        border: none !important;
        border-top: 1px solid #eaeaea !important;
    }
    
    /* 手机端提示框的样式优化 */
    .mobile-alert {
        background-color: #fff0f0; 
        padding: 12px; 
        border-radius: 8px; 
        border-left: 5px solid #ff4b4b; 
        margin-bottom: 25px;
        color: #333; /* 强制提示框内文字为深色，防止深色模式下看不清 */
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 状态管理
# -----------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "user_level" not in st.session_state:
    st.session_state.user_level = "Intermediate (B1-B2)"

# -----------------------------------------------------------------------------
# 3. 核心功能函数库
# -----------------------------------------------------------------------------

def get_api_key():
    try:
        if "ALIYUN_API_KEY" in st.secrets:
            return st.secrets["ALIYUN_API_KEY"]
    except FileNotFoundError:
        pass 
    return None

def generate_save_token(data):
    if not data: return ""
    try:
        json_str = json.dumps(data)
        compressed = zlib.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    except Exception as e:
        return ""

def load_save_token(token):
    try:
        decoded = base64.b64decode(token)
        json_str = zlib.decompress(decoded).decode('utf-8')
        return json.loads(json_str)
    except Exception:
        return None

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
        content = response.choices[0].message.content
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "AI 返回格式异常，请重试。"}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 4. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    
    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input("🔑 API Key", type="password", placeholder="Paste Aliyun Key here")
        if not api_key:
            st.warning("⚠️ 请输入 Key 以使用")
    
    st.divider()
    
    st.subheader("👤 User Level")
    st.session_state.user_level = st.selectbox(
        "Select Target Level:",
        ["Beginner (A1-A2)", "Intermediate (B1-B2)", "Advanced (C1-C2)"],
        index=1
    )
    
    st.divider()
    
    with st.expander("💾 Backup / Restore", expanded=False):
        st.caption("防止数据丢失，请定期备份")
        if st.session_state.history:
            token = generate_save_token(st.session_state.history)
            st.markdown("**Export Token:**")
            st.code(token, language="text")
            st.caption("👆 全选复制，存入备忘录。")
        else:
            st.info("暂无记录可导出")
        st.markdown("---")
        restore_token = st.text_input("Import Token:", placeholder="Paste token here...", label_visibility="collapsed")
        if st.button("🔄 Restore Data", use_container_width=True):
            data = load_save_token(restore_token)
            if data:
                st.session_state.history = data
                st.toast("✅ 数据恢复成功！", icon="🎉")
                st.rerun()
            else:
                st.error("无效的存档码")

# -----------------------------------------------------------------------------
# 5. 主界面
# -----------------------------------------------------------------------------
st.title("📘 DeepRead Pro")
st.caption("Your AI-Powered Linguistics Tutor")

tab_analysis, tab_library = st.tabs(["✨ Deep Analysis", "📚 My Library"])

# === Tab 1: 深度分析 ===
with tab_analysis:
    # 手机提示 (强制黑色文字，防止深色模式看不见)
    st.markdown(
        """
        <div class="mobile-alert">
            <strong style='color: #d8000c;'>⚠️ 手机用户请注意：</strong>
            <span style='color: #333;'>请点击左上角 <b>></b> 箭头展开设置，或在浏览器菜单选择<b>“请求桌面网站”</b>以获得最佳体验。</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_in, col_out = st.columns([1, 1.1])
    
    with col_in:
        st.markdown("#### Input Text")
        # 这里去掉了 placeholder，因为在某些模式下也会导致视觉干扰
        source_text = st.text_area(
            "Content", 
            height=350, 
            label_visibility="collapsed"
        )
        
        c1, c2, c3 = st.columns([1.5, 1, 1])
        with c1:
            model = st.selectbox("Model", ["qwen-plus", "qwen-max"], label_visibility="collapsed")
        with c2:
            if st.button("🗑️ Clear", use_container_width=True):
                pass 
        with c3:
            analyze_btn = st.button("Analyze 🚀", type="primary", use_container_width=True)

    with col_out:
        st.markdown("#### Insight")
        result_box = st.container()

    if analyze_btn:
        if not api_key:
            st.toast("🚫 Please enter API Key first.", icon="🔒")
        elif not source_text:
            st.toast("✍️ Please paste some text.", icon="📝")
        else:
            with result_box:
                with st.spinner("Analyzing structure, grammar, and context..."):
                    try:
                        client = OpenAI(
                            api_key=api_key, 
                            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                        )
                        data = analyze_text_pro(client, source_text, st.session_state.user_level, model)
                        
                        if "error" in data:
                            st.error(f"Analysis Failed: {data['error']}")
                        else:
                            md_content = f"### **Main Idea**\n{data.get('main_idea', 'No summary available.')}\n\n"
                            md_content += "---\n### **Detailed Explanation**\n\n"
                            for i, item in enumerate(data.get('explanation', []), 1):
                                md_content += f"**{i}. {item['title']}**\n> *Original: \"{item['original']}\"*\n* **Meaning:** {item['meaning']}\n\n"
                            md_content += "---\n### **Grammar Breakdown**\n\n"
                            for i, item in enumerate(data.get('grammar', []), 1):
                                md_content += f"**{i}. {item['title']}**\n> *\"{item['original']}\"*\n* **Analysis:** {item['breakdown']}\n\n"
                            md_content += "---\n### **Vocabulary**\n\n"
                            for i, item in enumerate(data.get('vocabulary', []), 1):
                                md_content += f"**{i}. {item['word']}** `{item.get('ipa', '')}`\n* **Def:** {item['definition']}\n* **Ctx:** {item['context']}\n\n"

                            st.markdown(md_content)
                            record = {
                                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "original": source_text,
                                "markdown": md_content
                            }
                            st.session_state.history.insert(0, record)
                            st.toast("✅ Saved to Library!", icon="💾")
                            
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

# === Tab 2: 历史资料库 ===
with tab_library:
    st.markdown("#### 🗂️ Knowledge Base")
    if not st.session_state.history:
        st.info("No records found. Go to 'Deep Analysis' to start.")
    else:
        col_tools, _ = st.columns([1, 4])
        with col_tools:
            if st.button("🗑️ Clear All History", type="secondary"):
                st.session_state.history = []
                st.rerun()
        st.divider()
        selected_records = []
        for i, note in enumerate(st.session_state.history):
            with st.container():
                c_check, c_content = st.columns([0.05, 0.95])
                with c_check:
                    if st.checkbox("", key=f"check_{i}"):
                        selected_records.append(note)
                with c_content:
                    with st.expander(f"📅 {note['time']} - {note['original'][:50]}..."):
                        st.markdown(note['markdown'])
            st.divider()
        if selected_records:
            st.success(f"Selected {len(selected_records)} notes.")
            final_export = f"# DeepRead Study Notes\nGenerated: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
            for note in selected_records:
                final_export += f"## Record: {note['time']}\n{note['markdown']}\n\n========================================\n\n"
            st.download_button(
                label="📥 Download Markdown (Print-Ready)",
                data=final_export,
                file_name=f"DeepRead_Notes_{datetime.datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                type="primary"
            )
