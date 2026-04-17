import streamlit as st
import pdfplumber
import re
import random
import time

# 設定網頁標題
st.set_page_config(page_title="工業配線丙級測驗-正式考試版", layout="centered")

# --- CSS 樣式 ---
st.markdown("""
    <style>
    .stButton > button:disabled {
        color: #000000 !important;
        background-color: #f0f2f6 !important;
        opacity: 1 !important;
        border: 1px solid #d1d5db !important;
    }
    .correct-btn > div > button:disabled {
        border: 2px solid #28a745 !important;
        background-color: #e6ffed !important;
    }
    .wrong-btn > div > button:disabled {
        border: 2px solid #dc3545 !important;
        background-color: #fff5f5 !important;
    }
    div.stButton > button {
        width: 100%;
        height: 3.5em;
        font-size: 18px !important;
        margin-bottom: 5px;
        border-radius: 10px;
    }
    .timer-text {
        font-size: 24px;
        font-weight: bold;
        text-align: right;
        color: #007bff;
    }
    .timer-warn {
        color: #ff4b4b;
    }
    .wrong-q-box {
        padding: 15px;
        border-left: 5px solid #ff4b4b;
        background-color: #fdf2f2;
        margin-bottom: 10px;
        border-radius: 5px;
        color: #000;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_quiz_data(pdf_path):
    quiz_list = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "".join([page.extract_text() + "\n" for page in pdf.pages])
        pattern = re.compile(r'(\d+)\.\s*\((\d)\)\s*(.*?)(?=((?:\d+\.\s*\(\d\))|$))', re.DOTALL)
        matches = pattern.findall(full_text)
        for m in matches:
            content = m[2].strip()
            parts = re.split(r'([①②③④])', content)
            q_text = parts[0].strip()
            opts = [f"{parts[i]}{parts[i+1].strip()}" for i in range(1, len(parts), 2)]
            quiz_list.append({"num": m[0], "question": q_text, "options": opts, "answer": m[1]})
    except:
        return []
    return quiz_list

pdf_file = "工業配線(2)-題庫_copy.pdf"

# 初始化 Session State
if "all_qs" not in st.session_state:
    raw_qs = load_quiz_data(pdf_file)
    random.shuffle(raw_qs)
    st.session_state.all_qs = raw_qs
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.user_answers = {} # 紀錄每一題的選擇 {索引: 選擇的答案}
    st.session_state.end_time = time.time() + 60 * 60 
    st.session_state.is_finished = False

def restart_quiz():
    random.shuffle(st.session_state.all_qs)
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.end_time = time.time() + 60 * 60
    st.session_state.is_finished = False
    st.rerun()

# --- 側邊欄 ---
with st.sidebar:
    st.header("控制台")
    if st.button("🔄 重新洗牌重新開始"):
        restart_quiz()
    st.write(f"目前得分: {st.session_state.score}")

st.title("🎯 工業配線丙級測驗")

# --- 計時邏輯 ---
remaining = st.session_state.end_time - time.time()
if remaining <= 0:
    st.session_state.is_finished = True

# 顯示計時器
if not st.session_state.is_finished:
    mins, secs = divmod(int(remaining), 60)
    timer_placeholder = st.empty()
    timer_class = "timer-warn" if remaining < 600 else ""
    timer_placeholder.markdown(f'<p class="timer-text {timer_class}">⏳ 剩餘時間: {mins:02d}:{secs:02d}</p>', unsafe_allow_html=True)

# --- 主要內容 ---
if st.session_state.all_qs:
    total_qs = len(st.session_state.all_qs)
    
    # 判斷是否顯示結束畫面
    if st.session_state.idx >= total_qs or st.session_state.is_finished:
        st.session_state.is_finished = True # 確保狀態同步
        st.balloons()
        st.header("🎊 測驗結束！")
        if remaining <= 0: st.error("⏰ 時間到！系統已自動交卷")
        
        # 計算最終得分 (再次檢查所有答案)
        final_score = 0
        wrong_and_unanswered = []
        
        for i, q in enumerate(st.session_state.all_qs):
            user_choice = st.session_state.user_answers.get(i)
            if user_choice == q['answer']:
                final_score += 1
            else:
                wrong_and_unanswered.append({
                    "q": q,
                    "user_choice": user_choice
                })
        
        st.metric("最終得分", f"{final_score} / {total_qs}")
        
        if wrong_and_unanswered:
            st.subheader("❌ 錯題與未作答匯總")
            for item in wrong_and_unanswered:
                wq = item['q']
                correct_text = wq['options'][int(wq['answer'])-1]
                user_label = "未作答" if item['user_choice'] is None else wq['options'][int(item['user_choice'])-1]
                
                st.markdown(f"""
                <div class="wrong-q-box">
                    <strong>原題號 Q{wq['num']}</strong>: {wq['question']}<br>
                    <span style="color:red">你的答案: {user_label}</span><br>
                    <span style="color:green">正確答案: {correct_text}</span>
                </div>
                """, unsafe_allow_html=True)
        
        if st.button("🔄 重新挑戰", type="primary"):
            restart_quiz()

    else:
        # --- 答題中介面 ---
        # 快速跳轉選單
        q_labels = [f"第 {i+1} 題 (原:{q['num']})" for i, q in enumerate(st.session_state.all_qs)]
        selected_idx = st.selectbox("快速跳轉至：", range(total_qs), index=st.session_state.idx, format_func=lambda x: q_labels[x])
        if selected_idx != st.session_state.idx:
            st.session_state.idx = selected_idx
            st.rerun()

        q = st.session_state.all_qs[st.session_state.idx]
        current_selection = st.session_state.user_answers.get(st.session_state.idx)
        
        st.write(f"題目進度: {st.session_state.idx + 1} / {total_qs}")
        st.progress((st.session_state.idx + 1) / total_qs)
        st.markdown(f'<p class="question-text">Q{q["num"]}: {q["question"]}</p>', unsafe_allow_html=True)

        for i, opt in enumerate(q['options'], 1):
            is_correct = (str(i) == q['answer'])
            is_selected = (current_selection == str(i))
            
            label = opt
            btn_style = "normal"
            if current_selection:
                if is_correct:
                    label = f"✅ {opt}"
                    btn_style = "correct-btn"
                elif is_selected:
                    label = f"❌ {opt}"
                    btn_style = "wrong-btn"

            with st.container():
                if btn_style != "normal": st.markdown(f'<div class="{btn_style}">', unsafe_allow_html=True)
                if st.button(label, key=f"opt_{st.session_state.idx}_{i}", disabled=(current_selection is not None)):
                    st.session_state.user_answers[st.session_state.idx] = str(i)
                    if str(i) == q['answer']:
                        st.session_state.score += 1
                    st.rerun()
                if btn_style != "normal": st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        col_l, col_r = st.columns([2, 1])
        with col_r:
            if st.button("下一題 ➡️", type="primary"):
                if st.session_state.idx < total_qs - 1:
                    st.session_state.idx += 1
                else:
                    st.session_state.is_finished = True
                st.rerun()
        with col_l:
            if st.button("🏁 提前交卷"):
                st.session_state.is_finished = True
                st.rerun()
else:
    st.error("讀取題庫失敗，請確認 PDF 檔案。")