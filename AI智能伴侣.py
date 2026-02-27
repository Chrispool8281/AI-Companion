import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json
from streamlit import session_state

st.set_page_config(
    page_title="AI智能伴侣（劈哥作品）",
    page_icon="🫦",
    #布局
    layout="wide",
    initial_sidebar_state="expanded",
)

#生成会话标识函数
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#保存会话信息函数
def save_session():
    if st.session_state.current_session:
        session_data = {
            "nickname": st.session_state.nickname,
            "character": st.session_state.character,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }

        # 如果sessions目录不存在，则创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        # 保存会话信息
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

#加载会话列表信息函数
def load_sessions():
    session_list = []
    #加载sessions目录下的文件
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list

#加载指定会话信息函数
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nickname = session_data["nickname"]
                st.session_state.character = session_data["character"]
                st.session_state.current_session = session_name
    except Exception as e:
        st.error("加载会话失败!", icon="🚨")

#删除会话信息函数
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            #如果删除的是当前会话，则更新消息列表
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception:
        st.error("删除会话失败!", icon="🚨")

#大标题
st.title("AI智能伴侣")

#Logo
st.logo("resources/logo.png")

#系统提示词
system_prompt = """
        你叫%s，现在是用户的真实伴侣，请完全代入伴侣角色。：
        规则：
            1. 每次只回1条消息
            2. 禁止任何场景或状态描述性文字
            3. 匹配用户的语言
            4. 回复简短，像微信聊天一样
            5. 有需要的话可以用❤️🌸等emoji表情
            6. 用符合伴侣性格的方式对话
            7. 回复的内容, 要充分体现伴侣的性格特征
        伴侣性格：
            - %s
        你必须严格遵守上述规则来回复用户。
    """

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")

#初始化聊天信息
if 'messages' not in st.session_state:
    st.session_state.messages = []
#昵称
if 'nickname' not in st.session_state:
    st.session_state.nickname = "思妮"
#性格
if 'character' not in st.session_state:
    st.session_state.character = "温柔可爱的台湾妹子"

if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

#展示聊天信息
st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

#左侧的侧边栏
with (st.sidebar):
    #会话信息
    st.subheader("AI控制面板")

    #新建会话
    if st.button("新建会话", width="stretch" ,icon="🕶️"):
        #保存当前会话信息
        save_session()

        #创建新的会话
        if st.session_state.messages:
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()

    #会话历史
    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(session, width="stretch", icon="📄", key=f"load_{session}", type="primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("", width="stretch", icon="❌️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    #分割线
    st.divider()

    #伴侣信息
    st.subheader("伴侣信息")
    #昵称输入框
    nickname = st.text_input("昵称", placeholder="请输入伴侣昵称", value=st.session_state.nickname)
    if nickname:
        st.session_state.nickname = nickname
    #性格输入框
    character = st.text_area("性格", placeholder="请输入伴侣性格", value=st.session_state.character)
    if character:
        st.session_state.character = character

#输入框
prompt = st.chat_input("请输入信息...")
if prompt:
    st.chat_message("user").write(prompt)
    #保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    #调用AI大模型
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nickname, st.session_state.character)},
            *st.session_state.messages
        ],
        stream=True
    )

    #输出大模型返回的结果(流式输出)
    response_message = st.empty() #创建一个空的组件,用于显示大模型返回的结果
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    #保存大模型返回的结果
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    #保存会话信息
    save_session()