import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QGridLayout,
                             QRadioButton, QButtonGroup, QProgressBar, QStyle, QShortcut,
                             QFrame)
from PyQt5.QtGui import QImage, QPixmap, QIcon, QKeySequence, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize


class CustomProgressBar(QProgressBar):
    # 사용자 정의 클릭 이벤트 처리를 위한 프로그레스바
    clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setMinimumHeight(12)
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 4px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            value = int((event.x() / self.width()) * self.maximum())
            self.clicked.emit(value)

        super().mousePressEvent(event)


class VideoSyncPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("리링크 체킹 프로그램")
        self.setGeometry(100, 100, 1400, 800)  # GUI 크기 확대

        # 비디오 캡처 객체
        self.cap1 = None
        self.cap2 = None

        # 비디오 속성
        self.fps1 = 0
        self.fps2 = 0
        self.total_frames1 = 0
        self.total_frames2 = 0
        self.current_frame1 = 0
        self.current_frame2 = 0
        self.duration1 = 0  # 초 단위 동영상 길이
        self.duration2 = 0
        self.video_width1 = 0
        self.video_height1 = 0
        self.video_width2 = 0
        self.video_height2 = 0
        self.video_name1 = ""
        self.video_name2 = ""

        # 재생 상태
        self.is_playing = False

        # 이동 옵션 (기본값: 초 단위)
        self.navigation_mode = "seconds"

        # UI 설정
        self.init_ui()

        # 키보드 단축키 설정
        self.setup_shortcuts()

    def init_ui(self):
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)

        # 비디오 표시 레이아웃
        video_layout = QHBoxLayout()

        # 비디오 1 프레임 및 정보
        video1_container = QVBoxLayout()

        # 비디오 1 타이틀
        self.video1_title = QLabel("비디오 1")
        self.video1_title.setAlignment(Qt.AlignCenter)
        self.video1_title.setFont(QFont("Arial", 11, QFont.Bold))
        video1_container.addWidget(self.video1_title)

        # 비디오 1 프레임
        self.video_label1 = QLabel("비디오 1 파일을 선택하세요")
        self.video_label1.setAlignment(Qt.AlignCenter)
        self.video_label1.setMinimumSize(600, 400)  # 크기 확대
        self.video_label1.setStyleSheet("border: 1px solid #ccc; background-color: #222;")
        video1_container.addWidget(self.video_label1)

        # 비디오 1 타임라인
        self.progress1 = CustomProgressBar()
        self.progress1.setMaximum(100)
        self.progress1.clicked.connect(self.progress_bar_clicked)
        video1_container.addWidget(self.progress1)

        # 비디오 1 정보 레이블
        self.video1_info = QLabel("해상도: - x - | FPS: -")
        self.video1_info.setAlignment(Qt.AlignCenter)
        self.video1_info.setStyleSheet("color: #666;")
        video1_container.addWidget(self.video1_info)

        # 비디오 2 프레임 및 정보
        video2_container = QVBoxLayout()

        # 비디오 2 타이틀
        self.video2_title = QLabel("비디오 2")
        self.video2_title.setAlignment(Qt.AlignCenter)
        self.video2_title.setFont(QFont("Arial", 11, QFont.Bold))
        video2_container.addWidget(self.video2_title)

        # 비디오 2 프레임
        self.video_label2 = QLabel("비디오 2 파일을 선택하세요")
        self.video_label2.setAlignment(Qt.AlignCenter)
        self.video_label2.setMinimumSize(600, 400)  # 크기 확대
        self.video_label2.setStyleSheet("border: 1px solid #ccc; background-color: #222;")
        video2_container.addWidget(self.video_label2)

        # 비디오 2 타임라인
        self.progress2 = CustomProgressBar()
        self.progress2.setMaximum(100)
        self.progress2.clicked.connect(self.progress_bar_clicked)
        video2_container.addWidget(self.progress2)

        # 비디오 2 정보 레이블
        self.video2_info = QLabel("해상도: - x - | FPS: -")
        self.video2_info.setAlignment(Qt.AlignCenter)
        self.video2_info.setStyleSheet("color: #666;")
        video2_container.addWidget(self.video2_info)

        video_layout.addLayout(video1_container)
        video_layout.addLayout(video2_container)
        main_layout.addLayout(video_layout)

        # 구분선 추가
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # 컨트롤 레이아웃
        control_layout = QGridLayout()

        # 파일 선택 버튼
        self.select_video1_btn = QPushButton("비디오 1 선택")
        self.select_video1_btn.setMinimumHeight(30)
        self.select_video1_btn.clicked.connect(lambda: self.open_video(1))

        self.select_video2_btn = QPushButton("비디오 2 선택")
        self.select_video2_btn.setMinimumHeight(30)
        self.select_video2_btn.clicked.connect(lambda: self.open_video(2))

        # 플레이어 컨트롤 레이아웃
        player_controls = QHBoxLayout()

        # 빨리 이전/이후 버튼 (-5/+5)
        self.fast_prev_btn = QPushButton("-5")
        self.fast_prev_btn.setToolTip("5단위 뒤로 (초 또는 프레임)")
        self.fast_prev_btn.clicked.connect(self.fast_previous)
        self.fast_prev_btn.setEnabled(False)

        # 이전 버튼
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.prev_btn.setToolTip("1단위 뒤로 (초 또는 프레임)")
        self.prev_btn.clicked.connect(self.previous_unit)
        self.prev_btn.setEnabled(False)

        # 재생/일시정지 버튼
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_pause_btn.setIconSize(QSize(32, 32))
        self.play_pause_btn.clicked.connect(self.toggle_play)
        self.play_pause_btn.setEnabled(False)

        # 다음 버튼
        self.next_btn = QPushButton()
        self.next_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.next_btn.setToolTip("1단위 앞으로 (초 또는 프레임)")
        self.next_btn.clicked.connect(self.next_unit)
        self.next_btn.setEnabled(False)

        # 빨리 다음 버튼 (+5)
        self.fast_next_btn = QPushButton("+5")
        self.fast_next_btn.setToolTip("5단위 앞으로 (초 또는 프레임)")
        self.fast_next_btn.clicked.connect(self.fast_next)
        self.fast_next_btn.setEnabled(False)

        player_controls.addWidget(self.fast_prev_btn)
        player_controls.addWidget(self.prev_btn)
        player_controls.addWidget(self.play_pause_btn)
        player_controls.addWidget(self.next_btn)
        player_controls.addWidget(self.fast_next_btn)

        # 비교 옵션 (초/프레임)
        option_layout = QHBoxLayout()

        self.second_radio = QRadioButton("초 단위")
        self.second_radio.setChecked(True)  # 기본값: 초 단위
        self.second_radio.toggled.connect(self.toggle_navigation_mode)

        self.frame_radio = QRadioButton("프레임 단위")
        self.frame_radio.toggled.connect(self.toggle_navigation_mode)

        # 라디오 버튼 그룹화
        self.option_group = QButtonGroup()
        self.option_group.addButton(self.second_radio)
        self.option_group.addButton(self.frame_radio)

        option_layout.addWidget(self.second_radio)
        option_layout.addWidget(self.frame_radio)

        # 시간/프레임 정보 레이블
        self.time_info_label = QLabel("시간: 0:00 / 0:00")
        self.frame_info_label = QLabel("프레임: 0 / 0")

        # 검사하기 버튼
        self.check_btn = QPushButton("검사하기")
        self.check_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.check_btn.setMinimumHeight(40)
        self.check_btn.clicked.connect(self.check_videos)
        self.check_btn.setEnabled(False)

        # 컨트롤 패널 위젯 배치
        control_layout.addWidget(self.select_video1_btn, 0, 0)
        control_layout.addWidget(self.select_video2_btn, 0, 1)
        control_layout.addLayout(player_controls, 1, 0, 1, 2, Qt.AlignCenter)
        control_layout.addLayout(option_layout, 2, 0, 1, 2)
        control_layout.addWidget(self.time_info_label, 3, 0)
        control_layout.addWidget(self.frame_info_label, 3, 1)
        control_layout.addWidget(self.check_btn, 4, 0, 1, 2)

        # 단축키 정보 레이블
        keyboard_info = QLabel("단축키: ←→ (1단위 이동), Shift+←→ (5단위 이동), Space (재생/일시정지)")
        keyboard_info.setStyleSheet("color: #666; font-size: 10px;")
        control_layout.addWidget(keyboard_info, 5, 0, 1, 2)

        main_layout.addLayout(control_layout)

        # 타이머 설정
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # 상태 표시줄 추가
        self.statusBar().showMessage("비디오를 선택해주세요")

    def setup_shortcuts(self):
        # 키보드 단축키 설정
        # 왼쪽 화살표 - 1단위 뒤로
        self.shortcut_left = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.shortcut_left.activated.connect(self.previous_unit)

        # 오른쪽 화살표 - 1단위 앞으로
        self.shortcut_right = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.shortcut_right.activated.connect(self.next_unit)

        # Shift+왼쪽 화살표 - 5단위 뒤로
        self.shortcut_shift_left = QShortcut(QKeySequence("Shift+Left"), self)
        self.shortcut_shift_left.activated.connect(self.fast_previous)

        # Shift+오른쪽 화살표 - 5단위 앞으로
        self.shortcut_shift_right = QShortcut(QKeySequence("Shift+Right"), self)
        self.shortcut_shift_right.activated.connect(self.fast_next)

        # 스페이스바 - 재생/일시정지
        self.shortcut_space = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.shortcut_space.activated.connect(self.toggle_play)

    def open_video(self, video_num):
        file_path, _ = QFileDialog.getOpenFileName(self, f"비디오 {video_num} 선택", "",
                                                   "Video Files (*.mp4 *.avi *.mkv *.mov *.mxf *.m2t *.mts)")

        if not file_path:
            return

        # 파일 이름 추출
        file_name = file_path.split('/')[-1]

        if video_num == 1:
            if self.cap1 is not None:
                self.cap1.release()

            self.cap1 = cv2.VideoCapture(file_path)
            self.fps1 = self.cap1.get(cv2.CAP_PROP_FPS)
            self.total_frames1 = int(self.cap1.get(cv2.CAP_PROP_FRAME_COUNT))
            self.duration1 = self.total_frames1 / self.fps1
            self.current_frame1 = 0
            self.video_width1 = int(self.cap1.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height1 = int(self.cap1.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.video_name1 = file_name

            # 비디오 1 제목 및 정보 업데이트
            self.video1_title.setText(file_name)
            self.video1_info.setText(f"해상도: {self.video_width1} x {self.video_height1} | FPS: {self.fps1:.2f}")

            # 첫 프레임 표시
            ret, frame = self.cap1.read()
            if ret:
                self.display_frame(frame, self.video_label1)

            # 파일 이름 상태표시줄에 표시
            self.statusBar().showMessage(f"비디오 1 로드됨: {file_name}")

        else:
            if self.cap2 is not None:
                self.cap2.release()

            self.cap2 = cv2.VideoCapture(file_path)
            self.fps2 = self.cap2.get(cv2.CAP_PROP_FPS)
            self.total_frames2 = int(self.cap2.get(cv2.CAP_PROP_FRAME_COUNT))
            self.duration2 = self.total_frames2 / self.fps2
            self.current_frame2 = 0
            self.video_width2 = int(self.cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height2 = int(self.cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.video_name2 = file_name

            # 비디오 2 제목 및 정보 업데이트
            self.video2_title.setText(file_name)
            self.video2_info.setText(f"해상도: {self.video_width2} x {self.video_height2} | FPS: {self.fps2:.2f}")

            # 첫 프레임 표시
            ret, frame = self.cap2.read()
            if ret:
                self.display_frame(frame, self.video_label2)

            # 파일 이름 상태표시줄에 표시
            self.statusBar().showMessage(f"비디오 2 로드됨: {file_name}")

        # 두 비디오가 모두 로드되었는지 확인
        if self.cap1 is not None and self.cap2 is not None:
            self.play_pause_btn.setEnabled(True)
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            self.fast_prev_btn.setEnabled(True)
            self.fast_next_btn.setEnabled(True)
            self.check_btn.setEnabled(True)

            # 진행 바 범위 설정
            self.update_progress_range()

            # 정보 업데이트
            self.update_info()

            # 상태 메시지 업데이트
            self.statusBar().showMessage("두 비디오가 모두 로드되었습니다. 재생 준비 완료.")

    def update_progress_range(self):
        # 프로그레스 바의 최대값을 설정
        if self.navigation_mode == "seconds":
            max_duration = min(self.duration1, self.duration2)
            self.progress1.setMaximum(int(max_duration))
            self.progress2.setMaximum(int(max_duration))
        else:
            max_frames = min(self.total_frames1, self.total_frames2)
            self.progress1.setMaximum(int(max_frames - 1))
            self.progress2.setMaximum(int(max_frames - 1))

    def display_frame(self, frame, label):
        # OpenCV BGR을 RGB로 변환
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # QImage 생성
        h, w, ch = frame_rgb.shape
        img = QImage(frame_rgb.data, w, h, w * ch, QImage.Format_RGB888)

        # 라벨 크기에 맞게 조정
        pixmap = QPixmap.fromImage(img)
        pixmap = pixmap.scaled(label.width(), label.height(), Qt.KeepAspectRatio)

        # 라벨에 표시
        label.setPixmap(pixmap)

    def update_frame(self):
        if not self.is_playing:
            return

        # 두 비디오 모두 끝에 도달했는지 확인
        max_frames = min(self.total_frames1, self.total_frames2)
        if self.current_frame1 >= max_frames - 1 or self.current_frame2 >= max_frames - 1:
            self.toggle_play()  # 재생 중지
            return

        # 다음 프레임으로 이동
        self.current_frame1 += 1
        self.current_frame2 += 1

        # 프로그레스 바 업데이트
        if self.navigation_mode == "seconds":
            value = int(self.current_frame1 / self.fps1)
            self.progress1.setValue(value)
            self.progress2.setValue(value)
        else:
            self.progress1.setValue(self.current_frame1)
            self.progress2.setValue(self.current_frame1)

        # 프레임 표시
        self.show_current_frames()

    def toggle_play(self):
        # 비디오가 로드되지 않았으면 무시
        if self.cap1 is None or self.cap2 is None:
            return

        self.is_playing = not self.is_playing

        if self.is_playing:
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            # 타이머 시작 (FPS에 맞게 설정)
            self.timer.start(int(1000 / self.fps1))
            self.statusBar().showMessage("재생 중...")
        else:
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.timer.stop()
            self.statusBar().showMessage("일시정지됨")

    def previous_unit(self):
        # 비디오가 로드되지 않았으면 무시
        if self.cap1 is None or self.cap2 is None:
            return

        if self.navigation_mode == "seconds":
            # 초 단위로 1초 이전
            frames_to_move = int(self.fps1)
            if self.current_frame1 >= frames_to_move:
                self.current_frame1 -= frames_to_move
                self.current_frame2 -= frames_to_move

                # 프로그레스 바 업데이트
                value = int(self.current_frame1 / self.fps1)
                self.progress1.setValue(value)
                self.progress2.setValue(value)
        else:
            # 프레임 단위로 1프레임 이전
            if self.current_frame1 > 0:
                self.current_frame1 -= 1
                self.current_frame2 -= 1

                # 프로그레스 바 업데이트
                self.progress1.setValue(self.current_frame1)
                self.progress2.setValue(self.current_frame1)

        # 프레임 표시
        self.show_current_frames()

    def next_unit(self):
        # 비디오가 로드되지 않았으면 무시
        if self.cap1 is None or self.cap2 is None:
            return

        max_frames = min(self.total_frames1, self.total_frames2)

        if self.navigation_mode == "seconds":
            # 초 단위로 1초 이후
            frames_to_move = int(self.fps1)
            if self.current_frame1 + frames_to_move < max_frames:
                self.current_frame1 += frames_to_move
                self.current_frame2 += frames_to_move

                # 프로그레스 바 업데이트
                value = int(self.current_frame1 / self.fps1)
                self.progress1.setValue(value)
                self.progress2.setValue(value)
        else:
            # 프레임 단위로 1프레임 이후
            if self.current_frame1 < max_frames - 1:
                self.current_frame1 += 1
                self.current_frame2 += 1

                # 프로그레스 바 업데이트
                self.progress1.setValue(self.current_frame1)
                self.progress2.setValue(self.current_frame1)

        # 프레임 표시
        self.show_current_frames()

    def fast_previous(self):
        # 비디오가 로드되지 않았으면 무시
        if self.cap1 is None or self.cap2 is None:
            return

        if self.navigation_mode == "seconds":
            # 초 단위로 5초 이전
            frames_to_move = int(self.fps1 * 5)
            if self.current_frame1 >= frames_to_move:
                self.current_frame1 -= frames_to_move
                self.current_frame2 -= frames_to_move
            else:
                # 시작 지점보다 앞으로 가지 않도록
                self.current_frame1 = 0
                self.current_frame2 = 0

            # 프로그레스 바 업데이트
            value = int(self.current_frame1 / self.fps1)
            self.progress1.setValue(value)
            self.progress2.setValue(value)

            self.statusBar().showMessage("-5초 이동")
        else:
            # 프레임 단위로 5프레임 이전
            if self.current_frame1 >= 5:
                self.current_frame1 -= 5
                self.current_frame2 -= 5
            else:
                # 시작 지점보다 앞으로 가지 않도록
                self.current_frame1 = 0
                self.current_frame2 = 0

            # 프로그레스 바 업데이트
            self.progress1.setValue(self.current_frame1)
            self.progress2.setValue(self.current_frame1)

            self.statusBar().showMessage("-5프레임 이동")

        # 프레임 표시
        self.show_current_frames()

    def fast_next(self):
        # 비디오가 로드되지 않았으면 무시
        if self.cap1 is None or self.cap2 is None:
            return

        max_frames = min(self.total_frames1, self.total_frames2)

        if self.navigation_mode == "seconds":
            # 초 단위로 5초 이후
            frames_to_move = int(self.fps1 * 5)
            if self.current_frame1 + frames_to_move < max_frames:
                self.current_frame1 += frames_to_move
                self.current_frame2 += frames_to_move
            else:
                # 끝 지점보다 뒤로 가지 않도록
                self.current_frame1 = max_frames - 1
                self.current_frame2 = max_frames - 1

            # 프로그레스 바 업데이트
            value = int(self.current_frame1 / self.fps1)
            self.progress1.setValue(value)
            self.progress2.setValue(value)

            self.statusBar().showMessage("+5초 이동")
        else:
            # 프레임 단위로 5프레임 이후
            if self.current_frame1 + 5 < max_frames:
                self.current_frame1 += 5
                self.current_frame2 += 5
            else:
                # 끝 지점보다 뒤로 가지 않도록
                self.current_frame1 = max_frames - 1
                self.current_frame2 = max_frames - 1

            # 프로그레스 바 업데이트
            self.progress1.setValue(self.current_frame1)
            self.progress2.setValue(self.current_frame1)

            self.statusBar().showMessage("+5프레임 이동")

        # 프레임 표시
        self.show_current_frames()

    def show_current_frames(self):
        # 비디오 1 프레임 가져오기
        self.cap1.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame1)
        ret1, frame1 = self.cap1.read()

        # 비디오 2 프레임 가져오기
        self.cap2.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame2)
        ret2, frame2 = self.cap2.read()

        # 프레임 표시
        if ret1:
            self.display_frame(frame1, self.video_label1)

        if ret2:
            self.display_frame(frame2, self.video_label2)

        # 정보 업데이트
        self.update_info()

    def progress_bar_clicked(self, position):
        # 비디오가 로드되지 않았으면 무시
        if self.cap1 is None or self.cap2 is None:
            return

        # 프로그레스 바 클릭 시 해당 위치로 이동
        if self.navigation_mode == "seconds":
            # 초 단위로 이동
            self.current_frame1 = int(position * self.fps1)
            self.current_frame2 = int(position * self.fps2)
            self.statusBar().showMessage(f"{position}초 위치로 이동")
        else:
            # 프레임 단위로 이동
            self.current_frame1 = position
            self.current_frame2 = position
            self.statusBar().showMessage(f"{position}프레임 위치로 이동")

        # 프레임 표시
        self.show_current_frames()

        # 프로그레스 바 업데이트
        if self.navigation_mode == "seconds":
            self.progress1.setValue(position)
            self.progress2.setValue(position)
        else:
            self.progress1.setValue(self.current_frame1)
            self.progress2.setValue(self.current_frame1)

    def update_info(self):
        # 시간 정보 업데이트
        current_time = self.current_frame1 / self.fps1
        total_time = min(self.duration1, self.duration2)

        mins, secs = divmod(int(current_time), 60)
        max_mins, max_secs = divmod(int(total_time), 60)

        self.time_info_label.setText(f"시간: {mins}:{secs:02d} / {max_mins}:{max_secs:02d}")

        # 프레임 정보 업데이트
        max_frames = min(self.total_frames1, self.total_frames2)
        self.frame_info_label.setText(f"프레임: {self.current_frame1} / {max_frames - 1}")

    def toggle_navigation_mode(self):
        # 비디오가 로드되지 않았으면 통과
        if self.cap1 is None or self.cap2 is None:
            return

        # 모드 전환 (초/프레임)
        if self.second_radio.isChecked():
            self.navigation_mode = "seconds"
            self.fast_prev_btn.setText("-5초")
            self.fast_next_btn.setText("+5초")
            self.statusBar().showMessage("초 단위 모드로 전환됨")
        else:
            self.navigation_mode = "frames"
            self.fast_prev_btn.setText("-5프레임")
            self.fast_next_btn.setText("+5프레임")
            self.statusBar().showMessage("프레임 단위 모드로 전환됨")

        # 프로그레스 바 범위 업데이트
        self.update_progress_range()

        # 프로그레스 바 위치 업데이트
        if self.navigation_mode == "seconds":
            value = int(self.current_frame1 / self.fps1)
            self.progress1.setValue(value)
            self.progress2.setValue(value)
        else:
            self.progress1.setValue(self.current_frame1)
            self.progress2.setValue(self.current_frame1)

        # 정보 업데이트
        self.update_info()

    def check_videos(self):
        """
        두 동영상 검사 함수 - 사용자가 직접 수정할 예정
        """
        print(f"비디오 1: {self.video_name1}")
        print(f"비디오 2: {self.video_name2}")
        self.statusBar().showMessage("검사 완료! 콘솔에 결과가 출력되었습니다.")


# 애플리케이션 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 스타일 설정으로 전체적인 UI 개선
    app.setStyle("Fusion")

    player = VideoSyncPlayer()
    player.show()
    sys.exit(app.exec_())