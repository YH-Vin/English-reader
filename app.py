import streamlit as st
from openai import OpenAI
import json
import datetime
import base64
import zlib

# -----------------------------------------------------------------------------
# 1. 页面与视觉配置 (必须放在代码第一行)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DeepRead Pro",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 极简主义 CSS 注入 ---
custom_css = """
<style>
    /* 全局字体优化 - 类似 Apple/Notion 风格 */
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
        color: #1a1a1a !important;
    }

    /* 文本输入框美化 - 柔和背景与边框 */
    .stTextArea textarea {
        background-color: #f7f9fb !important;
        border: 1px solid #e1e4e8 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: none !important;
        transition: all 0.2s ease;
    }
    .stTextArea textarea:focus {
        border-color: #4dabf7 !important;
        background-color: #ffffff !important;
        box-shadow: 0 0 0 3px rgba(77, 171, 247, 0.1) !important;
    }

    /* 按钮样式 - 扁平化 */
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
    
    /* 结果展示区的分割线 */
    hr {
        margin: 2em 0 !important;
        border: none !important;
        border-top: 1px solid #eaeaea !important;
    }
    
    /* Toast 消息样式微调 */
    .stToast {
        border-radius: 10px !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 状态管理 (Session State)
# -----------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "user_level" not in st.session_state:
    st.session_state.user_level = "Intermediate (B1-B2)"

# -----------------------------------------------------------------------------
# 3. 核心功能函数库
# -----------------------------------------------------------------------------

def get_api_key():
    """优先从 Secrets 获取 Key，否则返回 None"""
    try:
        if "ALIYUN_API_KEY" in st.secrets:
            return st.secrets["ALIYUN_API_KEY"]
    except FileNotFoundError:
        pass # 本地运行且无 secrets.toml 时忽略
    return None

# --- 存档/读档黑科技 ---
def generate_save_token(data):
    """将历史数据压缩并编码为 Base64 字符串"""
    if not data: return ""
    try:
        json_str = json.dumps(data)
        compressed = zlib.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    except Exception as e:
        st.error(f"Backup Error: {e}")
        return ""

def load_save_token(token):
    """解码 Base64 并解压恢复数据"""
    try:
        decoded = base64.b64decode(token)
        json_str = zlib.decompress(decoded).decode('utf-8')
        return json.loads(json_str)
    except Exception:
        return None

# --- AI 分析核心 ---
def analyze_text_pro(client, text, level, model):
    """调用 API 进行深度分析，强制 JSON 输出"""
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
            temperature=0.2, # 低温度保证 JSON 格式稳定
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "AI 返回格式异常，请重试。"}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 4. 侧边栏 (设置 & 备份)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 1. API Key 处理
    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input("🔑 API Key", type="password", placeholder="Paste Aliyun Key here")
        if not api_key:
            st.warning("⚠️ 请输入 Key 以使用")
    
    st.divider()
    
    # 2. 难度选择
    st.subheader("👤 User Level")
    st.session_state.user_level = st.selectbox(
        "Select Target Level:",
        ["Beginner (A1-A2)", "Intermediate (B1-B2)", "Advanced (C1-C2)"],
        index=1
    )
    
    st.divider()
    
    # 3. 备份/恢复系统
    with st.expander("💾 Backup / Restore", expanded=False):
        st.caption("防止数据丢失，请定期备份")
        
        # 导出
        if st.session_state.history:
            token = generate_save_token(st.session_state.history)
            st.markdown("**Export Token:**")
            st.code(token, language="text")
            st.caption("👆 全选复制，存入备忘录。")
        else:
            st.info("暂无记录可导出")
            
        st.markdown("---")
        
        # 导入
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
# 5. 主界面 (Tabs)
# -----------------------------------------------------------------------------
st.title("📘 DeepRead Pro")
st.caption("Your AI-Powered Linguistics Tutor")

tab_analysis, tab_library = st.tabs(["✨ Deep Analysis", "📚 My Library"])

# === Tab 1: 深度分析 ===
with tab_analysis:
    # --- 📱 手机端提示 (红色醒目横幅) ---
    st.markdown(
        """
        <div style='background-color: #fff0f0; padding: 12px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 25px;'>
            <strong style='color: #d8000c;'>⚠️ 手机用户请注意：</strong>
            <span style='color: #333; font-size: 0.95em;'>请点击左上角 <b>></b> 箭头展开设置，或在浏览器菜单选择<b>“请求桌面网站”</b>以获得最佳体验。</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    # ----------------------------------

    col_in, col_out = st.columns([1, 1.1])
    
    with col_in:
        st.markdown("#### Input Text")
        source_text = st.text_area(
            "Content", 
            height=350, 
            placeholder="Paste English text here (e.g. from The Economist, NYT)...",
            label_visibility="collapsed"
        )
        
        # 底部操作栏
        c1, c2, c3 = st.columns([1.5, 1, 1])
        with c1:
            model = st.selectbox("Model", ["qwen-plus", "qwen-max"], label_visibility="collapsed")
        with c2:
            # 清空按钮
            if st.button("🗑️ Clear", use_container_width=True):
                # 这是一个简易清空方式，需配合 st.rerun() 或者是让用户手动删
                pass 
        with c3:
            analyze_btn = st.button("Analyze 🚀", type="primary", use_container_width=True)

    with col_out:
        st.markdown("#### Insight")
        result_box = st.container()

    # 触发逻辑
    if analyze_btn:
        if not api_key:
            st.toast("🚫 Please enter API Key first.", icon="🔒")
        elif not source_text:
            st.toast("✍️ Please paste some text.", icon="📝")
        else:
            with result_box:
                with st.spinner("Analyzing structure, grammar, and context..."):
                    # 初始化客户端
                    try:
                        client = OpenAI(
                            api_key=api_key, 
                            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                        )
                        
                        # 执行分析
                        data = analyze_text_pro(client, source_text, st.session_state.user_level, model)
                        
                        if "error" in data:
                            st.error(f"Analysis Failed: {data['error']}")
                        else:
                            # -----------------------------------------------
                            # 构建 Markdown 输出 (教科书风格)
                            # -----------------------------------------------
                            md_content = f"### **Main Idea**\n{data.get('main_idea', 'No summary available.')}\n\n"
                            
                            md_content += "---\n### **Detailed Explanation**\n\n"
                            for i, item in enumerate(data.get('explanation', []), 1):
                                md_content += f"**{i}. {item['title']}**\n"
                                md_content += f"> *Original: \"{item['original']}\"*\n\n"
                                md_content += f"*   **Meaning:** {item['meaning']}\n\n"
                            
                            md_content += "---\n### **Grammar Breakdown**\n\n"
                            for i, item in enumerate(data.get('grammar', []), 1):
                                md_content += f"**{i}. {item['title']}**\n"
                                md_content += f"> *\"{item['original']}\"*\n\n"
                                md_content += f"*   **Analysis:** {item['breakdown']}\n\n"
                                
                            md_content += "---\n### **Vocabulary**\n\n"
                            for i, item in enumerate(data.get('vocabulary', []), 1):
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
                            st.toast("✅ Saved to Library!", icon="💾")
                            
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

# === Tab 2: 历史资料库 ===
with tab_library:
    st.markdown("#### 🗂️ Knowledge Base")
    
    if not st.session_state.history:
        st.info("No records found. Go to 'Deep Analysis' to start.")
    else:
        # 工具栏
        col_tools, _ = st.columns([1, 4])
        with col_tools:
            if st.button("🗑️ Clear All History", type="secondary"):
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
