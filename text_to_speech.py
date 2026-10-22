import asyncio
import os
import random
import re
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import edge_tts


# =========================================================
# CONFIGURATION
# =========================================================

VOICES = {
    "Nữ - Hoài My": "vi-VN-HoaiMyNeural",
    "Nam - Nam Minh": "vi-VN-NamMinhNeural",
}

MAX_CHARS = 2000

# Bắt đầu với 2 tác vụ để cân bằng tốc độ và độ ổn định.
MAX_CONCURRENT_CHUNKS = 2

# Tổng số lần thử, bao gồm lần thử đầu tiên.
MAX_RETRIES = 3

# Thời gian chờ tối đa trước khi thử lại, chưa tính jitter.
MAX_RETRY_DELAY = 15


# =========================================================
# TEXT UTILITIES
# =========================================================

def safe_filename(title: str) -> str:
    """Loại bỏ các ký tự không hợp lệ trong tên file Windows."""
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', "_", title).strip()
    return name.rstrip(". ")[:120] or "audiobook"


def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Chia văn bản theo đoạn hoặc câu, hạn chế cắt ngang câu."""
    text = text.strip()

    if not text:
        return []

    chunks = []

    while len(text) > max_chars:
        split_at = -1

        for separator in ("\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "):
            position = text.rfind(separator, 0, max_chars)

            if position >= max_chars // 2:
                split_at = position + len(separator)
                break

        if split_at <= 0:
            split_at = max_chars

        chunk = text[:split_at].strip()

        if chunk:
            chunks.append(chunk)

        text = text[split_at:].strip()

    if text:
        chunks.append(text)

    return chunks


# =========================================================
# TTS ENGINE
# =========================================================

async def synthesize_chunk(
    index: int,
    text: str,
    output_path: str,
    voice: str,
    rate: str,
    semaphore: asyncio.Semaphore,
) -> str:
    """Tạo một chunk MP3, giới hạn concurrency và retry khi lỗi."""

    async with semaphore:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Xóa file dở dang nếu đây là lần thử lại.
                if os.path.exists(output_path):
                    os.remove(output_path)

                communicate = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=rate,
                )

                await communicate.save(output_path)

                if (
                    not os.path.isfile(output_path)
                    or os.path.getsize(output_path) == 0
                ):
                    raise RuntimeError("Dịch vụ trả về file MP3 rỗng.")

                return output_path

            except Exception:
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass

                if attempt >= MAX_RETRIES:
                    raise

                # Exponential backoff + jitter.
                delay = min(2 ** attempt, MAX_RETRY_DELAY)
                delay += random.uniform(0, 1)

                await asyncio.sleep(delay)

    raise RuntimeError(f"Không thể tạo chunk {index}.")


async def generate_audio(
    text: str,
    output_path: str,
    voice: str,
    rate: str,
    on_progress,
):
    """
    Chuyển đổi chunks song song có giới hạn.
    Chỉ ghép audio sau khi tất cả chunks đã thành công.
    Kết quả cuối cùng giữ đúng thứ tự văn bản ban đầu.
    """

    chunks = split_text(text)

    if not chunks:
        raise ValueError("Nội dung cần đọc đang trống.")

    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)

    # File tạm nằm cùng thư mục với file đích để os.replace
    # có thể thay thế file trên cùng filesystem.
    temp_output = output_path + ".tmp"

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHUNKS)
    progress_lock = asyncio.Lock()
    completed = 0
    total = len(chunks)

    try:
        with tempfile.TemporaryDirectory(
            prefix="tts_chunks_",
            dir=output_dir,
        ) as temp_dir:

            # Mỗi chunk có một file riêng, đánh số theo thứ tự gốc.
            part_paths = [
                os.path.join(temp_dir, f"chunk_{i:04d}.mp3")
                for i in range(1, total + 1)
            ]

            on_progress(
                0,
                total,
                f"Đang tạo {total} chunks "
                f"(tối đa {MAX_CONCURRENT_CHUNKS} tác vụ cùng lúc)...",
            )

            async def process_chunk(index: int, chunk: str) -> str:
                nonlocal completed

                part_path = await synthesize_chunk(
                    index=index,
                    text=chunk,
                    output_path=part_paths[index - 1],
                    voice=voice,
                    rate=rate,
                    semaphore=semaphore,
                )

                async with progress_lock:
                    completed += 1
                    current = completed

                on_progress(
                    current,
                    total,
                    f"Đã tạo {current}/{total} chunks.",
                )

                return part_path

            tasks = [
                process_chunk(index, chunk)
                for index, chunk in enumerate(chunks, start=1)
            ]

            # gather trả kết quả theo thứ tự tasks, không phải
            # theo thứ tự các tác vụ hoàn thành.
            results = await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

            failures = [
                (index, result)
                for index, result in enumerate(results, start=1)
                if isinstance(result, BaseException)
            ]

            if failures:
                index, error = failures[0]

                raise RuntimeError(
                    f"Chunk {index}/{total} thất bại sau "
                    f"{MAX_RETRIES} lần thử: {error}"
                ) from error

            on_progress(
                total,
                total,
                "Các chunks đã hoàn tất. Đang ghép file MP3...",
            )

            # Ghép tuần tự, theo thứ tự ban đầu.
            # Đọc từng phần nhỏ để tránh dùng quá nhiều RAM.
            with open(temp_output, "wb") as output:
                for part_path in results:
                    with open(part_path, "rb") as part:
                        while True:
                            data = part.read(1024 * 1024)

                            if not data:
                                break

                            output.write(data)

            if (
                not os.path.isfile(temp_output)
                or os.path.getsize(temp_output) == 0
            ):
                raise RuntimeError("File audio kết quả rỗng.")

        # Chỉ thay file đích sau khi mọi bước hoàn tất.
        os.replace(temp_output, output_path)

    finally:
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except OSError:
                pass


# =========================================================
# TKINTER APPLICATION
# =========================================================

class TextToSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Text to Speech Studio")
        self.root.geometry("760x680")
        self.root.minsize(600, 540)

        self.running = False

        self.title_var = tk.StringVar(value="audiobook")
        self.voice_var = tk.StringVar(value="Nữ - Hoài My")
        self.rate_var = tk.StringVar(value="+0%")

        self.folder_var = tk.StringVar(
            value=os.path.abspath("audiobooks")
        )

        self.status_var = tk.StringVar(value="Sẵn sàng.")
        self.count_var = tk.StringVar(value="0 ký tự · 0 từ")

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)

        ttk.Label(
            main,
            text="Text to Speech Studio",
            font=("Segoe UI", 18, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        # File title
        title_frame = ttk.LabelFrame(
            main,
            text="Tiêu đề file",
            padding=8,
        )
        title_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        title_frame.columnconfigure(0, weight=1)

        ttk.Entry(
            title_frame,
            textvariable=self.title_var,
        ).grid(row=0, column=0, sticky="ew")

        ttk.Label(
            title_frame,
            text=".mp3",
        ).grid(row=0, column=1, padx=(6, 0))

        # Input text
        content_frame = ttk.LabelFrame(
            main,
            text="Nội dung cần đọc",
            padding=8,
        )
        content_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            pady=(0, 10),
        )

        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        self.text = tk.Text(
            content_frame,
            wrap="word",
            font=("Segoe UI", 10),
            undo=True,
        )
        self.text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            content_frame,
            command=self.text.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.insert(
            "1.0",
            "Xin chào! Đây là công cụ chuyển văn bản thành giọng nói.\n\n"
            "Nhập một từ, một câu hoặc nhiều đoạn văn vào đây.",
        )

        self.text.bind(
            "<KeyRelease>",
            lambda _event: self.update_count(),
        )
        self.update_count()

        # Voice and rate
        options = ttk.LabelFrame(
            main,
            text="Cấu hình",
            padding=8,
        )
        options.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )

        ttk.Label(
            options,
            text="Giọng đọc",
        ).grid(row=0, column=0, sticky="w")

        ttk.Combobox(
            options,
            textvariable=self.voice_var,
            values=list(VOICES.keys()),
            state="readonly",
            width=22,
        ).grid(row=0, column=1, padx=8, sticky="w")

        ttk.Label(
            options,
            text="Tốc độ",
        ).grid(row=0, column=2, sticky="w")

        ttk.Combobox(
            options,
            textvariable=self.rate_var,
            values=["-20%", "-10%", "+0%", "+10%", "+20%"],
            state="readonly",
            width=8,
        ).grid(row=0, column=3, padx=8, sticky="w")

        # Output folder
        folder_frame = ttk.Frame(main)
        folder_frame.grid(
            row=5,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        folder_frame.columnconfigure(0, weight=1)

        ttk.Label(
            folder_frame,
            text="Thư mục lưu",
        ).grid(row=0, column=0, sticky="w")

        ttk.Entry(
            folder_frame,
            textvariable=self.folder_var,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

        ttk.Button(
            folder_frame,
            text="Chọn thư mục",
            command=self.choose_folder,
        ).grid(row=1, column=1, padx=(8, 0))

        # Progress
        self.progress = ttk.Progressbar(
            main,
            mode="determinate",
            maximum=100,
        )
        self.progress.grid(
            row=6,
            column=0,
            sticky="ew",
            pady=(0, 6),
        )

        ttk.Label(
            main,
            textvariable=self.status_var,
        ).grid(
            row=7,
            column=0,
            sticky="w",
            pady=(0, 10),
        )

        # Buttons
        buttons = ttk.Frame(main)
        buttons.grid(row=8, column=0, sticky="ew")

        self.generate_button = ttk.Button(
            buttons,
            text="Tạo file MP3",
            command=self.start_generation,
        )
        self.generate_button.pack(side="left")

        self.clear_button = ttk.Button(
            buttons,
            text="Xóa nội dung",
            command=self.clear_text,
        )
        self.clear_button.pack(side="left", padx=8)

        ttk.Label(
            buttons,
            textvariable=self.count_var,
        ).pack(side="right")

    # -----------------------------------------------------
    # UI ACTIONS
    # -----------------------------------------------------

    def update_count(self):
        content = self.text.get("1.0", "end-1c")

        self.count_var.set(
            f"{len(content):,} ký tự · {len(content.split()):,} từ"
        )

    def choose_folder(self):
        folder = filedialog.askdirectory(
            initialdir=self.folder_var.get(),
        )

        if folder:
            self.folder_var.set(folder)

    def clear_text(self):
        if self.running:
            return

        self.text.delete("1.0", "end")
        self.update_count()

    def start_generation(self):
        if self.running:
            return

        title = self.title_var.get().strip()
        content = self.text.get("1.0", "end-1c").strip()
        folder = self.folder_var.get().strip()

        if not title:
            messagebox.showwarning(
                "Thiếu tiêu đề",
                "Vui lòng nhập tiêu đề.",
            )
            return

        if not content:
            messagebox.showwarning(
                "Thiếu nội dung",
                "Vui lòng nhập nội dung cần đọc.",
            )
            return

        if not folder:
            messagebox.showwarning(
                "Thiếu thư mục",
                "Vui lòng chọn thư mục lưu.",
            )
            return

        try:
            os.makedirs(folder, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Lỗi thư mục", str(exc))
            return

        output_path = os.path.join(
            folder,
            safe_filename(title) + ".mp3",
        )

        if os.path.exists(output_path):
            overwrite = messagebox.askyesno(
                "Xác nhận ghi đè",
                f"File đã tồn tại:\n{output_path}\n\nGhi đè?",
            )

            if not overwrite:
                return

        voice = VOICES[self.voice_var.get()]
        rate = self.rate_var.get()

        self.running = True
        self.generate_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.progress.configure(value=0)
        self.status_var.set("Đang khởi tạo...")

        threading.Thread(
            target=self.worker,
            args=(content, output_path, voice, rate),
            daemon=True,
        ).start()

    # -----------------------------------------------------
    # BACKGROUND WORKER
    # -----------------------------------------------------

    def worker(self, content, output_path, voice, rate):
        def progress_callback(current, total, status):
            self.root.after(
                0,
                self.update_progress,
                current,
                total,
                status,
            )

        try:
            asyncio.run(
                generate_audio(
                    text=content,
                    output_path=output_path,
                    voice=voice,
                    rate=rate,
                    on_progress=progress_callback,
                )
            )

            self.root.after(
                0,
                self.finish_success,
                output_path,
            )

        except Exception as exc:
            self.root.after(
                0,
                self.finish_error,
                str(exc),
            )

    # -----------------------------------------------------
    # PROGRESS AND RESULTS
    # -----------------------------------------------------

    def update_progress(self, current, total, status):
        self.progress.configure(
            value=(current / total * 100) if total else 0,
        )
        self.status_var.set(status)

    def finish_success(self, output_path):
        self.running = False
        self.generate_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        self.progress.configure(value=100)
        self.status_var.set("Hoàn tất!")

        messagebox.showinfo(
            "Thành công",
            f"Đã tạo file MP3:\n{output_path}",
        )

    def finish_error(self, error):
        self.running = False
        self.generate_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        self.status_var.set("Tạo audio thất bại.")

        messagebox.showerror(
            "Lỗi tạo audio",
            error,
        )


# =========================================================
# APPLICATION ENTRY POINT
# =========================================================

def main():
    root = tk.Tk()

    try:
        ttk.Style().theme_use(
            "vista" if os.name == "nt" else "clam",
        )
    except tk.TclError:
        pass

    TextToSpeechApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
