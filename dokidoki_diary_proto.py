import streamlit as st
import datetime

# 左上のロゴ（さやさんデザインを仮で使用）
st.logo(
    "images_master/team_dokidoki_logo.png",
)

# 徳井風のイケメン（DALL-E3作※2回作ったら1日分のトークンが無くなった）
st.image("images_master/tokui_ver1.png") #,caption="Team DokiDoki")

# 小さい列と大きい列を作成
question_col, date_col = st.columns([25, 5])  # [25, 5]は列の比率

# question列に日記記入を促す文を入れる
with question_col:
    st.markdown('<div style="font-size: 24px; text-align: center;">お疲れ様。今日はどんな1日だった？</div>', unsafe_allow_html=True)

# date列に日付入力欄を入れる
with date_col:
    date = st.date_input("")

# 日記を入力する欄を入れる。openaiに渡したり、日記内容を反映した画像と合わせて日記を表示するためにdiary_inputに日記内容を代入する。
# CSSスタイルを定義
st.markdown("""
<style>
.stTextArea [data-baseweb=base-input] {
    background-color: #ffffff;  # ここで希望の色を指定
}
</style>
""", unsafe_allow_html=True)

# テキストエリアを表示
diary_input = st.text_area("日記を入力する", height=150, label_visibility="hidden", placeholder="マイクに話しかけてね。ちょっと違う部分は手動で編集してね。ごめんね。")
# 送信ボタンを入れる
submit_btn = st.button("送信")

#送信ボタンが押されると以下の処理が走る
if submit_btn:
    # 列を2つに分割する
    col1, col2 = st.columns(2)

    # 左の列には絵日記を表示。imageのところにopenaiで生成した画像を渡す（やり方のイメージがまだついてない）。
    with col1:
        image = "images_master/diary_picture_example.png"
        st.image(image, width=300)

    # 右の列には日記とフィードバックを表示
    with col2:
        st.write("Your Diary")
        # 文章を枠で囲う処理を入れています。
        st.markdown("""                    
                    <div style="background-color: #F0F2F6; padding: 15px; border-radius: 5px;">
                        diary_input+"（日記に入力した内容がそのまま表示される）"
                    </div>
                    """, unsafe_allow_html=True)

        st.write("Feedback from Tokui")
        feedback = "フィードバック（Openai APIで生成したフィードバックをここに格納する）"
        st.markdown("""                    
                    <div style="background-color: #F0F2F6; padding: 15px; border-radius: 5px;">
                        フィードバックが表示される
                    </div>
                    """, unsafe_allow_html=True)