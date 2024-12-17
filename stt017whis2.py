# stt017whis2.py
import os
import wave
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from openai import OpenAI
# from dotenv import load_dotenv
import base64

#api_key = st.secrets["openai"]["api_key"]
#client = OpenAI(api_key=api_key)

## 環境変数でOpenAI APIを使用するパターン
client = OpenAI()

## .envファイルでOpenAI APIを使用するパターン
# .envファイルの内容を読み込む
#load_dotenv()

# 環境変数OPENAI_API_KEYを取得
# openai_api_key = os.environ.get('OPENAI_API_KEY')

# OpenAIクライアントの初期化
# client = OpenAI(api_key=openai_api_key)

def get_recognized_text():
    """
    録音を行い、音声をテキストに変換します。
    """
    st.markdown("""
    <style>
    div.stButton > button {
        background-color: transparent;
        border: none;
        box-shadow: none;
    }
    </style>
    """, unsafe_allow_html=True)

    contents = audio_recorder(
        energy_threshold=(1000000000, 0.0000000002), 
        pause_threshold=0.1, 
        sample_rate=48000,
        text="今日の気持ち、話してみて 👉 ",
        icon_size=500
    )

    if contents is None:
        st.info('①　アイコンボタンを押して回答録音　(アイコンが赤色で録音中)。  \n②　もう一度押して回答終了　(再度アイコンが黒色になれば完了)')
        st.error('録音が終わったら10秒待ってね。')
        st.stop()
    else:
        # 録音した音声を再生
        st.audio(contents)
        
        # 録音データをファイルに保存
        with wave.open("audio.wav", "wb") as audio_file:
            audio_file.setnchannels(2)
            audio_file.setsampwidth(2)
            audio_file.setframerate(48000)
            audio_file.writeframes(contents)
        
        # 音声ファイルをOpenAI Whisperで文字起こし
        with open("audio.wav", "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
            )
        
        recognized_text = transcription.text
        st.success("音声認識できたよ。")
        return recognized_text
