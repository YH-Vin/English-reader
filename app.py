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
)  # <--- 这里必须闭合！设置结束。

# CSS: 兼容深色模式，修复输入框背景问题
custom_css = """
<style>
    .stApp { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    h1 { font-weight: 700 !important; letter-spacing: -0.03em !important; }
    div.stButton > button { border-radius: 10px !important; font-weight: 600 !important; border: none !important; padding: 0.5rem 1rem !important; transition: transform 0.1s; }
    div.stButton > button:active { transform: scale(0.98); }
    hr { margin: 2em 0 !important; border: none !important; border-top: 1px solid #eaeaea !important; }
    .mobile-alert { background-color: #fff0f0; padding: 12px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 25px; color: #333; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 状态管理与回调函数
# -----------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "user_level" not in st.session_state:
    st.session_state.user_level = "Intermediate (B1-B2)"

# --- 关键修复：清空文本的回调函数 ---
def clear_text():
    # 将输入框绑定的 key 的值设为空
    st.session_state["source_input"] = ""

# -----------------------------------------------------------------------------
# 3. 核心功能函数库
# -----------------------------------------------------------------------------
def get_api_key():
    try:
        if "ALIYUN_API_KEY" in st.secrets:
            return st.secrets["ALIYUN_API_KEY"]
    except FileNotFoundError: pass 
    return None

def generate_save_token(data):
    if not data: return ""
    try:
        json_str = json.dumps(data)
        compressed = zlib.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    except: return ""

def load_save_token(token):
    try:
        decoded = base64.b64decode(token)
        json_str = zlib.decompress(decoded).decode('utf-8')
        return json.loads(json_str)
    except: return None

def analyze_text_pro(client, text, level, model):
    """
    极致优化版分析函数：
    1. 逐句全量解析 (Sentence-by-Sentence Breakdown)
    2. 严格的词汇分级过滤 (Strict Vocabulary Filtering)
    3. 降维释义 (Simplified Definitions)
    """
    
    # 提取等级的核心关键词（例如 "Intermediate"），用于 Prompt 中的强调
    level_keyword = level.split()[0] if level else "Intermediate"

    prompt = f"""
    You are a strict and elite Linguistics Professor and Curriculum Designer. 
    Analyze the provided English text for a student at the CEFR level: {level}.

    Your task is to generate a structured learning guide. You must strictly adhere to the following rules:

    ### RULE 1: EXPLANATION (MANDATORY Sentence-by-Sentence Analysis)
    - You MUST iterate through the text **sentence by sentence**.
    - For **EVERY** sentence in the text, provide a breakdown object.
    - **DO NOT SKIP** any sentence unless it is essentially meaningless (e.g., just "Yes." or "No.").
    - If a sentence is simple, briefly explain its function or connection to the context.
    - If a sentence is complex, deconstruct its logic deeply.
    - **"title"** should be a short concept summary (e.g., "The Opening Argument", "Supporting Detail", "The Conclusion").
    - **"original"** must be the exact sentence from the text.

    ### RULE 2: VOCABULARY (Strict Level Filtering)
    - **SELECTION CRITERIA**: Select words that are **significantly difficult** for a learner at {level}.
    - **NEGATIVE CONSTRAINT**: DO NOT select words that a student at {level} should already know. If the word is common (e.g., "apple", "book", "difficult" for Intermediate), **IGNORE IT**.
    - If there are no words above the user's level, return an empty list for vocabulary. Do not fill it with easy words just to fill space.
    - **Max quantity**: 6 words (but only if they are truly hard).

    ### RULE 3: DEFINITIONS (Comprehensible Input)
    - The **"definition"** and **"context"** for vocabulary must be written using English that is **simpler** than the user's current level ({level}).
    - Do not use complex words to explain other complex words.

    ### OUTPUT FORMAT
    Return a **STRICT JSON** object with the following keys:
    1. "main_idea": Concise summary (2-3 sentences).
    2. "explanation": A list of objects. Each object must represent ONE sentence from the text. Keys: "title", "original", "meaning".
    3. "grammar": List of objects (keys: "title", "original", "breakdown"). Focus on syntax relevant to {level}.
    4. "vocabulary": List of objects (keys: "word", "ipa", "definition", "context").

    Original Text:
    {text}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                # System Prompt 强化人设，确保 AI 处于严格模式
                {"role": "system", "content": f"You are a strict English tutor. You never hallucinate. You prioritize the user's CEFR level ({level_keyword}) above all else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # 极低温度，防止 AI 发散或遗漏，保证逻辑严密
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def analyze_text_stream(client, text, level, model):
    """
    流式分析函数：直接要求 AI 输出 Markdown 格式，不再经过 JSON 解析
    """
    # 提取等级关键词
    level_keyword = level.split()[0] if level else "Intermediate"

    prompt = f"""
    You are a strict and elite Linguistics Professor. Analyze the text for a student at CEFR level: {level}.
    
    ### STRICT OUTPUT RULES
    1. Output **DIRECTLY in Markdown format**. Do not use JSON.
    2. **Sentence-by-Sentence Analysis**: You MUST iterate through the text sentence by sentence. Do not skip any sentence.
    3. **Vocabulary**: Select words significantly difficult for {level}. Definitions must be simpler than the word itself.
    
    ### REQUIRED MARKDOWN STRUCTURE
    Please output exactly in this format:

    ### **Main Idea**
    [Concise summary in 2-3 sentences]

    ---
    ### **Detailed Explanation**
    **1. [Short Concept Title]**
    > *Original: "[The exact sentence]"*
    *   **Meaning:** [Deep analysis of the sentence logic]

    **2. [Next Concept Title]**
    ... (Repeat for EVERY sentence) ...

    ---
    ### **Grammar Breakdown**
    **1. [Grammar Point Title]**
    > *"[Snippet]"*
    *   **Analysis:** [Syntax breakdown]

    ---
    ### **Vocabulary**
    **1. [Word]** `[IPA]`
    *   **Def:** [Simple definition]
    *   **Ctx:** [Context usage]

    Original Text:
    {text}
    """
    
    # 开启 stream=True
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a specialized Linguistics Tutor. Output strictly structured Markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        stream=True  # 关键点：开启流式
    )
    return stream

# -----------------------------------------------------------------------------
# 4. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input("🔑 API Key", type="password", placeholder="Paste Aliyun Key here")
        if not api_key: st.warning("⚠️ 请输入 Key 以使用")
    st.divider()
    st.subheader("👤 User Level")
    st.session_state.user_level = st.selectbox("Select Target Level:", ["Beginner (A1-A2)", "Intermediate (B1-B2)", "Advanced (C1-C2)"], index=1)
    st.divider()
    with st.expander("💾 Backup / Restore", expanded=False):
        st.caption("防止数据丢失，请定期备份")
        if st.session_state.history:
            token = generate_save_token(st.session_state.history)
            st.code(token, language="text")
            st.caption("👆 全选复制，存入备忘录。")
        else: st.info("暂无记录可导出")
        st.markdown("---")
        restore_token = st.text_input("Import Token:", placeholder="Paste token here...", label_visibility="collapsed")
        if st.button("🔄 Restore Data", use_container_width=True):
            data = load_save_token(restore_token)
            if data:
                st.session_state.history = data
                st.toast("✅ 数据恢复成功！", icon="🎉")
                st.rerun()
            else: st.error("无效的存档码")

# -----------------------------------------------------------------------------
# 5. 主界面
# -----------------------------------------------------------------------------

# 获取当前日期
today_str = datetime.datetime.now().strftime("%Y-%m-%d %A")

# 左右布局：左标题，右日期
col_title, col_date = st.columns([3, 1])

with col_title:
    st.title("📘 DeepRead Pro")

with col_date:
    # 右对齐显示日期
    st.markdown(f"<div style='text-align: right; color: gray; padding-top: 25px; font-size: 0.9em;'>📅 {today_str}</div>", unsafe_allow_html=True)

st.caption("Your AI-Powered Linguistics Tutor")


tab_analysis, tab_library = st.tabs(["✨ Deep Analysis", "📚 My Library"])

# === Tab 1: 深度分析 ===
with tab_analysis:
    st.markdown("""<div class="mobile-alert"><strong style='color: #d8000c;'>⚠️ 手机用户请注意：</strong><span style='color: #333;'>请点击左上角 <b>></b> 箭头展开设置，或在浏览器菜单选择<b>“请求桌面网站”</b>以获得最佳体验。</span></div>""", unsafe_allow_html=True)

    col_in, col_out = st.columns([1, 1.1])
    
    with col_in:
        st.markdown("#### Input Text")
        
        # --- 关键修复：添加 key 参数 ---
        source_text = st.text_area(
            "Content", 
            height=350, 
            label_visibility="collapsed",
            key="source_input"  # 给组件一个ID，方便回调函数找到它
        )
        
        c1, c2, c3 = st.columns([1.5, 1, 1])
        with c1:
            model = st.selectbox("Model", ["qwen3-max", "qwen-flash"], label_visibility="collapsed")
        with c2:
            # --- 关键修复：绑定 on_click 回调 ---
            st.button("🗑️ Clear", use_container_width=True, on_click=clear_text)
        with c3:
            analyze_btn = st.button("Analyze 🚀", type="primary", use_container_width=True)

    with col_out:
        st.markdown("#### Insight")
        result_box = st.container()

    # -------------------------------------------------------------------------
    # 替换后的流式输出逻辑
    # -------------------------------------------------------------------------
    if analyze_btn:
        if not api_key:
            st.toast("🚫 Please enter API Key first.", icon="🔒")
        elif not source_text:
            st.toast("✍️ Please paste some text.", icon="📝")
        else:
            with result_box:
                # 1. 准备一个空的容器用来显示流式内容
                placeholder = st.empty()
                full_response = ""
                
                # 2. 开始调用流式函数
                try:
                    client = OpenAI(
                        api_key=api_key, 
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                    )
                    
                    # 调用刚才新写的 stream 函数
                    stream = analyze_text_stream(client, source_text, st.session_state.user_level, model)
                    
                    # 3. 实时循环接收数据并显示
                    for chunk in stream:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_response += content
                            # 实时刷新 UI，加一个光标 ▌ 让它看起来像在打字
                            placeholder.markdown(full_response + "▌")
                    
                    # 4. 生成完毕，移除光标，显示最终结果
                    placeholder.markdown(full_response)
                    
                    # 5. 存入历史记录 (注意：这里直接存 Markdown 字符串)
                    record = {
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "original": source_text,
                        "markdown": full_response  # 直接存生成好的 Markdown
                    }
                    st.session_state.history.insert(0, record)
                    st.toast("✅ Analysis complete & Saved!", icon="💾")

                except Exception as e:
                    st.error(f"Connection Error: {e}")

# === Tab 2: 历史资料库 ===
with tab_library:
    st.markdown("#### 🗂️ Knowledge Base")
    if not st.session_state.history: st.info("No records found.")
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
                    if st.checkbox("", key=f"check_{i}"): selected_records.append(note)
                with c_content:
                    with st.expander(f"📅 {note['time']} - {note['original'][:50]}..."): st.markdown(note['markdown'])
            st.divider()
        if selected_records:
            st.success(f"Selected {len(selected_records)} notes.")
            final_export = f"# DeepRead Study Notes\nGenerated: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
            for note in selected_records: final_export += f"## Record: {note['time']}\n{note['markdown']}\n\n========================================\n\n"
            st.download_button("📥 Download Markdown", final_export, f"DeepRead_Notes_{datetime.datetime.now().strftime('%Y%m%d')}.md", "text/markdown", type="primary")

# --- 底部：固定版权署名 (CSS) ---
st.markdown(
    """
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: transparent; /* 透明背景 */
            color: #888; /* 灰色文字 */
            text-align: center;
            padding: 10px;
            font-size: 12px;
            z-index: 999;
            pointer-events: none; /* 让鼠标可以穿透文字点击下面的按钮 */
        }
    </style>
    <div class="footer">
        Designed by <b>uncompleted vin</b> | Powered by Aliyun Qwen
    </div>
    """, 
    unsafe_allow_html=True
)
