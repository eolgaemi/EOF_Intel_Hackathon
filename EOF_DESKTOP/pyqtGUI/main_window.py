"""
메인 GUI 출력을 담당하는 모듈입니다.
"""
import sys
import configparser
import queue
import time

import cv2
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QTextEdit, QPushButton,QLineEdit

from utils.debugging import current_date, print_err     # 디버깅 용으로 추가
from utils.Comm.launch_control_comm import LaunchControlComm
from utils.Comm.hw_control_comm import HwControlComm
from utils.Inference.bottle_detector import BottleDetector
from utils.Inference.bottle_classifier import BottleClassifier
from utils.Inference.voice_inferencer import VoiceInferencer
from pyqtGUI.threads.rcv_audio_thread import ReceiveAudio
from pyqtGUI.threads.stream_img_thread import StreamImage
# from pyqtGUI.threads.rcv_img_thread import ReceiveImage
from pyqtGUI.threads.ROI_detect_classify_thread import ClassifyTimingChecker
from pyqtGUI.threads.audio_processing_thread import AudioProcessing, TextProcessing


class MainGUI(QMainWindow):
    """메인 GUI에 관한 클래스입니다."""
    config = configparser.ConfigParser()
    config.read("resources/communication_config.ini")

    def __init__(self):
        super().__init__()
        self.on_change_model = False 
        self.frame_queue = queue.Queue(maxsize=30)      # 영상 스트리밍용 queue
        self.launch_control = None                      # 레인 가동 객체
        self.hw_control_comm = None                     # 하드웨어 제어 객체
        self.video_stream_thread = None                 # 영상 수신 thread
        self.audio_recv_thread = None                   # 음성 수신 thread
        self.activated = False                          # 레인 가동 여부
        self.last_detect_time = 0                       # 마지막으로 탐지한 시간
        print(1)
        self.init_basic_instance()
        print(2)
        self.init_ui()

    def init_basic_instance(self):
        """프로그램 동작에 필요한 기본 인스턴스를 초기화 합니다."""
        try:
            self.detector = BottleDetector()                # 페트병 탐지 모델 (위치)
            self.classifier = BottleClassifier()            # 페트병 분류 모델 (LABEL, CLEAR)
            self.voice_inferencer = VoiceInferencer()       # 음성 추론 객체 (음성 명령)

            self.process_client_audio_thread = AudioProcessing(self.voice_inferencer)                   # 음성 처리 thread
            self.process_client_audio_thread.model_change_signal.connect(self.change_model)             # 모델 변경 event
            self.process_client_audio_thread.message_signal.connect(self.send_llama_output)             # 자연어 처리 event
            self.process_textbox_input_thread = TextProcessing(self.voice_inferencer)                   # Llama 추론 thread
            self.process_textbox_input_thread.finished_signal.connect(self.update_log_text)             # Llama 추론 완료 event
            self.classify_timing_check_thread = ClassifyTimingChecker()                                 # 123
            self.classify_timing_check_thread.finished_signal.connect(self.send_classification_result)  # 123

            self.frame_refresh_timer = QTimer(self)
            self.frame_refresh_timer.timeout.connect(self.update_pixmap)
        except Exception as e:
            print_err(f"Failed to initialize basic instances")
            sys.exit(-1)

    def init_ui(self):
        """기본 UI 레이아웃을 생성합니다."""
        try:
            self.setWindowTitle("EOF Trash - Server")

            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)

            self.layout = QVBoxLayout(self.central_widget)

            # 영상 표시 프레임
            self.image_label = QLabel(self)
            pixmap = QPixmap("resources/idle_frame.png")
            self.image_label.setPixmap(pixmap.scaled(640, 480, aspectRatioMode=Qt.KeepAspectRatio))

            # 라인 시작 버튼
            self.lane_start_btn = QPushButton('라인 시작')
            self.lane_start_btn.clicked.connect(self.start_lane)
            # 라인 정지 버튼
            self.lane_stop_btn = QPushButton('라인 정지')
            self.lane_stop_btn.clicked.connect(self.stop_lane)

            # 로그 출력 박스
            self.log_text = QTextEdit(self)
            self.log_text.setReadOnly(True)
            self.log_text.setPlainText("프로그램이 실행되었습니다.")
            self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.log_scrollbar = self.log_text.verticalScrollBar()

            # 명령 입력 박스
            self.user_input_text = QLineEdit(self)
            self.user_input_text.setPlaceholderText("사용자 입력:")
            self.user_input_text.setMaximumHeight(30)
            # 명령 전송 버튼
            self.enter_clicked_btn = QPushButton('전송')
            self.enter_clicked_btn.clicked.connect(self.enter_clicked)
            self.user_input_text.returnPressed.connect(self.enter_clicked_btn.click)

            main_vertical_layout = QVBoxLayout()
            sub_horizontal_layout_1 = QHBoxLayout()
            sub_horizontal_layout_2 = QHBoxLayout()

            sub_horizontal_layout_1.addWidget(self.lane_start_btn)
            sub_horizontal_layout_1.addWidget(self.lane_stop_btn)

            sub_horizontal_layout_2.addWidget(self.user_input_text)
            sub_horizontal_layout_2.addWidget(self.enter_clicked_btn)

            main_vertical_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
            main_vertical_layout.addLayout(sub_horizontal_layout_1)
            main_vertical_layout.addWidget(self.log_text)
            main_vertical_layout.addLayout(sub_horizontal_layout_2)
            self.layout.addLayout(main_vertical_layout)
        except Exception as e:
            print_err("Failed to initialize UI")
            sys.exit(-1)

    def activate_lane(self, str_lane_num):
        """
        레인 객체를 생성하고 실행합니다. (원래는 클래스화가 필요함)
        명령어: /activate {str_lane_num}
        
        Args:
            str_lane_num (str): 실행할 레인 번호
        """
        if self.activated is True:
            added_text = f"{str_lane_num}이 이미 가동중입니다."
            self.update_log_text(added_text)
            return
        
        try:
            # 실행 명령
            self.launch_control = LaunchControlComm(
                self.config["IP"][str_lane_num],
                int(self.config["PORT"]["LAUNCH_CONTROL_PORT"])
            )

            # 하드웨어 제어
            self.hw_control_comm = HwControlComm(
                self.config["IP"][str_lane_num],
                int(self.config["PORT"]["STRING_PORT"])
            )

            # 파이에서 녹음 버튼 명령 수신
            self.audio_recv_thread = ReceiveAudio(
                self.config["IP"]["SERVER"],
                int(self.config["PORT"]["AUDIO_PORT"])
            )
            self.audio_recv_thread.rcv_audio_signal.connect(
                self.process_client_audio_thread.start
            )
            self.audio_recv_thread.start()

            # (사용 안함) 파이에서 이미지 가져오기
            # self.video_stream_thread = ReceiveImage(
            #     self.frame_queue,
            #     self.config["IP"]["SERVER"],
            #     int(self.config["PORT"]["IMAGE_PORT"])
            # )

            # 카메라에서 이미지 가져오기
            self.video_stream_thread = StreamImage(self.frame_queue)
            self.video_stream_thread.start()

            self.frame_refresh_timer.start(30)  # 30ms 마다 콜백 실행 (33 fps)
            self.activated = self.launch_control.activate()
        except Exception as e:
            print_err(f"Failed to activate {str_lane_num}")
            self.deactivate_lane(str_lane_num)

    def deactivate_lane(self, str_lane_num):
        """
        레인 객체를 종료하고 삭제합니다. (원래는 클래스화가 필요함)
        명령어: /deactivate {str_lane_num}
        
        Args:
            str_lane_num (str): 종료할 레인 번호
        """
        if self.activated is False:
            added_text = f"{str_lane_num}은 정지 상태입니다."
            self.update_log_text(added_text)
            return

        try:
            if self.activated is True:
                self.hw_control_comm.send(f"/deactivate {str_lane_num}")  #  /deactivate LANE_1

            del self.launch_control
            del self.hw_control_comm

            if self.video_stream_thread is not None:
                self.video_stream_thread.stop()
                self.video_stream_thread.quit()
                del self.video_stream_thread

            if self.audio_recv_thread is not None:
                self.audio_recv_thread.stop()
                self.audio_recv_thread.quit()
                del self.audio_recv_thread

            if self.frame_queue is not None:
                self.frame_refresh_timer.stop()
                self.frame_queue.queue.clear()

            self.activated = False
        except Exception as e:
            print_err(f"Failed to deactivate {str_lane_num}")

    def update_pixmap(self):
        """메인 GUI의 이미지를 업데이트 합니다."""
        # 이미지 수신 확인
        if not self.frame_queue.empty():
            frame = self.frame_queue.get()

            if not self.on_change_model:  # 모델 스위칭 도중에 프레임 떨어지는 문제 방지
                roi_offset = 100
                roi = frame[roi_offset:480-roi_offset, :]
                (detected, prediction_accuracy, crop_frame_coordinate) \
                    = self.detector.detect_bottle(roi)

                if detected:
                    cv2.rectangle(
                        frame,
                        (crop_frame_coordinate[0], crop_frame_coordinate[1]),
                        (crop_frame_coordinate[2], crop_frame_coordinate[3]),
                        (0, 255, 0), 2
                    )
                    # 트리거
                    if crop_frame_coordinate[2] > 320 and crop_frame_coordinate[2] < 480:
                        if self.classify_timing_check_thread.on_process is False:
                            print("트리거 thread start!!!")
                            self.classify_timing_check_thread.start()
                        else:
                            print("--image 들어가는중")
                            self.classify_timing_check_thread.detection_frame_list.append(
                                (prediction_accuracy,
                                 frame[crop_frame_coordinate[1]:crop_frame_coordinate[3],
                                       crop_frame_coordinate[0]:crop_frame_coordinate[2]])
                            )

            cv2.putText(
                frame, self.detector.current_target, (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 3
            )
            height, width, channels = frame.shape
            bytes_per_line = channels * width
            q_image = QImage(
                frame.data, width, height, bytes_per_line, QImage.Format_BGR888
            )

            if not q_image.isNull():
                pixmap = QPixmap.fromImage(q_image)
                self.image_label.setPixmap(pixmap)
            else:
                print("Invalid image data.")

    def send_classification_result(self, max_accracy_frame):
        """클라이언트로 분류process_client_audio_thread 결과를 전송합니다."""
        result = self.classifier.classify_bottle(max_accracy_frame)     # 분류 결과를 가져옴
        current_time = time.localtime()
        hour = current_time.tm_hour
        minute = current_time.tm_min
        second = current_time.tm_sec

        # Clear Bottle
        if result == 0:
            print("CLEAR BOTTLE 결과 전송")
            added_text = f"분류결과: CLEAR {hour}시 {minute}분 {second}초"
            self.update_log_text(added_text)
        # Label Bottle
        elif result == 1:
            print("LABEL BOTTLE 결과 전송")
            self.hw_control_comm.send(message="Servo Kick")
            added_text = f"분류결과: LABEL {hour}시 {minute}분 {second}초"
            self.update_log_text(added_text)

    def change_model(self):
        """페트병, 유리병 모델을 스위칭 합니다."""
        print("페트병, 유리병 모델을 스위칭 합니다")
        self.on_change_model = True

        current_time = time.localtime()
        hour = current_time.tm_hour
        minute = current_time.tm_min
        second = current_time.tm_sec

        if self.detector.current_target == "pet" \
                and self.classifier.current_target == "pet":
            self.detector.set_model_target("glass")
            self.classifier.set_model_target("glass")
            added_text = f"모델 변경: 페트병->유리병 {hour}시 {minute}분 {second}초"
            self.update_log_text(added_text)
        elif self.detector.current_target == "glass" \
                and self.classifier.current_target == "glass":
            self.detector.set_model_target("pet")
            self.classifier.set_model_target("pet")
            added_text = f"모델 변경: 유리병->페트병 {hour}시 {minute}분 {second}초"
            self.update_log_text(added_text)

        print(f"현재 detector의 target = {self.detector.current_target}")
        print(f"현재 classifier target = {self.classifier.current_target}")

        self.hw_control_comm.send(f"{self.detector.current_target}")
        self.on_change_model = False

    def send_llama_output(self, message):
        """llama2의 추론 결과를 클라이언트로 전송합니다."""
        print("text를 클라이언트로 전송합니다.")
        self.hw_control_comm.send(f'@{message}')

    def start_lane(self):
        """라인을 가동합니다."""
        # 라즈베리 파이로 명령 전달
        self.hw_control_comm.send(message="RC Start")

        # 로그 창에 텍스트 추가
        current_time = time.localtime()
        hour = current_time.tm_hour
        minute = current_time.tm_min
        second = current_time.tm_sec
        added_text = f"라인을 가동합니다. {hour}시 {minute}분 {second}초"
        self.update_log_text(added_text)

        self.last_detect_time = time.time()

    def stop_lane(self):
        """라인을 중지합니다."""
        self.hw_control_comm.send(message="RC Stop")

        current_time = time.localtime()
        hour = current_time.tm_hour
        minute = current_time.tm_min
        second = current_time.tm_sec
        added_text = f"라인을 중지합니다. {hour}시 {minute}분 {second}초"
        self.update_log_text(added_text)

    def enter_clicked(self):
        """사용자 입력 전송버튼이 눌렸을 때의 동작입니다."""
        entered_text = self.user_input_text.text()

        display_text = "- 사용자 입력: " + entered_text
        self.update_log_text(display_text)
        self.user_input_text.setText("")

        # 명령어 입력인 경우
        if entered_text.startswith("/"):
            if entered_text == "/activate LANE_1":
                self.activate_lane("LANE_1")
            elif entered_text == "/deactivate LANE_1":
                self.deactivate_lane("LANE_1")
                pixmap = QPixmap("resources/idle_frame.png")
                self.image_label.setPixmap(
                    pixmap.scaled(640, 480, aspectRatioMode=Qt.KeepAspectRatio)
                )
            elif entered_text == "/change model":
                self.change_model()
            elif entered_text == "/clear":
                self.log_text.setPlainText("프로그램이 실행되었습니다.")
        # 자연어 입력인 경우
        else:
            self.process_textbox_input_thread.target_text = entered_text
            self.process_textbox_input_thread.start()

    def update_log_text(self, added_text):
        """
        로그를 추가합니다.

        텍스트 에디터에 새로운 텍스트를 추가하고, 
        수직 스크롤바를 아래로 이동하여 가장 최근에 추가된 텍스트가 보이도록 합니다.
        """
        log = self.log_text.toPlainText() + "\n" + added_text
        self.log_text.setPlainText(log)
        self.log_scrollbar.setValue(self.log_scrollbar.maximum())

    def close_event(self, event):
        """어플리케이션이 종료될 때 실행중인 스레드를 종료합니다."""
        self.process_client_audio_thread.terminate()
        self.process_client_audio_thread.wait()
        self.classify_timing_check_thread.terminate()
        self.classify_timing_check_thread.wait()
        self.video_stream_thread.terminate()
        self.video_stream_thread.wait()
        self.audio_recv_thread.terminate()
        self.audio_recv_thread.wait()
        event.accept()
