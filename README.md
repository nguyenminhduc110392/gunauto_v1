# GunAuto V1

Hệ thống pipeline module hóa để tạo video nội dung về súng từ 4 loại đầu vào:

1. Bài viết hoặc script có sẵn.
2. Tiêu đề bài viết và prompt viết bài.
3. Video gốc và prompt rewrite.
4. File voice có sẵn.

## Cây thư mục

```text
gunauto_v1/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── input_adapters.py
│   ├── main.py
│   ├── models.py
│   ├── pipeline.py
│   └── services/
│       ├── production_services.py
│       └── script_service.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Luồng xử lý

```text
Input
  -> Input Adapter
  -> ScriptService.normalize()
  -> NormalizedContent
  -> ScenePlanner.create_plan()
  -> VoiceService.create_or_reuse_voice()
  -> AssetService.collect_assets()
  -> SubtitleService.create_srt()
  -> RenderService.render()
  -> VideoManifest + video output
```

Mọi loại input đều được chuẩn hóa thành `NormalizedContent`, gồm title, script, transcript và media nguồn. Nhờ vậy phần lập cảnh, voice, subtitle và render không cần biết input ban đầu đến từ đâu.

## API

- `POST /videos/from-script`
- `POST /videos/from-title-prompt`
- `POST /videos/from-source-video`
- `POST /videos/from-voice`
- `GET /health`

## Chạy dự án

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

Mở Swagger tại `http://127.0.0.1:8000/docs`.

## Các phần đang để interface/TODO

- LLM viết và rewrite script.
- Whisper hoặc speech-to-text.
- ElevenLabs/OpenAI TTS.
- Tìm hoặc tạo asset hình ảnh/video.
- MoviePy/FFmpeg renderer.
- Tích hợp các template video riêng.

Các service đã có hợp đồng hàm cố định, nên có thể thay provider mà không làm thay đổi endpoint hoặc pipeline chính.
