# Kiosk AI : Age/Gender-aware Video Player

- 웹 캠으로 사람으 성별/연령대를 추정해 카테고리별 동영상을 재생하는 키오스크 플레이어
- InsightFace로 얼굴/성별/나이를 추정하고, OpenCV로 캡처, python-vlc로 전체화면 재생을 제어한다.

## 특징

- 실시간 얼굴 검출 + 성별/나이 추정(InsightFace)
- 카테고리 매핑으로 폴더별 영상 자동 재생
  사용자 클립 1회 재생 후 사후 스캔으로 자연스러운 전환
- AMD GPU(DirectML) 사용 가능, 미지원 환경은 CPU로 자동 폴백
- 모니터 인덱스 지정 전체화면 재생

## 폴더 구조

```
kiosk_ai/
├─ config/
│ └─ pipeline.yaml
├─ src/
│ ├─ main.py
│ ├─ categories.py
│ ├─ config.py
│ ├─ runtime_state.py
│ ├─ loops/
│ │ ├─ __init__.py
│ │ ├─ capture_loop.py
│ │ ├─ infer_loop.py
│ │ └─ preview_loop.py
│ ├─ ai_insight/
│ │ ├─ __init__.py
│ │ └─ engine.py
│ └─ player/
│ │ ├─ __init__.py
│ │ ├─ fullscreen.py
│ │ ├─ kiosk_player.py
│ │ ├─ video_utils.py
│ │ └─ vlc_controller.py
├─ videos/
│ ├─ young_male/
│ ├─ young_female/
│ ├─ senior_male/
│ ├─ senior_female/
│ └─ fallback_video/
```

- videos 하위 각 폴더에는 최소 1개 이상의 mp4 파일이 있어야 한다.

## 실행 방법

1. Python 3.11 설치, VLC 플레이어 설치

2. 가상환경 생성 후 라이브러리 설치

   ```
   python -m pip install --upgrade pip
   pip install opencv-python numpy onnxruntime-directml python-vlc screeninfo insightface
   ```

3. 설정 파일 확인

   - config/pipeline.yaml 에서 모니터 인덱스, 카메라 인덱스, providers, 비디오 경로를 확인/수정
   - src/config.py 에서 pipeline.yaml 경로 확인/수정

4. 실행
   ```
   python src\main.py
   ```
   - 키보드 Q : 프리뷰 창만 닫기
   - 키보드 ESC : 전체 앱 종료

## 구성

```
camera:
  index_candidates: [0, 1, 2]
  width: 640
  height: 360
  fps: 30
inference:
  sample_every_n_frames: 1
  male_threshold: 0.5
  age_cutoff_years: 50
  hysteresis_sec: 2.0
runtime:
  providers: ["DmlExecutionProvider", "CPUExecutionProvider"]
display:
  target_monitor_index: 1
videos:
  base: "D:\\kiosk_ai\\videos"
  categories:
    young_male: "young_male"
    young_female: "young_female"
    senior_male: "senior_male"
    senior_female: "senior_female"
    fallback: "fallback_video"
defaults:
  fallback_category: "fallback"
```

- providers
  - AMD GPU : ["DmlExecutionProvider", "CPUExecutionProvider"]
  - 강제 CPU : ["CPUExecutionProvider"]
  - NVIDIA GPU를 사용할 계획이면 onnxruntime-gpu를 쓰는 분기 코드를 넣어야 하므로 현재 버전은 CPU 또는 DirectML만 지원
- target_monitor_index
  - 0 이 메인 모니터, 듀얼이면 1이 보조 모니터

## 작동 방법

- src\ai_insight\engine.py
  - InsightFace FaceAnalysis를 어댑터로 감싸 detect와 age/gender 추정을 제공
- src\loops\\\*.py
  - 캡처/추론/프리뷰 쓰레드 루프
- src\player\\\*.py
  - VLC 임베딩, 전체화면 제어, 재생 리스트 전환
- src\main.py
  - 상태머신, 히스테리시스, 사후 스캔 로직을 조율

## 트러블슈팅

- insightface 라이브러리가 다운 불가
  - Visual Studio 설치되었는지 확인
- VLC가 뜨지 않거나 검은 화면
  - VLC 설치 확인, 64bit 권장
  - Windows에서 관리자 권한 콘솔이 필요한 환경이 있을 수 있음
- 카메라가 열리지 않음
  - pipeline.yaml의 camera.index_candidates를 변경
  - 다른 앱에서 웹캠 사용 중인지 확인
- AMD GPU가 안 잡힘
  - providers에서 CPUExecutionProvider를 같이 두면 자동 폴백
  - onnxruntime-directml 설치 확인
- OpenCV 창이 안 뜨는 환경
  - 라즈베리파이 등 헤드리스 환경은 preview_loop를 끄거나 X11 준비 필요
