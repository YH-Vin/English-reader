import streamlit as st
from openai import OpenAI

# 1. 页面基础设置
st.set_page_config(page_title="英语降维阅读器 (通义版)", layout="wide")

# 2. 获取 API Key
# 优先从 Secrets 获取，如果没有则显示侧边栏输入框
try:
    api_key = st.secrets["ALIYUN_API_KEY"]
    using_secrets = True
except:
    using_secrets = False
    with st.sidebar:
        st.header("⚙️ 设置")
        api_key = st.text_input("请输入阿里云 API Key", type="password")
        st.markdown("[获取阿里云 Key](https://dashscope.console.aliyun.com/apiKey)")

# 3. 主页面标题
st.title("📚 英语降维阅读器 (Qwen驱动)")

# 4. 定义难度提示词
difficulty_map = {
    "小学 (Entry Level)": "Use very simple vocabulary and short sentences (CEFR A1-A2 level). Explain complex concepts simply.",
    "高中 (Intermediate)": "Use standard vocabulary and grammar (CEFR B1-B2 level). Make the text clear and readable.",
    "大学 (Advanced)": "Retain academic tone but improve clarity and flow (CEFR C1 level). Maintain the original depth."
}

# 5. 布局
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 输入原文本")
    source_text = st.text_area("请粘贴英语文本：", height=300)
    selected_difficulty = st.selectbox("选择目标难度", list(difficulty_map.keys()))
    
    # 增加一个模型选择（可选）
    model_choice = st.selectbox("选择模型", ["qwen-plus", "qwen-turbo", "qwen-max"], index=0)
    st.caption("💡 推荐使用 qwen-plus，速度与效果最平衡")
    
    convert_btn = st.button("🚀 开始转换", type="primary")

with col2:
    st.subheader("📖 降维后的文本")
    result_container = st.empty()

# 6. 核心逻辑
if convert_btn:
    if not api_key:
        st.error("❌ 未检测到 API Key！请在侧边栏输入或配置 Secrets。")
    elif not source_text:
        st.warning("⚠️ 请先输入需要转换的文本")
    else:
        with st.spinner(f"通义千问 ({model_choice}) 正在重写文本..."):
            try:
                # --- 关键修改点 ---
                # 初始化客户端时，指定阿里云的 Base URL
                client = OpenAI(
                    api_key=api_key, 
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                
                system_instruction = (
                    "You are a helpful English reading assistant. "
                    "Your task is to rewrite the provided English text into simpler English. "
                    "Do NOT translate it into Chinese. Keep the result in English. "
                    f"Target Level Instruction: {difficulty_map[selected_difficulty]}"
                )

                response = client.chat.completions.create(
                    model=model_choice,  # 这里使用了阿里云的模型名
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": source_text}
                    ],
                    temperature=0.7
                )

                rewritten_text = response.choices[0].message.content
                result_container.success("转换成功！")
                with col2:
                    st.text_area(label="结果", value=rewritten_text, height=300)

            except Exception as e:
                st.error(f"发生错误: {e}")
                st.info("💡 常见原因：API Key 无效、余额不足或网络波动。")
