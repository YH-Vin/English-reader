import streamlit as st
from openai import OpenAI
import json
import datetime

# -----------------------------------------------------------------------------
# 1. 页面与状态配置
# -----------------------------------------------------------------------------
st.set_page_config(page_title="DeepRead - 深度英语降维", page_icon="🧠", layout="wide")

# 初始化 Session State (用于像"内存"一样暂时记住数据)
if "history" not in st.session_state:
    st.session_state.history = []  # 存放所有的阅读记录

if "user_level" not in st.session_state:
    st.session_state.user_level = "Intermediate" # 默认等级

# -----------------------------------------------------------------------------
# 2. 核心功能函数
# -----------------------------------------------------------------------------
def get_api_key():
    # 优先从 Secrets 获取，否则侧边栏输入
    if "ALIYUN_API_KEY" in st.secrets:
        return st.secrets["ALIYUN_API_KEY"]
    return None

def analyze_text(client, text, level, model):
    """
    调用 AI 进行全方位分析：降维 + 语法 + 词汇 + 文化
    要求 AI 返回 JSON 格式以便程序处理
    """
    prompt = f"""
    You are an expert English teacher. Analyze the user's text based on their level: {level}.
    
    Output format: STRICT JSON with the following keys:
    1. "rewritten": The simplified version of the text (keep meaning, lower complexity).
    2. "vocabulary": A list of objects, each containing "word" (from original text), "definition" (English simple definition), and "context" (why it is used here). Max 5 hardest words.
    3. "grammar": A list of strings explaining complex sentence structures found in the original text.
    4. "culture": A string explaining any idioms, cultural references, or tone (if none, return "No special cultural context").
    
    Original Text:
    {text}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "You are a JSON-speaking English tutor."},
                      {"role": "user", "content": prompt}],
            temperature=0.3, # 低温度保证 JSON 格式稳定
            response_format={"type": "json_object"} # 强制 JSON 模式 (如果模型支持)
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 3. 侧边栏：用户画像 (记忆功能)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("👤 学习者档案")
    
    # 获取 API Key (如果没有配置 Secrets，显示输入框)
    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input("🔑 输入阿里云 API Key", type="password")
        if not api_key:
            st.warning("请输入 Key 以开始使用")

    st.divider()
    
    # 设定用户水平 (记忆功能的一部分)
    st.subheader("你的当前水平")
    levels = ["Beginner (小学/初中)", "Intermediate (高中/四级)", "Advanced (六级/考研)", "Native (雅思/托福)"]
    selected_level = st.selectbox("选择水平", levels, index=1)
    st.session_state.user_level = selected_level
    
    st.info(f"🧠 AI 将根据 **{selected_level.split()[0]}** 水平为你定制内容。")

# -----------------------------------------------------------------------------
# 4. 主界面：双 Tab 布局
# -----------------------------------------------------------------------------
st.title("🧠 DeepRead 英语降维学习器")

tab1, tab2 = st.tabs(["📖 深度阅读 & 分析", "🖨️ 资料库 & 导出"])

# === Tab 1: 阅读与分析功能 ===
with tab1:
    col_input, col_output = st.columns([1, 1.2])
    
    with col_input:
        st.subheader("原文输入")
        source_text = st.text_area("粘贴英语长难句...", height=300)
        analyze_btn = st.button("🚀 降维 & 深度分析", type="primary", use_container_width=True)
    
    with col_output:
        st.subheader("学习面板")
        result_container = st.container()

    if analyze_btn and api_key and source_text:
        with result_container:
            with st.spinner("AI 正在拆解语法、查词、重写中..."):
                client = OpenAI(api_key=api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
                
                # 调用核心分析函数
                data = analyze_text(client, source_text, st.session_state.user_level, "qwen-plus")
                
                if "error" in data:
                    st.error(f"分析失败: {data['error']}")
                else:
                    # 1. 展示降维文本
                    st.success("✅ 降维改写")
                    st.markdown(f"**{data['rewritten']}**")
                    
                    # 2. 展示分析 (使用折叠面板保持整洁)
                    with st.expander("🔍 重点词汇 (Vocabulary)", expanded=True):
                        for v in data.get('vocabulary', []):
                            st.markdown(f"- **{v['word']}**: {v['definition']}")
                    
                    with st.expander("📐 语法拆解 (Grammar)"):
                        for g in data.get('grammar', []):
                            st.markdown(f"- {g}")
                            
                    with st.expander("🌍 文化与背景 (Context)"):
                        st.write(data.get('culture', '无特殊背景'))

                    # 3. 存入历史记录 (记忆功能)
                    record = {
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "original": source_text,
                        "rewritten": data['rewritten'],
                        "vocab": data.get('vocabulary', []),
                        "grammar": data.get('grammar', [])
                    }
                    st.session_state.history.insert(0, record) # 插到最前面

# === Tab 2: 汇总与导出功能 ===
with tab2:
    st.header("🗂️ 你的学习资料库")
    
    if not st.session_state.history:
        st.info("还没有记录，快去 Tab 1 进行阅读吧！")
    else:
        # 多选框：选择要打印的内容
        st.write("勾选你想要汇总打印的笔记：")
        
        # 创建一个列表来保存被选中的索引
        selected_indices = []
        
        for i, item in enumerate(st.session_state.history):
            with st.container(border=True):
                # checkbox 的 key 必须唯一
                is_selected = st.checkbox(f"{item['time']} - {item['original'][:30]}...", key=f"hist_{i}")
                if is_selected:
                    selected_indices.append(i)
                
                st.caption(f"降维: {item['rewritten'][:50]}...")

        st.divider()
        
        # 导出逻辑
        if selected_indices:
            st.subheader("📤 导出选项")
            
            # 生成 Markdown 格式的文本 (最适合打印和排版)
            export_text = f"# 英语学习汇总 ({datetime.datetime.now().strftime('%Y-%m-%d')})\n\n"
            for idx in selected_indices:
                note = st.session_state.history[idx]
                export_text += f"## 📅 记录: {note['time']}\n"
                export_text += f"### 1. 原文\n> {note['original']}\n\n"
                export_text += f"### 2. 降维版\n{note['rewritten']}\n\n"
                export_text += f"### 3. 核心词汇\n"
                for v in note['vocab']:
                    export_text += f"- **{v['word']}**: {v['definition']}\n"
                export_text += f"\n### 4. 语法解析\n"
                for g in note['grammar']:
                    export_text += f"- {g}\n"
                export_text += "\n---\n\n"

            # 下载按钮
            st.download_button(
                label="📥 下载 Markdown 讲义 (可直接打印)",
                data=export_text,
                file_name="english_study_notes.md",
                mime="text/markdown"
            )
        else:
            st.caption("请先勾选上面的记录以进行导出。")
