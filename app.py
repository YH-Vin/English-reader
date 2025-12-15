import streamlit as st
from openai import OpenAI

# -----------------------------------------------------------------------------
# 1. 页面配置 (必须放在第一行)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="英语降维阅读器 (通义版)",
    page_icon="📚",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 核心逻辑功能函数
# -----------------------------------------------------------------------------
def get_api_key():
    """
    尝试获取 API Key。
    优先级 1: Streamlit Secrets (最推荐，安全)
    优先级 2: 侧边栏手动输入 (临时用)
    """
    # 尝试从 Secrets 获取
    if "ALIYUN_API_KEY" in st.secrets:
        return st.secrets["ALIYUN_API_KEY"]
    
    # 如果 Secrets 里没有，就在侧边栏显示输入框
    with st.sidebar:
        st.header("⚙️ 设置")
        user_key = st.text_input("未检测到配置，请输入阿里云 API Key", type="password")
        st.info("提示：建议在 Streamlit Secrets 中配置 Key 以免去重复输入。")
        return user_key

# -----------------------------------------------------------------------------
# 3. 界面布局与交互
# -----------------------------------------------------------------------------
st.title("📚 英语降维阅读器 (Qwen驱动)")
st.markdown("把复杂的英语长难句，一键转换为更简单、易读的版本。")

# 获取 Key
api_key = get_api_key()

# 定义难度等级对应的 Prompt
difficulty_map = {
    "小学 (Entry Level)": "Use very simple vocabulary (top 1000 words) and short sentences. Explain strictly for a beginner (CEFR A1-A2).",
    "高中 (Intermediate)": "Use standard vocabulary. Make sentences clear and readable. Avoid overly obscure words (CEFR B1-B2).",
    "大学 (Advanced)": "Retain academic tone but improve clarity, flow, and structure. Keep the original depth (CEFR C1)."
}

# 左右分栏布局
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 原文输入")
    # 文本输入框
    source_text = st.text_area("请粘贴需要降维的英语文本：", height=350, placeholder="Paste your English text here...")
    
    # 选项区
    c1, c2 = st.columns(2)
    with c1:
        selected_difficulty = st.selectbox("🎯 目标难度", list(difficulty_map.keys()))
    with c2:
        # 阿里云模型选择
        model_name = st.selectbox("🤖 选择模型", ["qwen-plus", "qwen-turbo", "qwen-max"], index=0)

    # 提交按钮
    submit = st.button("🚀 开始转换", type="primary", use_container_width=True)

with col2:
    st.subheader("📖 降维结果")
    # 创建一个空的容器，用来动态展示结果
    result_box = st.empty()
    result_box.info("👈 在左侧输入文本并点击转换，结果将显示在这里。")

# -----------------------------------------------------------------------------
# 4. 触发转换逻辑
# -----------------------------------------------------------------------------
if submit:
    if not api_key:
        st.toast("❌ 缺少 API Key！", icon="🚫")
        st.error("请先配置 API Key 才能使用。")
    elif not source_text:
        st.toast("⚠️ 没看到文本呀", icon="😯")
        st.warning("请先在左侧粘贴英语文本。")
    else:
        # 开始调用 API
        result_box.empty() # 清空提示信息
        
        with st.spinner(f"正在请求通义千问 ({model_name})..."):
            try:
                # 初始化客户端 (连接阿里云)
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )

                # 构建指令
                system_prompt = (
                    "You are a professional English simplifier. "
                    "Your GOAL is to rewrite the input text into simpler English based on the user's level. "
                    "RULES: \n"
                    "1. Keep the same meaning. \n"
                    "2. Do NOT translate to Chinese. Output must be English. \n"
                    f"3. Target Level: {difficulty_map[selected_difficulty]}"
                )

                # 发起请求
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": source_text}
                    ],
                    temperature=0.7,
                    stream=True  # 开启流式输出，像打字机一样显示
                )

                #以此接收流式数据
                report = []
                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        report.append(content)
                        # 实时更新右侧显示框
                        result_box.markdown("".join(report))
                
                st.toast("✅ 转换完成！", icon="🎉")

            except Exception as e:
                st.error(f"出错了: {e}")
                st.markdown("### 可能的原因：\n1. API Key 填错了（检查引号、空格）。\n2. 阿里云账户欠费了。\n3. 网络问题。")
