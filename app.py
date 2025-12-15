import streamlit as st
from openai import OpenAI

# 1. 页面基础设置
st.set_page_config(
    page_title="英语降维阅读器",
    layout="wide"  # 设置为宽屏模式，方便左右分栏显示
)

# 2. 侧边栏：配置 API Key
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("请输入 OpenAI API Key", type="password")
    st.markdown("[获取 API Key](https://platform.openai.com/account/api-keys)")
    
    st.write("---")
    st.write("💡 **说明**：此工具旨在将复杂的英语长难句，根据所选等级改写为更简单的英语，辅助学习。")

# 3. 主页面标题
st.title("📚 英语降维阅读器")

# 4. 定义难度对应的提示词 (Prompt)
# 这里是核心逻辑：告诉 AI 如何“降维”
difficulty_map = {
    "小学 (Entry Level)": "Use very simple vocabulary and short sentences (CEFR A1-A2 level). Explain complex concepts simply.",
    "高中 (Intermediate)": "Use standard vocabulary and grammar (CEFR B1-B2 level). Make the text clear and readable.",
    "大学 (Advanced)": "Retain academic tone but improve clarity and flow (CEFR C1 level). Maintain the original depth."
}

# 5. 布局：创建左右两列
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 输入原文本")
    # 文本输入框，高度设置高一点方便粘贴长文
    source_text = st.text_area("请粘贴英语文本：", height=300)
    
    # 难度选择下拉菜单
    selected_difficulty = st.selectbox("选择目标难度", list(difficulty_map.keys()))
    
    # 转换按钮
    convert_btn = st.button("🚀 开始转换", type="primary")

with col2:
    st.subheader("📖 降维后的文本")
    # 用于显示结果的占位符
    result_container = st.empty()

# 6. 按钮点击后的逻辑
if convert_btn:
    if not api_key:
        st.error("❌ 请先在侧边栏输入 OpenAI API Key")
    elif not source_text:
        st.warning("⚠️ 请先输入需要转换的文本")
    else:
        # 显示加载状态
        with st.spinner("AI 正在重写文本，请稍候..."):
            try:
                # 初始化 OpenAI 客户端
                client = OpenAI(api_key=api_key)
                
                # 构建 Prompt
                system_instruction = (
                    "You are a helpful English reading assistant. "
                    "Your task is to rewrite the provided English text into simpler English. "
                    "Do NOT translate it into Chinese. Keep the result in English. "
                    f"Target Level Instruction: {difficulty_map[selected_difficulty]}"
                )

                # 调用接口
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # 或者 gpt-4
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": source_text}
                    ],
                    temperature=0.7
                )

                # 获取结果
                rewritten_text = response.choices[0].message.content

                # 在右侧显示结果
                result_container.success("转换成功！")
                with col2:
                    st.text_area(label="结果", value=rewritten_text, height=300)

            except Exception as e:
                st.error(f"发生错误: {e}")
