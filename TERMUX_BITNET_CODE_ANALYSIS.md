# termux-bitnet 기술 아키텍처 및 소스 코드 전수 분석 보고서

---

## 1. 개요 및 시스템 아키텍처 (Overview & Architecture)

`termux-bitnet`은 Android Termux 및 ARM64 환경에 최적화된 **1.58비트(Ternary Quantization $\{-1, 0, +1\}$, `i2_s`) 온디바이스 대형 언어 모델(LLM) 추론 SDK이자 런타임 엔진**입니다.

본 프레임워크는 모바일 기기의 제한된 메모리 대역폭과 전력 예산 내에서 고속 추론을 달성하기 위해 **ARM NEON SIMD 및 ARMv8.2-A DotProd(`vdotq_s32`) 인트린직 기반의 저수준 C++ 연산 커널**을 내장하고 있으며, 이를 **C ABI, Python SDK, Node.js 게이트웨이, OpenAI 호환 로컬 HTTP 서버**의 다층 구조로 추상화하였습니다.

```
+-------------------------------------------------------------------------------+
|                             Application Layer                                 |
|  * termux-bitnet CLI / Chat REPL / Benchmark / AMEVA Brain Orchestrator       |
|  * OpenAI-Compatible HTTP Server (http://0.0.0.0:8080/v1/chat/completions)    |
+---------------------------------------+---------------------------------------+
|              Python SDK               |             Node.js SDK               |
|      (termux_bitnet.BitNetEngine)     |         (npm/lib/engine.js)           |
+---------------------------------------+---------------------------------------+
|                           C ABI Binding Layer                                 |
|                   (include/termux_bitnet.h / src/c_api.cpp)                   |
+-------------------------------------------------------------------------------+
|                       Native C++ Inference Core                               |
|        (src/llama_bitnet_core.cpp / src/ggml_bitnet_mad.cpp)                  |
|  - QK=128 32-stride Interleaved Memory Layout                                 |
|  - ARM NEON / DotProd (vdotq_s32) Acceleration / AVX2 Fallback                |
+-------------------------------------------------------------------------------+
|                          Target Operating System                              |
|           Android Termux (Native Bionic libc) / PRoot / Linux ARM64           |
+-------------------------------------------------------------------------------+
```

---

## 2. 디렉토리 구조 및 파일 맵 (Directory Map)

```
termux-bitnet/
├── CMakeLists.txt              # Native C++ 빌드 정의 (ARM NEON/DotProd 컴파일 플래그)
├── setup.py                    # Python 패키징 및 CMake 빌드 자동화 스크립트
├── install.sh                  # Termux/PRoot 원터치 환경 구성 셸 스크립트
├── pyproject.toml              # 빌드 메타데이터
├── include/
│   └── termux_bitnet.h         # C ABI 표준 공개 헤더
├── src/
│   ├── ggml_bitnet_mad.cpp     # 1.58비트 i2_s 행렬-벡터 점곱(Dot-Product) SIMD 커널
│   ├── llama_bitnet_core.h     # C++ 내부 컨텍스트 및 어휘집(Vocab) 구조체 정의
│   ├── llama_bitnet_core.cpp   # 엔진 초기화, 모델 로딩, 로짓 계산, 샘플링 로직
│   ├── c_api.cpp               # C ABI 익스포트 및 원시 텐서 연산 인터페이스
│   └── main.cpp                # 독립 실행형 네이티브 C++ CLI (termux-bitnet-cli)
├── termux_bitnet/
│   ├── __init__.py             # Python SDK 최상위 익스포트 정의
│   ├── config.py               # BitNetConfig 하이퍼파라미터 및 모델 캐시 탐색
│   ├── exceptions.py           # BitNetError, BitNetEngineNotFound 예외 정의
│   ├── hardware.py             # CPU SIMD/DotProd 기능 탐색 및 스레드 추천
│   ├── downloader.py           # 검증된 GGUF 모델 레지스트리 및 스트리밍 다운로더
│   ├── engine.py               # Ctypes C ABI 바인딩 및 서브프로세스 연동 엔진
│   ├── server.py               # 무의존성 OpenAI 규격 로컬 HTTP 서버
│   ├── cli.py                  # 통합 CLI (run, chat, serve, info, download, benchmark)
│   └── installer.py            # 사전 컴파일된 바이너리 디스패처
├── npm/
│   ├── package.json            # Node.js 패키지 정의
│   ├── index.js                # Node.js 모듈 엔트리포인트
│   ├── index.d.ts              # TypeScript 타입 선언
│   ├── bin/termux-bitnet.js    # Node.js 전용 CLI 실행기
│   └── lib/
│       ├── engine.js           # Node.js Thin Gateway 엔진
│       └── downloader.js       # Levenshtein 기반 모델 다운로더
├── examples/
│   ├── 01_simple_chat.py       # 스트리밍 텍스트 생성 기본 예제
│   ├── 02_openai_client.py     # OpenAI API 클라이언트 연동 예제
│   └── 03_brain_orchestrator.py# AMEVA 멀티모달 자율 에이전트 연동 예제
└── tests/
    ├── test_engine.py          # 엔진 기본 기능 단위 테스트
    └── test_remediation.py     # 예외 처리 및 경계 조건(Fail-Fast) 검증 테스트
```

---

## 3. 설치 및 빌드 파이프라인 (Installation & Build Pipeline)

### 3.1 원터치 설치 스크립트: `install.sh`

Termux 패키지 관리자(`pkg`) 또는 PRoot Ubuntu 환경(`apt-get`)을 자동 감지하여 빌드 체인과 런타임을 구성합니다.

```bash
# 1. 패키지 관리자 감지 및 빌드 도구 설치
pkg install -y clang cmake git python python-pip openblas libandroid-execinfo nodejs

# 2. 파이썬 휠 도구체인 업그레이드
pip install --upgrade setuptools wheel
pip install ameva-vulkan-runtime || true

# 3. 빌드 격리를 우회하여 네이티브 C++ 코어와 함께 설치
pip install --no-build-isolation -e .

# 4. Node.js 듀얼 엔진 글로벌 CLI 등록
cd npm && npm install -g .
```

* **핵심 메커니즘**: `pip install --no-build-isolation -e .` 플래그를 사용하여 Termux 환경에서 빌드 격리(isolated build environment)로 인해 발생하는 CMake 컴파일 병목을 방지하고 호스트 컴파일러를 직접 활용합니다.

---

### 3.2 네이티브 빌드 시스템: `CMakeLists.txt` 및 `setup.py`

#### `CMakeLists.txt`
ARM64 플랫폼 감지 시 하드웨어 가속 플래그를 조건부로 인젝션합니다.
```cmake
if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64|arm64")
    if(GGML_NEON)
        add_definitions(-D__ARM_NEON)
        if(GGML_ARM_DOTPROD)
            add_compile_options(-march=armv8.2-a+dotprod+fp16)
            add_definitions(-D__ARM_FEATURE_DOTPROD=1)
        else()
            add_compile_options(-march=armv8-a+simd+fp16)
        endif()
    endif()
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
    add_compile_options(-mavx2 -mfma)
endif()
```

#### `setup.py`
`/proc/cpuinfo`를 직접 파싱하여 대상 기기의 `asimd` 및 `asimddp` 지원 여부를 확인한 후 CMake 빌드 파라미터(`-DGGML_NEON=ON`, `-DGGML_ARM_DOTPROD=ON`)를 주입하여 공유 라이브러리(`libtermux_bitnet.so`)를 패키지 내부에 빌드합니다.

---

## 4. 핵심 모듈별 소스 코드 상세 해설

### 4.1 저수준 연산 커널 및 네이티브 C++ 코어

#### (1) 1.58비트 양자화 SIMD 커널: `src/ggml_bitnet_mad.cpp`

1.58비트 가중치는 2비트로 패킹되어 저장되며, 블록 크기는 $QK=128$입니다. 1바이트에는 4개의 가중치(각 2비트)가 포함됩니다.

* **메모리 인터리빙 (32-stride Interleaving)**:
  가중치 바이트에서 2비트씩 시프트 및 마스킹하여 4개의 16바이트 벡터($v_0, v_1, v_2, v_3$)를 언패킹합니다.
  활성화 텐서($y$)는 32바이트 단위로 건너뛰며 로드되어 캐시 지역성을 극대화합니다.

```cpp
// 2비트 언패킹 (MSB -> LSB)
int8x16_t v0 = vreinterpretq_s8_u8(vandq_u8(vshrq_n_u8(xb, 6), mask));
int8x16_t v1 = vreinterpretq_s8_u8(vandq_u8(vshrq_n_u8(xb, 4), mask));
int8x16_t v2 = vreinterpretq_s8_u8(vandq_u8(vshrq_n_u8(xb, 2), mask));
int8x16_t v3 = vreinterpretq_s8_u8(vandq_u8(xb, mask));

// 32-stride 인터리브드 활성화 텐서 로드
int8x16_t y0 = vld1q_s8(py + k + 0*32);
int8x16_t y1 = vld1q_s8(py + k + 1*32);
int8x16_t y2 = vld1q_s8(py + k + 2*32);
int8x16_t y3 = vld1q_s8(py + k + 3*32);
```

* **DotProd 하드웨어 가속**:
  ARMv8.2-A 이상에서는 4개의 8비트 곱셈과 32비트 누적을 1 사이클에 수행하는 `vdotq_s32` 인트린직을 사용합니다. 지원하지 않는 구형 ARMv8-A 코어에서는 `vmlal_s8` 및 `vaddq_s32`를 통한 FMA 폴백을 수행합니다.
```cpp
#if defined(__ARM_FEATURE_DOTPROD)
    accu = vdotq_s32(accu, v0, y0);
    accu = vdotq_s32(accu, v1, y1);
    accu = vdotq_s32(accu, v2, y2);
    accu = vdotq_s32(accu, v3, y3);
#else
    // FMA 폴백: 8비트 곱셈 후 16비트 확장 누적 -> 32비트 변환
    int16x8_t accula = vdupq_n_s16(0);
    accula = vmlal_s8(accula, vget_low_s8(v0), vget_low_s8(y0));
    accula = vmlal_s8(accula, vget_high_s8(v0), vget_high_s8(y0));
    ...
    accu = vaddq_s32(accu, vmovl_s16(vget_low_s16(accula)));
    accu = vaddq_s32(accu, vmovl_high_s16(accula));
#endif
```

* **커널 디스패처**:
  - `ggml_vec_dot_i2_i8_s_1x1`: 단일 행렬-벡터 연산
  - `ggml_vec_dot_i2_i8_s_1xN`: 활성화 배치 병렬 연산 (`PARALLEL_SIZE = 4`)
  - `ggml_vec_dot_i2_i8_s_Nx1`: 가중치 멀티 로우 연산
  - `ggml_vec_dot_i2_i8_s`: 호출 타입(`type`)에 따른 라우팅 함수

---

#### (2) C ABI 인터페이스: `include/termux_bitnet.h`

C/C++, Python(ctypes), Rust 등 다양한 언어와의 바인딩을 위한 표준 C ABI를 선언합니다.

* **설정 구조체 (`bitnet_params_t`)**:
  모델 경로, 스레드 수(`n_threads`), 컨텍스트 윈도우 크기(`n_ctx`), 배치 크기(`n_batch`, `n_ubatch`), 샘플링 파라미터(`temperature`, `top_p`, `top_k`, `min_p`, `repeat_penalty`, `repeat_last_n`), GPU 오프로드 계층 수(`n_gpu_layers`)를 정의합니다.
* **스트리밍 콜백 시그니처**:
  `typedef bool (*bitnet_stream_cb)(const char* token_str, int32_t token_id, void* user_data);`
  콜백에서 `false`를 반환하면 엔진이 즉시 생성을 중단(Early Abort)합니다.

---

#### (3) 코어 엔진 구현체: `src/llama_bitnet_core.cpp`

1. **엄격한 초기화 검증 (`bitnet_init`)**:
   - 파라미터 NULL 여부, 모델 경로 유효성, 파일 존재 여부, 파일 헤더 크기(최소 1024 바이트 이상)를 검증합니다.
   - 유효하지 않을 경우 즉시 에러 메시지와 함께 공식 모델 다운로드 카탈로그 가이드를 출력하고 `nullptr`을 반환합니다(Fail-Fast).
2. **토크나이징 및 디코딩 (`bitnet_tokenize`, `bitnet_token_to_str`)**:
   - BPE(Byte-Pair Encoding) 토큰 어휘집과 매핑하여 UTF-8 문자열과 토큰 ID 간 상호 변환을 수행합니다.
3. **샘플링 엔진 (`bitnet_sample`)**:
   - **반복 방지 페널티(Repetition Penalty)**: 직전 `repeat_last_n`개 토큰의 로짓에 감산 페널티(`-8.0f`)를 적용하여 루프 생성을 방지합니다.
   - **Softmax 및 확률적 샘플링**: 상위 유효 로짓을 추출하여 Softmax 확률 분포를 계산한 후, 난수 생성기(`std::mt19937`)를 통해 다음 토큰을 샘플링합니다.
4. **스트리밍 생성 파이프라인 (`bitnet_generate_stream`)**:
   - 시스템 프롬프트와 사용자 입력을 결합하여 프롬프트 평가(`bitnet_eval`)를 진행합니다.
   - 토큰별 생성 루프를 돌며 콜백 호출, 정지 토큰(Stop Tokens) 일치 검사, 성능 지표(TTFT, TPS)를 실시간 기록합니다.

---

### 4.2 Python SDK 및 실행 계층

#### (1) 하드웨어 탐색 모듈: `termux_bitnet/hardware.py`

모바일 기기의 하드웨어 사양을 런타임에 진단하여 최적의 추론 스레드 수를 결정합니다.

```python
def detect_hardware() -> HardwareProfile:
    # 1. /proc/cpuinfo 탐색
    # NEON (asimd), DotProd (asimddp), FP16 (fphp) 플래그 확인
    # 2. SoC 식별: Snapdragon, Exynos, Dimensity, Tensor 등
    # 3. 모바일 Big.LITTLE 코어 스케줄링 휴리스틱:
    #    8코어 모바일 AP(4 Big + 4 Little)에서는 발열 쓰로틀링(Thermal Throttling) 방지를 위해
    #    Big 코어 수에 맞춘 4개 스레드를 추천합니다.
```

---

#### (2) 모델 레지스트리 및 다운로더: `termux_bitnet/downloader.py`

검증된 1.58비트 GGUF 모델 레지스트리를 관리하며, 견고한 다운로드를 제공합니다.

* **등록 모델 카탈로그**:
  - `bitnet-2b`: Microsoft BitNet 2B-4T (`i1_s` 양자화, 564 MB) - 모바일 초고속 기본 모델
  - `bitnet-large`: BitNet 2B (`i1_m` 양자화, 718 MB) - 고품질 모델
  - `bitnet-3b`: BitNet 3.3B (`q1_3` 양자화, 730 MB)
  - `bitnet-3b-q4`: BitNet 3.3B (`Q4_0` 양자화, 1.83 GB)
* **오타 자동 교정 (Typo Correction)**:
  사용자가 `bitnet2b` 또는 `bitnet-lg` 등으로 오입력 시 `difflib.get_close_matches`를 통해 유사한 모델명을 탐지하고 안내합니다.
* **HTTP Range 기반 이어받기 (Resume Support)**:
  다운로드 중단 시 로컬에 저장된 파일 크기부터 HTTP `Range: bytes={downloaded}-` 헤더를 통해 다운로드를 재개합니다.

---

#### (3) Python 엔진 및 실행 라우터: `termux_bitnet/engine.py`

1. **하드웨어 가속 위임**:
   - `import ameva_vulkan_runtime as avr`를 통해 Vulkan GPU 백엔드가 활성화되어 있는지 확인하고 GPU 오프로드(`n_gpu_layers = 33`)를 자동 적용합니다.
2. **2단계 실행 전략 (Dual-Engine Execution Strategy)**:
   - **우선 순위 1**: 시스템에 빌드된 네이티브 CLI 바이너리(`llama-cli` 등)를 서브프로세스로 실행하여 1.58비트 추론을 수행하고 표준 출력 스트림을 실시간 파싱하여 제너레이터(`yield`)로 반환합니다.
   - **우선 순위 2**: 네이티브 바이너리가 없을 경우 C ABI 공유 라이브러리(`libtermux_bitnet.so`)를 `ctypes`로 직접 로드하여 내부 C++ 엔진을 호출합니다.
3. **리소스 수명 주기 관리**:
   - `__enter__` 및 `__exit__` 컨텍스트 매니저를 지원하여 추론 종료 시 `bitnet_free`를 호출해 C 메모리 누수를 원천 차단합니다.

---

#### (4) OpenAI 호환 로컬 HTTP 서버: `termux_bitnet/server.py`

외부 의존성(FastAPI/Flask 등) 없이 Python 내장 `http.server.HTTPServer` 및 `BaseHTTPRequestHandler`만으로 구축된 초경량 OpenAI 규격 API 서버입니다.

* **엔드포인트 지원**:
  - `GET /health`: 서버 헬스체크
  - `GET /v1/models`: 사용 가능한 모델 목록 반환
  - `POST /v1/chat/completions`: 표준 챗 컴플리션 (단일 JSON 응답 및 Server-Sent Events 기반 SSE 스트리밍 `stream: true` 완벽 지원)
  - `POST /v1/completions`: 일반 텍스트 완성
* **엄격한 에러 처리 (Fail-Fast)**:
  엔진 미초기화 시 HTTP 503 반환, 빈 메시지 입력 시 HTTP 400 JSON 규격 에러 반환.

---

#### (5) 통합 CLI 인터페이스: `termux_bitnet/cli.py`

다음의 6대 서브커맨드를 제공합니다:

| 서브커맨드 | 역할 | 주요 옵션 |
| :--- | :--- | :--- |
| `info` | 모바일 CPU SIMD/DotProd 및 하드웨어 사양 출력 | - |
| `download` | 검증된 1.58비트 GGUF 모델 다운로드 | `<model_name>`, `-o/--output-dir`, `--force` |
| `run` | 단일 프롬프트 스트리밍 텍스트 생성 | `-m`, `-p`, `-f`, `-t`, `-c`, `--temp`, `--top-p`, `-ngl` |
| `chat` | 실시간 대화형 REPL 터미널 세션 시작 | `-m`, `-t`, `-c`, `--temp`, `--top-p` |
| `serve` | OpenAI 호환 로컬 REST API 서버 구동 | `-m`, `--host`, `--port` (기본값: `0.0.0.0:8080`) |
| `benchmark` | 코딩, 논리, 심리 다분야 벤치마크 수행 및 TPS 측정 | `-m`, `-t` |
| `install` | 1-Click 네이티브 엔진 프로비저닝 | - |

---

### 4.3 Node.js / JavaScript 게이트웨이

* **`npm/lib/engine.js`**:
  Node.js의 `child_process.spawn`을 활용하여 네이티브 엔진을 비동기 실행하고, `generateStream(prompt, maxTokens, onToken)`을 통해 JavaScript 비동기 콜백 스트리밍을 제공합니다.
* **`npm/lib/downloader.js`**:
  Levenshtein Distance 알고리즘을 내장하여 CLI에서 모델명 오타 입력 시 최적의 교정 모델명을 제안하며, Node.js `https` 스트림을 통해 진행률 바(Progress Bar)를 출력합니다.

---

## 5. 실행 흐름 및 라이프사이클 (Execution Lifecycle)

### 5.1 CLI 실행 시 처리 흐름 (Stream Generation Sequence)

```
User Shell
   │
   ▼
termux-bitnet run -m model.gguf -p "Explain BitNet"
   │
   ├─► [1. Argument & Model Validation]
   │     - validate_model_path_or_exit() -> 파일 크기/GGUF 헤더 확인
   │     - 프롬프트 공백 검사 -> 빈 문자열 시 exit code 2 즉시 반환
   │
   ├─► [2. Engine Context Initialization]
   │     - BitNetConfig 생성
   │     - ameva-vulkan-runtime 가속 컨텍스트 바인딩 확인
   │     - libtermux_bitnet.so / llama-cli 프로세스 확인
   │
   ├─► [3. Prompt Evaluation]
   │     - bitnet_tokenize() -> Token ID 배열 생성
   │     - bitnet_eval() -> KV Cache 전방향 연산 및 First Token 계산 (TTFT 측정)
   │
   ├─► [4. Autoregressive Token Generation Loop]
   │     - bitnet_sample() -> Softmax + Repetition Penalty 로짓 샘플링
   │     - Stop sequence 및 EOS 검사
   │     - stdout.write(token) -> 실시간 터미널 출력
   │     - Next Token에 대한 bitnet_eval() 수행
   │
   └─► [5. Telemetry & Resource Cleanup]
         - GenerationMetrics (TPS, Total Latency) 집계 및 출력
         - bitnet_free() C++ 컨텍스트 메모리 해제
```

---

## 6. 사용 및 실행 가이드 (Practical Usage Guide)

### 6.1 환경 진단 및 모델 다운로드
```bash
# 1. 기기 하드웨어 SIMD/DotProd 기능 확인
termux-bitnet info

# 2. 공식 1.58비트 경량 모델 다운로드 (캐시 경로: ~/.cache/termux-bitnet/models/)
termux-bitnet download bitnet-2b
```

### 6.2 CLI 스트리밍 추론 및 대화
```bash
# 1. 단일 프롬프트 실행 (8 스레드, 128 토큰)
termux-bitnet run -m ~/.cache/termux-bitnet/models/bitnet-2b-bitnet-b1.58-2b-i1_s.gguf -p "Explain quantum computing in 2 sentences:" -t 8

# 2. 대화형 터미널 REPL 시작
termux-bitnet chat -m ~/.cache/termux-bitnet/models/bitnet-2b-bitnet-b1.58-2b-i1_s.gguf -t 4
```

### 6.3 OpenAI 호환 로컬 API 서버 구동
```bash
# 서버 시작 (기본 포트 8080)
termux-bitnet serve -m ~/.cache/termux-bitnet/models/bitnet-2b-bitnet-b1.58-2b-i1_s.gguf --port 8080
```

#### cURL을 통한 API 호출 테스트:
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, BitNet!"}],
    "temperature": 0.5,
    "max_tokens": 64
  }'
```

### 6.4 Python SDK 프로그래밍 연동 (`examples/01_simple_chat.py`)
```python
import sys
from termux_bitnet import BitNetEngine, BitNetConfig, detect_hardware

# 하드웨어 자동 감지 기반 스레드 설정
hw = detect_hardware()
config = BitNetConfig(
    n_threads=hw.recommended_threads,
    temperature=0.3,
    top_p=0.95,
    repeat_penalty=1.15
)

# 컨텍스트 매니저를 통한 안전한 생성 및 메모리 해제
with BitNetEngine(config) as engine:
    prompt = "Write a Python function to check palindrome:"
    print(f"[Prompt]: {prompt}\n[Response]: ", end="", flush=True)
    
    for token in engine.generate_stream(prompt, max_tokens=100):
        sys.stdout.write(token)
        sys.stdout.flush()
        
    metrics = engine.get_last_metrics()
    print(f"\n\n[Telemetry] Speed: {metrics.tokens_per_second:.2f} tokens/sec")
```

---

## 7. 검증 및 테스트 규격 (Testing & Quality Assurance)

`tests/` 디렉토리 내에 구축된 단위 테스트 및 회귀 테스트 스위트는 다음의 항목을 엄격히 검증합니다:

1. `test_01_hardware_detection`: CPU 아키텍처, 코어 수, NEON 및 DotProd 부울 플래그 무결성 검증.
2. `test_bitnet_native_missing_raises_exception`: 네이티브 라이브러리 부재 시 임의의 텍스트를 반환하지 않고 명시적 `BitNetEngineNotFound` 예외를 발생시키는지 검증.
3. `test_model_missing_raises_file_not_found`: 존재하지 않는 모델 파일 경로 지정 시 즉시 `FileNotFoundError` 발생 검증.
4. `test_empty_prompt_raises_value_error`: 빈 프롬프트 전달 시 `ValueError` 발생 검증.
5. `test_download_model_typo_suggestion`: 모델명 오타 입력 시 교정 제안 동작 검증.
6. `test_server_engine_uninitialized_returns_503`: 서버 핸들러의 엔진 미초기화 시 HTTP 503 반환 검증.

---

### 결론 요약
`termux-bitnet`은 Android Termux 및 ARM64 모바일 디바이스 상에서 **1.58비트 Ternary 가중치 모델을 ARM NEON 및 DotProd 하드웨어 수준에서 초고속으로 가속**할 수 있도록 설계된 프로덕션 레디 툴체인입니다. C++ 네이티브 연산 코어, C ABI 브릿지, Python SDK, Node.js 게이트웨이 및 OpenAI 호환 서버가 완벽히 결합되어 모바일 온디바이스 AI 파이프라인을 온전히 로컬에서 구동할 수 있습니다.
