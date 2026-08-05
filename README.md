# GunAuto V1 — Multi-project Video Workflow Platform

GunAuto V1 là backend tạo video theo workflow, hỗ trợ nhiều project và nhiều step chạy song song bằng **FastAPI + PostgreSQL + Redis + Celery**.

## 1. Các loại input

| `input_type` | Dữ liệu bắt buộc | Luồng đầu vào |
|---|---|---|
| `script` | `script` | Dùng bài viết hoặc script có sẵn |
| `title_prompt` | `title`, `prompt` | Gọi LLM để viết bài từ tiêu đề và prompt |
| `source_video` | `source_video_uri`, `prompt` | Transcribe video rồi rewrite theo prompt |
| `voice` | `voice_uri` | Transcribe voice, tạo script và tái sử dụng voice gốc |

File video/voice được upload trước qua `POST /api/v1/uploads`, sau đó dùng `uri` trả về để tạo project.

## 2. Kiến trúc xử lý song song

Mỗi project được lưu thành một DAG trong PostgreSQL:

```text
ingest_input
   └── transcribe_media              # chỉ video/voice
          └── prepare_script
                 ├── plan_scenes
                 ├── generate_voice
                 └── collect_assets  # chờ scene plan
                        └────────────┐
                 generate_subtitles ├── render_video
                                    └── quality_check
                                           └── finalize_manifest
```

Scheduler chỉ queue một step khi toàn bộ dependency của step đó là `completed`. Các queue độc lập:

- `default`: ingest và finalize.
- `ai`: viết/rewrite script, lập scene.
- `audio`: speech-to-text, TTS, subtitle.
- `assets`: tìm hoặc tạo hình/video asset.
- `render`: FFmpeg/MoviePy render và kiểm tra đầu ra.

Vì vậy Project A có thể render trong lúc Project B đang viết script và Project C đang transcribe audio.

## 3. Cây thư mục

```text
app/
├── api/routes/          # project, upload, health endpoints
├── core/                # config và enum
├── db/                  # SQLAlchemy models và async session
├── repositories/        # truy vấn project, step, artifact
├── schemas/             # Pydantic request/response
├── services/            # storage và provider integrations
├── steps/               # handler của từng pipeline step
├── workers/             # Celery app và task executor
└── workflows/           # DAG definitions, workflow creator, scheduler
alembic/                 # PostgreSQL migrations
tests/                   # DAG và input validation tests
```

## 4. Chạy bằng Docker

```bash
cp .env.example .env
docker compose up --build
```

- Swagger API: `http://localhost:8000/docs`
- Flower: `http://localhost:5555`
- Readiness: `http://localhost:8000/health/ready`

## 5. Tạo project

### Script có sẵn

```json
POST /api/v1/projects
{
  "name": "Top 7 compact pistols",
  "input_type": "script",
  "title": "Top 7 Compact Pistols",
  "script": "Full narration script..."
}
```

### Tiêu đề + prompt

```json
{
  "name": "History video",
  "input_type": "title_prompt",
  "title": "The Evolution of the 1911",
  "prompt": "Write a documentary-style YouTube narration with clear sections."
}
```

### Video gốc + prompt rewrite

```json
{
  "name": "Rewrite source review",
  "input_type": "source_video",
  "source_video_uri": "storage/uploads/source.mp4",
  "prompt": "Rewrite as an original, neutral product-history narration."
}
```

### Voice có sẵn

```json
{
  "name": "Build video from voice",
  "input_type": "voice",
  "voice_uri": "storage/uploads/voice.mp3"
}
```

## 6. Trạng thái

Project: `pending`, `running`, `completed`, `failed`, `canceled`.

Step: `pending`, `queued`, `running`, `retrying`, `completed`, `failed`, `canceled`.

API hỗ trợ:

- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/cancel`
- `POST /api/v1/projects/{project_id}/retry`
- `POST /api/v1/projects/scheduler/dispatch`

## 7. Provider cần cắm tiếp

Các handler hiện tạo artifact placeholder nhưng đã có hợp đồng hàm và trạng thái hoàn chỉnh. Thay logic trong `app/steps/handlers.py` để cắm:

- LLM viết/rewrite script.
- Whisper hoặc STT khác.
- ElevenLabs/OpenAI TTS.
- Image/video search hoặc generation.
- FFmpeg/MoviePy và bộ template render.

Không cần thay API, database hay scheduler khi đổi provider.
