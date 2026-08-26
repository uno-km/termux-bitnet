// AMEVA Auto-Generated i18n Dictionary
if (window.i18nManager) {
  window.i18nManager.registerTranslations({
  "en": {
    "common": {
      "brand": "Termux-BitNet",
      "releaseTag": "v1.0.6 (Production Ready)",
      "pypiBtn": "PyPI (pip)",
      "npmBtn": "npm (Node.js)",
      "githubBtn": "GitHub",
      "founderBtn": "Founder CV",
      "footerText": "© 2026 AMEVA Open-Source Foundation. Released under the Apache-2.0 License.",
      "nav": {
        "foundation": "Foundation Info",
        "libraries": "Flagship Libraries",
        "docNav": "Document Navigation",
        "aiSpecs": "AI Agent Protocols",
        "home": "Home / Architecture",
        "installation": "Installation Guide",
        "quickstart": "Quickstart & Recipes",
        "apiReference": "API Reference",
        "benchmarks": "Benchmarks & Profiling",
        "advancedParams": "Advanced Parameters",
        "versions": "Version Archive"
      }
    },
    "home": {
      "title": "Termux-BitNet",
      "subtitle": "ARM64 NEON DotProd SIMD Accelerated 1.58-bit On-Device LLM Inference Engine",
      "quickInstallTitle": "1-Line Quick Installation",
      "quickInstallDesc": "Install the official package directly into your runtime:",
      "challengeTitle": "The Engineering Challenge",
      "challengeText": "Standard FP16/INT4 LLM inference on mobile CPU architectures encounters extreme memory bandwidth bottlenecks, thermal throttling, and severe battery drain exceeding 15W.",
      "breakthroughTitle": "The Architectural Breakthrough",
      "breakthroughText": "Executes 1.58-bit ternary quantized weights {-1, 0, +1} directly via hand-vectorized ARM64 NEON assembly kernels, reducing matrix multiplications to integer additions and subtractions with under 350MB RAM footprint.",
      "featuresTitle": "Key Capabilities & Built-in Hardening",
      "matrixTitle": "Supported Compute Kernels & Operations",
      "matrixCol1": "Subsystem Category",
      "matrixCol2": "Operations & Kernels",
      "matrixCol3": "Status",
      "codeExampleTitle": "Canonical Usage Example",
      "nextStepsTitle": "Getting Started & Deep Guides",
      "linkInstall": "Detailed Installation Guide",
      "linkQuickstart": "Quickstart Recipes",
      "linkApi": "API Reference Specification",
      "features": {
        "0": {
          "title": "1.58-Bit Ternary DotProd Acceleration",
          "desc": "Replaces multiplication with integer additions using ARM64 dot-product vector SIMD instructions."
        },
        "1": {
          "title": "Zero-PRoot Native Bionic Execution",
          "desc": "Direct execution on Android Bionic libc without Linux PRoot containers or root privileges."
        },
        "2": {
          "title": "Dual-Engine Python & Node.js Gateways",
          "desc": "Ultra-low overhead thin FFI bindings for both Python 3.8+ and Node.js 18+ runtimes with independent CLI namespaces."
        },
        "3": {
          "title": "Energy-Efficient Edge Deployment",
          "desc": "Consumes under 2.5W during continuous token generation, preventing thermal throttling."
        }
      }
    }
  },
  "ko": {
    "common": {
      "brand": "Termux-BitNet",
      "releaseTag": "v1.0.6 (Production Ready)",
      "pypiBtn": "PyPI 패키지",
      "npmBtn": "npm 패키지",
      "githubBtn": "GitHub 저장소",
      "founderBtn": "설립자 CV",
      "footerText": "© 2026 AMEVA 오픈소스 재단. Apache-2.0 라이선스로 배포됨.",
      "nav": {
        "foundation": "재단 소개 (AOSF)",
        "libraries": "플래그십 라이브러리",
        "docNav": "문서 상세 목차",
        "aiSpecs": "AI 에이전트 프로토콜",
        "home": "홈 / 아키텍처",
        "installation": "설치 가이드",
        "quickstart": "퀵스타트 & 레시피",
        "apiReference": "전체 API 명세",
        "benchmarks": "벤치마크 & 하드웨어",
        "advancedParams": "고급 파라미터 제어",
        "versions": "버전 릴리즈 아카이브"
      }
    },
    "home": {
      "title": "Termux-BitNet",
      "subtitle": "ARM64 NEON DotProd SIMD 어셈블리 가속 1.58-bit 온디바이스 초고속 LLM 추론 엔진",
      "quickInstallTitle": "1줄 빠른 설치",
      "quickInstallDesc": "환경에 맞는 공식 패키지를 즉시 설치하세요:",
      "challengeTitle": "엔지니어링 도전 과제",
      "challengeText": "모바일 CPU 환경에서 표준 FP16/INT4 대규모 언어 모델 추론은 극심한 메모리 대역폭 병목과 15W 이상의 발열 및 배터리 소모를 유발합니다.",
      "breakthroughTitle": "아키텍처 혁신 및 해결책",
      "breakthroughText": "3진화 1.58-bit 가중치 {-1, 0, +1}를 최적화된 ARM64 NEON 어셈블리 커널로 직접 실행하여 행렬 곱셈을 정수 덧셈/뺄셈으로 치환하고 350MB 미만의 초경량 메모리로 고속 온디바이스 추론을 지원합니다.",
      "featuresTitle": "핵심 역량 및 빌트인 보안/안정성",
      "matrixTitle": "지원 연산 커널 및 모듈 매트릭스",
      "matrixCol1": "서브시스템 분류",
      "matrixCol2": "지원 연산 및 커널",
      "matrixCol3": "상태",
      "codeExampleTitle": "정석 사용법 코드 예제",
      "nextStepsTitle": "시작하기 & 심층 가이드",
      "linkInstall": "상세 설치 가이드",
      "linkQuickstart": "퀵스타트 & 실무 레시피",
      "linkApi": "전체 API 상세 규격서",
      "features": {
        "0": {
          "title": "1.58-bit 삼진 연산 DotProd 하드웨어 가속",
          "desc": "ARM64 Dot-Product 벡터 SIMD 명령어를 활용하여 고비용 부동소수점 곱셈을 정수 덧셈으로 대체합니다."
        },
        "1": {
          "title": "비루트 네이티브 Bionic 직접 구동",
          "desc": "루팅이나 가상 리눅스(PRoot) 컨테이너 없이 안드로이드 순정 Bionic libc 환경에서 즉각 구동됩니다."
        },
        "2": {
          "title": "Python 및 Node.js 듀얼 게이트웨이",
          "desc": "독립된 CLI 네임스페이스와 함께 Python 3.8+ 및 Node.js 18+ 런타임을 위한 경량 FFI 바인딩을 제공합니다."
        },
        "3": {
          "title": "초저전력 스마트폰 구동",
          "desc": "지속 토큰 생성 시 2.5W 미만의 초저전력을 소모하여 스마트폰의 발열 쓰로틀링을 효과적으로 방지합니다."
        }
      }
    }
  },
  "ja": {
    "common": {
      "brand": "Termux-BitNet",
      "releaseTag": "v1.0.6 (Production Ready)",
      "pypiBtn": "PyPIパッケージ",
      "npmBtn": "npmパッケージ",
      "githubBtn": "GitHub",
      "founderBtn": "創設者CV",
      "footerText": "© 2026 AMEVA Open-Source Foundation. Apache-2.0 ライセンスの下で公開。",
      "nav": {
        "foundation": "財団情報 (AOSF)",
        "libraries": "フラッグシップライブラリ",
        "docNav": "ドキュメント目次",
        "aiSpecs": "AIエージェント仕様",
        "home": "ホーム / アーキテクチャ",
        "installation": "インストールガイド",
        "quickstart": "クイックスタート",
        "apiReference": "APIリファレンス",
        "benchmarks": "ベンチマーク",
        "advancedParams": "詳細パラメータ",
        "versions": "バージョン履歴"
      }
    },
    "home": {
      "title": "Termux-BitNet",
      "subtitle": "ブラウザおよびエッジ環境向けの高パフォーマンスオープンソースシステムライブラリ",
      "quickInstallTitle": "1行クイックインストール",
      "quickInstallDesc": "ランタイムに公式パッケージを直接インストールします:",
      "challengeTitle": "技術的課題",
      "challengeText": "Standard FP16/INT4 LLM inference on mobile CPU architectures encounters extreme memory bandwidth bottlenecks, thermal throttling, and severe battery drain exceeding 15W.",
      "breakthroughTitle": "アーキテクチャのブレークスルー",
      "breakthroughText": "Executes 1.58-bit ternary quantized weights {-1, 0, +1} directly via hand-vectorized ARM64 NEON assembly kernels, reducing matrix multiplications to integer additions and subtractions with under 350MB RAM footprint.",
      "featuresTitle": "コア機能と安定性",
      "matrixTitle": "サポートされている演算とカーネル",
      "matrixCol1": "サブシステム区分",
      "matrixCol2": "サポート演算",
      "matrixCol3": "状態",
      "codeExampleTitle": "標準的なコード例",
      "nextStepsTitle": "はじめに",
      "linkInstall": "詳細インストールガイド",
      "linkQuickstart": "クイックスタートレシピ",
      "linkApi": "API仕様書"
    }
  }
});
};
