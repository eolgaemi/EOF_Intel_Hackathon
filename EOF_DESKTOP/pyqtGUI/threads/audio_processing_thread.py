"""
오디오 파일을 전처리 하는 모듈입니다.
"""
from PyQt5.QtCore import QThread, pyqtSignal
import pygame
from gtts import gTTS


class AudioProcessing(QThread):
    """녹음된 음성 명령 파일을 전처리한 후 수행할 동작을 결정하는 쓰레드입니다."""
    model_change_signal = pyqtSignal()                  # 모델 변경 신호
    message_signal = pyqtSignal(str)                    # 자연어 처리 신호

    AUDIO_FILE_PATH = "resources/recorded_voice.wav"    # 음성 파일 경로
    model_change_keywords = ["change", "model"]         # 모델 변경에 사용할 키워드

    def __init__(self, voice_inferencer):
        super().__init__()
        self.voice_inferencer = voice_inferencer

    def run(self):
        """음성 파일의 내용을 바탕으로 동작을 결정합니다."""
        # Speech To Text
        stt = self.voice_inferencer.get_stt(self.AUDIO_FILE_PATH)
        print(f"Input speech: {stt}")

        # 키워드 단어가 포함되어 있는지 확인
        cnt = 0
        for keyword in self.model_change_keywords:
            if stt.find(keyword) != -1:
                cnt += 1

        # model과 change가 모두 포함되어 있을 경우 모델 변경
        model_change_flag = True if cnt == \
            len(self.model_change_keywords) else False

        # 동작 결정
        if model_change_flag:
            self.model_change_signal.emit()
        else:
            answer = self.voice_inferencer.get_llama2_answer(stt)
            print("Llama answer:", answer)
            self.message_signal.emit(answer)
            self.speak(answer)
        
    def speak(self, text):
        """서버로부터 받은 문자열을 TTS하여 스피커로 출력합니다."""
        # print("받은 문자", text)
        tts = gTTS(text=text, lang="ko")
        tts.save("resources/text_to_speech.mp3")

        pygame.mixer.init()
        pygame.mixer.music.load("resources/text_to_speech.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


class TextProcessing(QThread):
    """whisper가 생성한 텍스트를 가지고 llama2 모델에 추론합니다."""
    finished_signal = pyqtSignal(str)

    def __init__(self, voice_inferencer):
        super().__init__()
        self.voice_inferencer = voice_inferencer
        self.target_text = None

    def run(self):
        """whisper가 생성한 텍스트를 가지고 llama2 모델에 추론합니다."""
        answer = self.voice_inferencer.get_llama2_answer(self.target_text)
        self.finished_signal.emit(answer)
