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

# データベースファイルパス
db_path = "dokidoki_diary.db"

# データベースのテーブル名を指定
table_name = "Diary_table"

# サイドバー編集
# サイドバーに日付選択、天気表示、気分選択の３つを追加
with st.sidebar:
    # 日付選択
    selected_date = st.date_input("📍日付を選択してね", value=datetime.now().date())
    today_date = datetime.now().date()
    delta_days = (selected_date - today_date).days

    # 天気取得と表示（取得できるのは３日分のみ）
    if delta_days < 0 or delta_days > 2:
        st.warning("過去の天気は振り返らないようにしてるんよ。ごめんな。")
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
            forecast_data = weather_json['forecasts'][delta_days]
            raw_weather_text = forecast_data["telop"]

            # 天気表記変換関数（重複回避のため定義）→初期出力した時に「晴れ☀️」がいいのに「晴れ☀️れ」のように表示されたので変換するように指定した
            def convert_weather_text(text):
                text = text.replace("晴", "☀️")
                text = text.replace("☀️れ","☀️")
                text = text.replace("はれ☀️れ", "☀️")
                text = text.replace("曇", "☁️")
                text = text.replace("くもり☁️り", "☁️")
                text = text.replace("雨", "☔️")
                text = text.replace("雪", "⛄️")
                return text

            selected_weather = convert_weather_text(raw_weather_text)
            st.session_state.weather_info = selected_weather
            # 今日の天気表示
            st.write(f"**Today：{selected_weather}**")

            # 明日の天気表示
            if delta_days < 2:  # 明日のデータがある場合
                next_day_forecast_data = weather_json['forecasts'][delta_days+1]
                next_day_raw = next_day_forecast_data["telop"]
                next_day_converted = convert_weather_text(next_day_raw)
                st.write(f"**Tomorrow：{next_day_converted}**")
            else:
                next_day_converted = None
        else:
            # 天気情報が取得できない場合の表示
            st.error("天気分からへんな。すまんな。")
            st.session_state.weather_info = None
            selected_weather = None
            next_day_converted = None

    #気分を辞書登録して、気分に応じたプロンプトを設定する
    options = {
    "癒してほしい": "優しい口調でユーザに共感し、心が軽くなるようなコメントをしてください。具体的なアドバイスはせずに、共感をしつつも、「徳井義実」というキャラの良さが反映されたコメントをしてください。",
    "励ましてほしい": "明るい口調でユーザに共感し、ユーザが前向きになれるような具体的なアドバイスをしてください",
    "喝を入れてほしい": "ユーザの状況や心情に対して、少し毒舌要素のある関西弁のツッコミを入れつつ、力強い言葉でユーザーを奮い立たせるようなコメントをしてください。",
    }
    # Streamlit セレクトボックスで気分を選択
    option = st.selectbox(
        "今日はどんな気分？",
        list(options.keys())
    )

# 左上のロゴ（さやさんデザインを仮で使用）
st.image(
    "images_master/team_dokidoki_logo.png",
    use_container_width=True,  # use_column_width を use_container_width に変更
)

# 徳井風のイケメン
st.image("images_master/tokui_ver1.png", use_container_width=True)  # use_column_width を use_container_width に変更

# メイン部分にタブを２つ追加（今日の日記ページと振り返りページ）
tab1, tab2, = st.tabs(["今日の日記をつける", "過去の日記を振り返る"])

# タブ1（今日の日記ページ）に日記を入力する
with tab1:

    # 子モジュールから音声認識結果を取得
    recognized_text = get_recognized_text()

    # 日記を入力する欄を入れる。openaiに渡したり、日記内容を反映した画像と合わせて日記を表示するためにdiary_inputに日記内容を代入する。
    diary_input = st.text_area(
        "日記を入力する", 
        height=150,
        label_visibility="hidden", 
        placeholder="マイクを押して話しかけてね。話し終わったらもう1回マイクを押してね。ちょっと違う部分は手動で編集してね。ごめんね。",
        value=recognized_text  # 音声認識結果をデフォルト値として設定
    )

    # 送信ボタンを入れる
    submit_btn = st.button("日記完了！")

    # 送信ボタンが押されると以下の処理が走る
    if submit_btn:
        
        # フィードバックの出力前にフィードバックに使用するプロンプトをそれぞれoptionで指定
            # イメージ画像は直接パスで持ってきている（相対だとうまく反映されなかった※課題）
            personality_prompt = f"""あなたは日本のお笑い芸人チュートリアルの『徳井義実』です。京都府出身で、関西弁口調で話します。"""
            face_image_path = "images_master/tokui.png"
                        
            #選択した気分をプロンプトに反映させる
            mood_prompt = options[option]
            
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

            st.markdown("### 今日のあなたへのめっせーじ🩷")
            # フィードバックを表示する
            # カラムを２分割（左:徳井の画像 右:メッセージ吹き出し）
            left_col, right_col = st.columns([1,4])

            with left_col:
                st.image(face_image_path, width=100, caption=None)

                with right_col:
                    # 吹き出しスタイルのメッセージ表示
                    st.markdown(
                        f"""
                        <div style="display:inline-block; position:relative; background:#f0f0f0; padding:10px 15px; border-radius:30px; max-width:80%; margin-bottom:20px;">
                            <div style="position:absolute; top:20px; left:-10px; width:0; height:0; 
                                        border-top:10px solid transparent;
                                        border-bottom:10px solid transparent;
                                        border-right:10px solid #f0f0f0;">
                            </div>
                            {feedback_comment} <br>最後に君の1日を絵にしてみたで
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # DALL-E 3で日記内容を反映したイラストを作成
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"Create a stylish illustration based on the following text.\n#text\n{diary_input}",
        size="1792x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    st.image(image_url, width=300, use_container_width=False)  # use_container_width=False に設定（幅を固定）

    # 日記の内容をデータベースに格納
    conn = sqlite3.connect('dokidoki_diary.db')
    cur = conn.cursor()

    data = (1, selected_date, diary_input, feedback_comment)
        
    cur.execute(
        "INSERT INTO Diary_table (user_id, date, diary, feedback) VALUES (?,?,?,?)",
        data
    )

    conn.commit()
    conn.close()


# タブ2: 振り返りページ
with tab2:
    st.markdown("### ふりかえりページ")

    # 日付を指定できるカレンダー
    reflect_date = st.date_input("ふりかえりたい日付を選択してね", value=datetime.now().date())

    # 1ヶ月前、1年前を計算
    one_month_ago = reflect_date - pd.DateOffset(months=1)
    one_year_ago = reflect_date - pd.DateOffset(years=1)

    # 実際のデータベースからデータを取得する関数
    def get_diary_data(date_obj):
        date_str = date_obj.strftime('%Y-%m-%d')# 日付を文字列に変換
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(f"SELECT diary, feedback FROM {table_name} WHERE date = ?", (date_str,))
        row = c.fetchone()
        conn.close()
        if row:
            diary, feedback = row
            # diary, feedbackを返す
            return (date_str, diary, feedback)
        else:
            return None

    def display_diary_row(label, data_tuple):
        st.markdown(f"#### {label}")
        date_col, diary_col, feedback_col = st.columns([1,2,2])
        if data_tuple:
            date_str, diary, feedback = data_tuple
            with date_col:
                st.markdown(f"**{date_str}**")
            with diary_col:
                st.markdown(diary)
            with feedback_col:
                st.markdown(feedback)
        else:
            with date_col:
                st.markdown("日記を書き忘れているよ")
            with diary_col:
                st.markdown("日記を書き忘れているよ")
            with feedback_col:
                st.markdown("日記を書き忘れているよ")

    data_current = get_diary_data(reflect_date)
    data_month = get_diary_data(one_month_ago.to_pydatetime())
    data_year = get_diary_data(one_year_ago.to_pydatetime())

    display_diary_row("指定日付", data_current)
    display_diary_row("1ヶ月前", data_month)
    display_diary_row("1年前", data_year)
