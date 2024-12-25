# dokidoki_diary_proto3.py
import streamlit as st
import requests
from datetime import datetime, timedelta
import os
from openai import OpenAI
from stt017whis2 import get_recognized_text
#from dotenv import load_dotenv
import pandas as pd
import sqlite3
import base64

# OpenAIクライアントの初期化（初期化って何だ？）
api_key = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=api_key)

### 環境変数でOpenAI APIを使用するパターン
#client = OpenAI()

### .envファイルでOpenAI APIを使用するパターン
## .envファイルの内容を読み込む
## load_dotenv()

## 環境変数OPENAI_API_KEYを取得
## openai_api_key = os.environ.get('OPENAI_API_KEY')

## OpenAIクライアントの初期化
## client = OpenAI(api_key=openai_api_key)

############################################
# カスタムCSS（背景全体を画像、文字色白、ボタンの丸角、中央配置など）
############################################

# ２）背景に使いたい画像パスと名前『　back_image.png 』
background_image_path = "images_master/back_image.png"

# ３）TOPに差し込みたい徳井風画像パスと名前『　top_image.png 』
top_image_path = "images_master/top_image.png"

# ４）背景画像の読み込みにBase64を使う
def get_base64_image(image_path):
    """
    画像ファイルをBase64エンコードする関数
    """
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"背景画像の読み込みに失敗しました: {e}")
        return ""

# ５）Base64エンコードされた背景画像
background_base64 = get_base64_image(background_image_path)

# ６）背景画像が正しくエンコードされたか確認
if not background_base64:
    st.stop()  # 背景画像が読み込めない場合、アプリケーションを停止

# ７）以下カスタムCSS

custom_css = f"""
<style>
/* 全体の背景画像を反映 */
html, body, .stApp {{
    background: url("data:image/png;base64,{background_base64}") no-repeat center center fixed;
    background-size: cover;
    color: #FFFFFF !important; /* 全ての文字色を白に */
}}

/* ボタン全体のスタイル */
div.stButton > button {{
    background-color: #FFFFFF !important; /* ボタンの背景色（白） */
    color: #333333 !important;            /* ボタン文字色（ピンク） */
    border-radius: 10px !important;
    text-align: center !important;
    font-weight: nomal !important;
    border: 1px solid #FFFFFF !important;
}}

/* 入力欄や他のテキストも白文字に */
.block-container {{
    color: #FFFFFF !important;
}}

/* タブヘッダーの文字色 */
div[data-testid="stHeader"] {{
    color: #ffffff !important;
}}

/* セレクトボックス等のラベル文字色を白に */
.css-16hu3l7 {{
    color: #ffffff !important;
}}

/* カスタムラベルのスタイル */
.custom-label {{
    font-weight: bold;
    background-color: white;
    color: black;
    padding: 5px 10px;
    border-radius: 5px;
    display: inline-block;
    margin-bottom: 10px;
}}

/* 日付選択（date_input）の背景を白色 */
[data-testid="stDateInput"] input {{
    background-color: #FFFFFF !important;
    color: #333333 !important; /* 文字色は黒っぽく */
}}

/* テキストエリアの背景を白色 */
.stTextArea textarea {{
    background-color: #FFFFFF !important;
    color: #333333 !important; /* 文字色は黒っぽく */
}}

/* セレクトボックスの背景を白色 */
.stSelectbox div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    color: #333333 !important; /* 文字色は黒っぽく */
}}

/* 天気表示のスタイル調整 */
.weather-display {{
    font-size: 0.8em;
    font-weight: normal; /* フォントの太さを通常に設定 */
    line-height: 1.1;
    text-align: left; /* 左揃え */
    color: #333333; /* 濃いグレーに変更 */
}}

/* 吹き出し専用のスタイル */
.feedback-bubble {{
    color: #333333 !important; /* 文字色を濃いグレーに設定 */
    background: #FFFFFF; /* 背景色を白に設定 */
    padding: 10px 15px;
    border-radius: 30px;
    width: 100%; /* 横幅を最大に */
    max-width: 100%; /* 最大横幅を100%に設定 */
    margin-bottom: 20px;
    position: relative;
}}

/* 日記表示用のスタイル */
.diary-bubble {{
    color: #333333 !important; /* 文字色を濃いグレーに設定 */
    background-color: #FFFFFF !important; /* 背景色を白に設定 */
    padding: 10px 15px;
    border-radius: 30px;
    width: 100%; /* 横幅を最大に */
    max-width: 100%; /* 最大横幅を100%に設定 */
    margin-bottom: 10px;
    position: relative;
    
}}

</style>
"""

#　８） カスタムCSSを適用
st.markdown(custom_css, unsafe_allow_html=True)

# ９）画面上部にヘッダー画像（背景とは別）
st.image(top_image_path, use_container_width=True)

###############################
#10) データベース
###############################
# データベースに接続し、dokidoki_diary.dbという名前のDBファイルを作成あるいは開く
conn = sqlite3.connect('dokidoki_diary.db')
#データベースを操作するためのカーソルを作成
c = conn.cursor()

# テーブルの作成（存在しない場合のみ）日付（日付型）、日記とFB（テキスト型）
c.execute('''CREATE TABLE IF NOT EXISTS Diary_table(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date date,
            diary TEXT,
            feedback TEXT)''')

# テーブルに 'user' カラムがない場合はテキスト型で追加
try:
    c.execute("ALTER TABLE Diary_table ADD COLUMN user TEXT")
# カラムがすでに存在する場合、SQLiteはエラーを発生させるが、
except sqlite3.OperationalError:
    # 'user' カラムが既に存在している場合はスキップし、処理を継続
    pass  

#--------------------------------------
#ログイン
#--------------------------------------
# ユーザー認証情報
USERS = {
    "Arichan": "dokidoki",
    "Captain": "dokidoki",
    "Sayapi": "dokidoki",
    "A-chan": "dokidoki"
}


# セッション状態にauthenticatedが存在しない場合、初期値をNoneに設定
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = None

# ユーザーが未ログインの場合
if not st.session_state["authenticated"]:
    # ログインフォーム
    st.markdown('<h2 class="custom-title">ログイン</h2>', unsafe_allow_html=True)
    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")
    
    
    if st.button("ログイン"):
        # 入力されたユーザー名とパスワードが正しいか確認（USERSは事前に定義された辞書型で、ユーザー名とパスワードのペアが格納） 
        if username in USERS and USERS[username] == password:
            # 認証されるとセッション状態にユーザー名を保存し、処理成功を知らせるメッセージを表示
            st.session_state["authenticated"] = username
            st.success(f"Welcome! {username}!")
            # ログイン成功後、アプリのページを再描画
            st.rerun()  
        else:
            st.error("ユーザー名またはパスワードが間違っています")
    # ログイン前の状態では、以降のコードの処理停止
    st.stop()  

# ログイン後の処理
if st.session_state["authenticated"]:

    ##############################
    # 11）メインタブ　日付選択と気分でカラムを２つに
    ##############################
    with st.container():
        col1, col2 = st.columns(2)

        # カラム1: 日付選択
        with col1:
            selected_date = st.date_input("Today is", value=datetime.now().date())

        # カラム2: 気分選択
        with col2:
            options = {
        "癒してほしい": "優しい口調でユーザに共感し、心が軽くなるようなコメントをしてください。具体的なアドバイスはせずに、共感をしつつも、「徳井義実」というキャラの良さが反映されたコメントをしてください。",
        "励ましてほしい": "明るい口調でユーザに共感し、ユーザが前向きになれるような具体的なアドバイスをしてください",
        "喝を入れてほしい": "ユーザの状況や心情に対して、少し毒舌要素のある関西弁のツッコミを入れつつ、力強い言葉でユーザーを奮い立たせるようなコメントをしてください。",
        }
            # Streamlit セレクトボックスで気分を選択
            option = st.selectbox("Select Mode", list(options.keys()), key='select_mode')
        
        
        # ここから天気予報
        # まず delta_days を計算
        delta_days = (selected_date - datetime.now().date()).days

        # 天気用の変数をあらかじめ定義
        weather_today = "未取得"
        weather_tomorrow = "未取得"

        # 天気取得ロジック（delta_daysによって分岐）
        if delta_days < 0 or delta_days > 2:
            # 取得できるのは 今日・明日・明後日まで
            st.warning("このAPIで取得できるのは今日・明日・明後日の天気のみです。")
            st.session_state.weather_info = None
            selected_weather = None
            next_day_converted = None
        else:
            # 天気取得API部分
            city_code = "110010"  # 埼玉(さいたま市)
            url = f"https://weather.tsukumijima.net/api/forecast/city/{city_code}"
            response = requests.get(url)
            if response.status_code == 200:
                weather_json = response.json()
                forecast_data_today = weather_json['forecasts'][delta_days]
                raw_weather_today = forecast_data_today["telop"]

                def convert_weather_text(text):
                    # 天気表記変換
                    text = text.replace("晴", "☀️")
                    text = text.replace("☀️れ","☀️")
                    text = text.replace("はれ☀️れ", "☀️")
                    text = text.replace("曇", "☁️")
                    text = text.replace("くもり☁️り", "☁️")
                    text = text.replace("雨", "☔️")
                    text = text.replace("雪", "⛄️")
                    return text

                # 今日の天気
                weather_today = convert_weather_text(raw_weather_today)
                st.session_state.weather_info = weather_today

                # 明日の天気
                if delta_days < 2:
                    forecast_data_tomorrow = weather_json['forecasts'][delta_days + 1]
                    raw_weather_tomorrow = forecast_data_tomorrow["telop"]
                    weather_tomorrow = convert_weather_text(raw_weather_tomorrow)
                else:
                    weather_tomorrow = "不明"

            else:
                # 天気情報が取得できない場合
                st.error("天気情報の取得に失敗しました。")
                st.session_state.weather_info = None
                weather_today = "-"
                weather_tomorrow = "-"

        # 11）天気表示　２つのカラムの下に表示、今日と明日の天気を１列で表示する設定にしたよ
        st.markdown(
            f'''
            <div style="display:flex; align-items:center; justify-content:left; height:100%;">
                <span class="weather-display" style="margin-right: 20px;">TODAY：{weather_today}</span>
                <span class="weather-display">TOMORROW：{weather_tomorrow}</span>
            </div>
            ''',
            unsafe_allow_html=True)
    ##############################
    # タブ1　フィードバックページ
    ##############################
    tab1, tab2 = st.tabs(["Make a Diary", "Record of Memories"])

    # タブ1（今日の日記ページ）に日記を入力する
    with tab1:

        # 子モジュールから音声認識結果を取得
        recognized_text = get_recognized_text()

        # 日記を入力する欄を入れる。openaiに渡したり、日記内容を反映した画像と合わせて日記を表示するためにdiary_inputに日記内容を代入する。
        diary_input = st.text_area(
            "ちょっと違うところは手で修正してね。", 
            height=150,
            placeholder="",
            value=recognized_text  # 音声認識結果をデフォルト値として設定
        )

        # 送信ボタンを入れる
        submit_btn = st.button("F i n i s h")

        # 送信ボタンが押されると以下の処理が走る
        if submit_btn:
            
            # フィードバックの出力前にフィードバックに使用するプロンプトをそれぞれoptionで指定
                # イメージ画像は直接パスで持ってきている（相対だとうまく反映されなかった※課題）
                personality_prompt = f"""あなたは日本のお笑い芸人チュートリアルの『徳井義実』です。京都府出身で、関西弁口調で話します。"""
                face_image_path = "images_master/tokui.png"
                            
                #選択した気分をプロンプトに反映させる
                mood_prompt = options[option]
                
                # 天気がない場合は '不明' とする
                selected_weather = weather_today if weather_today else '不明'
                
                # ここからはフィードバック自体のプロンプトを指定
                # 日記の要約・天気情報・2名のパーソナルプロンプトからコメントするように指示
                # 天気は必ずしもフィードバックに使用しなくても良いとも補足
                feedback_prompt = f"""
                以下はユーザーの日記内容の要約と、その日の埼玉の天気です。

                - 天気: {selected_weather if selected_weather else '不明'}

                ユーザーは毎日日記を通じて、その日の出来事や気持ちや悩みを示しています。
                あなたの役割は、{personality_prompt}です。
                {diary_input}というユーザーの状況や心情を理解し、{option}ユーザの気分に基づいて、{mood_prompt}

                もし天気 ({selected_weather if selected_weather else '不明'}) の状況がユーザーの気分転換や行動提案に有効に活かせる場合は、天気を考慮したアドバイスを含めてください。
                しかし、天気を考慮しても特にユーザーの役に立たないと判断できる場合は、無理に天気に言及する必要はありません。ただし、天気情報({selected_weather if selected_weather else '不明'})をそのまま使うのではなく「晴れ」「雨」「曇り」などの話し言葉に変更して出力してください。

                ＃制約条件
                - {diary_input}というユーザーの状況や心情に共感してください。
                - 天気を有効活用できそうなアイデアがあれば取り入れてください。なければ天気に関する言及は省いて構いません。
                - {personality_prompt}の口調やキャラ設定を守った状態で回答を生成してください。
                - {option}というユーザの気分をもとに、{mood_prompt}

                以上を踏まえ、ユーザーを励ますコメントを作成してください。
                """

                # フィードバックを生成する
                feedback_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": feedback_prompt}
                    ],
                    temperature=0.7,
                )
                feedback_comment = feedback_response.choices[0].message.content.strip()

                st.markdown("### M e s s a g e")
                # フィードバックを表示する
                # カラムを２分割（左:徳井の画像 右:メッセージ吹き出し）
                left_col, right_col = st.columns([1,3])

                with left_col:
                    st.image(face_image_path, width=100, caption=None)

                with right_col:
                    st.markdown(
                        f"""
                        <div class="feedback-bubble">
                            {feedback_comment}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # DALL-E 3で日記内容を反映したイラストを作成
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"ディズニー風、トイ・ストーリー風のアメリカンモダンなスタイルで、明るくカラフルな色使いと温かみのある雰囲気を持つ、以下の日記内容に基づいたスタイリッシュなイラストを作成してください。\n#text\n{diary_input}",
            size="1792x1024",
            quality="standard",
            n=1,
            ) 

        image_url = response.data[0].url
        st.image(image_url, width=650, use_container_width=False)  # use_container_width=False に設定（幅を固定）
        
        # 日記とFBをDBに格納
        c.execute("INSERT INTO Diary_table (user, date, diary, feedback) VALUES (?, ?, ?, ?)",
                (st.session_state["authenticated"],selected_date ,diary_input ,feedback_comment ))
        conn.commit()
        st.success("日記を保存したよ")
        
        # データベース接続を終了
        conn.close()        

    #＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
    # タブ2: 振り返りページ
    #＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝

    with tab2:
        # データベースファイルパス
        db_path = "dokidoki_diary.db"

        # データベースのテーブル名を指定
        table_name = "Diary_table"
        reflect_date = st.date_input("Check the date you want to remember", value=datetime.now().date())
        one_month_ago = reflect_date - pd.DateOffset(months=1)
        one_year_ago = reflect_date - pd.DateOffset(years=1)

        def get_diary_data(date_obj):
            date_str = date_obj.strftime('%Y-%m-%d')
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute(f"SELECT diary, feedback FROM {table_name} WHERE date = ?", (date_str,))
            row = c.fetchone()
            conn.close()
            if row:
                diary, feedback = row
                return (date_str, diary, feedback)
            else:
                return None
        def display_diary_feedback(label, data_tuple):
            st.markdown(f"#### {label}")
            if data_tuple:
                date_str, diary, feedback = data_tuple
                # 3カラムに分ける
                date_col, diary_col, feedback_col = st.columns([1, 2, 2])
                with date_col:
                    st.markdown(f"**{date_str}**")
                with diary_col:
                    st.markdown("**Diary**")
                    st.markdown(
                        f"""
                        <div class="diary-bubble">
                            {diary}
                        </div>
                        """, unsafe_allow_html=True
                    )
                with feedback_col:
                    st.markdown("**Feedback**")
                    st.markdown(
                        f"""
                        <div class="feedback-bubble">
                            {feedback}
                        </div>
                        """, unsafe_allow_html=True
                    )
            else:
                # データがない場合
                date_col, diary_col, feedback_col = st.columns([1, 2, 2])
                with date_col:
                    st.markdown("**ー**")
                with diary_col:
                    st.markdown("**Diary**")
                    st.markdown("ー")
                with feedback_col:
                    st.markdown("**Feedback**")
                    st.markdown("ー")

        data_current = get_diary_data(reflect_date)
        data_month = get_diary_data(one_month_ago.to_pydatetime())
        data_year = get_diary_data(one_year_ago.to_pydatetime())

    # 表示
        display_diary_feedback("", data_current)

        st.markdown("#### 1ヶ月前")
        display_diary_feedback("", data_month)

        st.markdown("#### 1年前")
        display_diary_feedback("", data_year)
