import os
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from pymediainfo import MediaInfo
import glob


class VideoInfoViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("동영상 정보 뷰어")
        self.root.geometry("900x700")

        # 변수 초기화
        self.video_files = []
        self.current_index = 0

        # 컴포넌트 레이아웃
        self.setup_ui()

        # 키보드 바인딩 설정
        self.root.bind('<Left>', lambda event: self.show_prev_file())
        self.root.bind('<Right>', lambda event: self.show_next_file())

    def setup_ui(self):
        # 상단 프레임 (폴더 선택 및 시작 버튼)
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="폴더 경로:").pack(side=tk.LEFT, padx=(0, 5))

        self.folder_path_var = tk.StringVar()
        path_entry = ttk.Entry(top_frame, textvariable=self.folder_path_var, width=50)
        path_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        browse_btn = ttk.Button(top_frame, text="폴더 선택", command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT, padx=(0, 5))

        start_btn = ttk.Button(top_frame, text="시작", command=self.start_scan)
        start_btn.pack(side=tk.LEFT)

        # 중앙 프레임 (파일 정보 및 탐색)
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 요약 정보 프레임
        summary_frame = ttk.LabelFrame(main_frame, text="요약 정보", padding="5")
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        self.summary_text = tk.Text(summary_frame, wrap=tk.WORD, height=8)
        self.summary_text.pack(fill=tk.X)

        # 상세 정보 프레임
        detail_frame = ttk.LabelFrame(main_frame, text="상세 정보", padding="5")
        detail_frame.pack(fill=tk.BOTH, expand=True)

        # 파일 정보 텍스트 영역
        self.info_text = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD, width=80, height=20)
        self.info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 파일 탐색 버튼
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X)

        self.prev_btn = ttk.Button(nav_frame, text="이전", command=self.show_prev_file, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.file_counter_var = tk.StringVar(value="0 / 0")
        ttk.Label(nav_frame, textvariable=self.file_counter_var).pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(nav_frame, text="다음", command=self.show_next_file, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=(5, 0))

        # 현재 파일 정보
        self.current_file_var = tk.StringVar(value="")
        ttk.Label(main_frame, textvariable=self.current_file_var, wraplength=880).pack(fill=tk.X, pady=(10, 0))

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path_var.set(folder_path)

    def start_scan(self):
        folder_path = self.folder_path_var.get()
        if not folder_path or not os.path.isdir(folder_path):
            self.show_error("유효한 폴더 경로를 선택해주세요.")
            return

        # 동영상 파일 찾기
        video_extensions = (
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.3gp', '.mpg', '.mpeg', '.m4v', '.mts', '.m2t')
        self.video_files = []

        for ext in video_extensions:
            # 소문자 버전 검색
            pattern = os.path.join(folder_path, '**', f'*{ext}')
            self.video_files.extend(glob.glob(pattern, recursive=True))
            # 대문자 버전 검색
            pattern = os.path.join(folder_path, '**', f'*{ext.upper()}')
            self.video_files.extend(glob.glob(pattern, recursive=True))

        if not self.video_files:
            self.show_error("선택한 폴더에 동영상 파일이 없습니다.")
            return

        # 파일 목록 정렬
        self.video_files.sort()
        self.current_index = 0

        # UI 업데이트
        self.update_counter()
        self.show_current_file_info()
        self.update_navigation_buttons()

    def show_current_file_info(self):
        if 0 <= self.current_index < len(self.video_files):
            file_path = self.video_files[self.current_index]
            self.current_file_var.set(f"현재 파일: {file_path}")

            # pymediainfo로 정보 가져오기
            try:
                media_info = MediaInfo.parse(file_path)

                # 요약 정보 표시
                self.summary_text.delete(1.0, tk.END)
                summary = self.generate_summary(file_path, media_info)
                self.summary_text.insert(tk.END, summary)

                # 상세 정보 표시
                self.info_text.delete(1.0, tk.END)
                detail = self.format_media_info(media_info)
                self.info_text.insert(tk.END, detail)
            except Exception as e:
                self.summary_text.delete(1.0, tk.END)
                self.summary_text.insert(tk.END, f"파일 정보를 가져오는데 실패했습니다: {str(e)}")
                self.info_text.delete(1.0, tk.END)

    def generate_summary(self, file_path, media_info):
        """중요 정보만 요약하여 표시"""
        result = []

        # 파일 확장자
        file_ext = os.path.splitext(file_path)[1].lower()

        # 일반 정보
        general_track = media_info.general_tracks[0] if media_info.general_tracks else None
        video_track = media_info.video_tracks[0] if media_info.video_tracks else None

        if general_track:
            # 파일명과 확장자
            result.append(f"파일명: {os.path.basename(file_path)}")
            result.append(f"확장자: {file_ext}")

            # 포맷과 코덱
            result.append(f"포맷: {general_track.format}")

            # 길이
            duration = general_track.duration_string if hasattr(general_track,
                                                                'duration_string') and general_track.duration_string else f"{general_track.duration}ms" if hasattr(
                general_track, 'duration') else "알 수 없음"
            result.append(f"길이: {duration}")

        if video_track:
            # 코덱
            codec = video_track.codec if hasattr(video_track,
                                                 'codec') and video_track.codec else video_track.codec_id if hasattr(
                video_track, 'codec_id') else "알 수 없음"
            result.append(f"비디오 코덱: {codec}")

            # 해상도
            resolution = f"{video_track.width}x{video_track.height}" if hasattr(video_track, 'width') and hasattr(
                video_track, 'height') else "알 수 없음"
            result.append(f"해상도: {resolution}")

            # 색공간
            color_space = video_track.color_space if hasattr(video_track,
                                                             'color_space') and video_track.color_space else "알 수 없음"
            result.append(f"색공간: {color_space}")

            # 비트레이트
            bitrate = video_track.bit_rate_string if hasattr(video_track,
                                                             'bit_rate_string') and video_track.bit_rate_string else "알 수 없음"
            result.append(f"비트레이트: {bitrate}")

            # 프레임레이트
            framerate = f"{video_track.frame_rate} fps" if hasattr(video_track,
                                                                   'frame_rate') and video_track.frame_rate else "알 수 없음"
            result.append(f"프레임레이트: {framerate}")

            # HDR 여부
            hdr_formats = ["HDR", "HDR10", "HDR10+", "Dolby Vision", "HLG"]
            is_hdr = False
            hdr_format = "없음"

            for attr_name in dir(video_track):
                if not attr_name.startswith('_') and not callable(getattr(video_track, attr_name)):
                    try:
                        value = str(getattr(video_track, attr_name))
                        if any(hdr in value for hdr in hdr_formats):
                            is_hdr = True
                            hdr_format = value
                            break
                    except:
                        pass

            result.append(f"HDR: {hdr_format if is_hdr else '없음'}")

            # LOG 촬영 여부
            is_log = False
            log_info = "없음"

            # DJI DLOG 감지 (파일명)
            if "_D" in os.path.basename(file_path) and "DJI" in os.path.basename(file_path):
                is_log = True
                log_info = "DJI D-LOG"

            # 일반적인 LOG 포맷 감지
            log_formats = ["LOG", "Log", "S-Log", "V-Log", "C-Log", "N-Log"]

            if not is_log:
                for attr_name in dir(video_track):
                    if not attr_name.startswith('_') and not callable(getattr(video_track, attr_name)):
                        try:
                            value = str(getattr(video_track, attr_name))
                            if any(log in value for log in log_formats):
                                is_log = True
                                log_info = value
                                break
                        except:
                            pass

            result.append(f"LOG: {log_info}")

        return "\n".join(result)

    def format_media_info(self, media_info):
        """모든 상세 정보 표시"""
        result = []

        # 모든 트랙 정보 표시
        for track in media_info.tracks:
            result.append(f"=== {track.track_type} 트랙 ===")

            # 모든 속성을 표시
            for attr_name in dir(track):
                if not attr_name.startswith('_') and not callable(getattr(track, attr_name)):
                    try:
                        value = getattr(track, attr_name)
                        if value is not None and str(value).strip() and not isinstance(value, (list, dict)):
                            result.append(f"{attr_name}: {value}")
                    except:
                        pass

            result.append("")  # 트랙 간 빈 줄

        return "\n".join(result)

    def format_size(self, size_bytes):
        if not size_bytes:
            return "알 수 없음"

        size_bytes = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.2f} PB"

    def show_next_file(self):
        if self.current_index < len(self.video_files) - 1:
            self.current_index += 1
            self.show_current_file_info()
            self.update_counter()
            self.update_navigation_buttons()
        return "break"  # 이벤트 전파 중단

    def show_prev_file(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_file_info()
            self.update_counter()
            self.update_navigation_buttons()
        return "break"  # 이벤트 전파 중단

    def update_counter(self):
        total = len(self.video_files)
        current = self.current_index + 1 if total > 0 else 0
        self.file_counter_var.set(f"{current} / {total}")

    def update_navigation_buttons(self):
        # 이전 버튼 활성화/비활성화
        if self.current_index > 0:
            self.prev_btn["state"] = tk.NORMAL
        else:
            self.prev_btn["state"] = tk.DISABLED

        # 다음 버튼 활성화/비활성화
        if self.current_index < len(self.video_files) - 1:
            self.next_btn["state"] = tk.NORMAL
        else:
            self.next_btn["state"] = tk.DISABLED

    def show_error(self, message):
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, f"오류: {message}")
        self.info_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = VideoInfoViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()