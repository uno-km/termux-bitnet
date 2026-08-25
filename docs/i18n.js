/**
 * AMEVA Ecosystem - Master Universal Multilingual (i18n) Core Engine (SSOT v2.1)
 * 100% Full-Page Body, Table, Heading, and Alert Dynamic Translation across 13 Languages.
 */

(function(global) {
  'use strict';

  const SUPPORTED_LANGUAGES = {
    'en': { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸', dir: 'ltr' },
    'ko': { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷', dir: 'ltr' },
    'ja': { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵', dir: 'ltr' },
    'zh': { code: 'zh', name: 'Chinese', nativeName: '简体中文', flag: '🇨🇳', dir: 'ltr' },
    'ar': { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦', dir: 'rtl' },
    'fr': { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷', dir: 'ltr' },
    'de': { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪', dir: 'ltr' },
    'es': { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸', dir: 'ltr' },
    'hi': { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳', dir: 'ltr' },
    'ru': { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺', dir: 'ltr' },
    'vi': { code: 'vi', name: 'Vietnamese', nativeName: 'Tiếng Việt', flag: '🇻🇳', dir: 'ltr' },
    'pl': { code: 'pl', name: 'Polish', nativeName: 'Polski', flag: '🇵🇱', dir: 'ltr' },
    'la': { code: 'la', name: 'Latin', nativeName: 'Latina', flag: '🏛️', dir: 'ltr' }
  };

  const DEFAULT_LANG = 'en';
  const STORAGE_KEYS = ['ameva_global_lang', 'uno_km_lang', 'ameva_lib_doc_lang', 'forge_lang'];
  const PHRASE_MAP = {

  "AMEVA Ecosystem": {
    "ko": "AMEVA 생태계",
    "zh": "AMEVA 生态系统",
    "ja": "AMEVA 生態系",
    "ar": "النظام البيئي AMEVA",
    "fr": "Écosystème AMEVA",
    "de": "AMEVA Ökosystem",
    "es": "Ecosistema AMEVA",
    "hi": "AMEVA इकोसिस्टम",
    "ru": "Экосистема AMEVA",
    "vi": "Hệ sinh thái AMEVA",
    "pl": "Ekosystem AMEVA",
    "la": "Oecosystema AMEVA"
  },
  "Overview": {
    "ko": "개요",
    "zh": "概述",
    "ja": "概要",
    "ar": "نظرة عامة",
    "fr": "Aperçu",
    "de": "Überblick",
    "es": "Descripción General",
    "hi": "अवलोकन",
    "ru": "Обзор",
    "vi": "Tổng quan",
    "pl": "Przegląd",
    "la": "Conspectus"
  },
  "Official Reference": {
    "ko": "공식 레퍼런스",
    "zh": "官方参考",
    "ja": "公式リファレンス",
    "ar": "المرجع الرسمي",
    "fr": "Référence Officielle",
    "de": "Offizielle Referenz",
    "es": "Referencia Oficial",
    "hi": "आधिकारिक संदर्भ",
    "ru": "Официальная документация",
    "vi": "Tài liệu tham khảo",
    "pl": "Oficjalna Dokumentacja",
    "la": "Documenta Publica"
  },
  "Interactive": {
    "ko": "인터랙티브",
    "zh": "交互式演示",
    "ja": "インタラクティブ",
    "ar": "تفاعلي",
    "fr": "Interactif",
    "de": "Interaktiv",
    "es": "Interactivo",
    "hi": "इंटरैक्टिव",
    "ru": "Интерактив",
    "vi": "Tương tác",
    "pl": "Interaktywne",
    "la": "Repertorium"
  },
  "Concepts": {
    "ko": "핵심 개념",
    "zh": "核心概念",
    "ja": "コア概念",
    "ar": "المفاهيم الأساسية",
    "fr": "Concepts Clés",
    "de": "Kernkonzepte",
    "es": "Conceptos Clave",
    "hi": "मुख्य अवधारणाएँ",
    "ru": "Основные концепции",
    "vi": "Khái niệm cốt lõi",
    "pl": "Kluczowe Pojęcia",
    "la": "Doctrinae"
  },
  "Documentation": {
    "ko": "공식 문서",
    "zh": "官方文档",
    "ja": "公式ドキュメント",
    "ar": "الوثائق الرسمية",
    "fr": "Documentation Officielle",
    "de": "Offizielle Dokumentation",
    "es": "Documentación Oficial",
    "hi": "आधिकारिक दस्तावेज़",
    "ru": "Официальные документы",
    "vi": "Tài liệu chính thức",
    "pl": "Oficjalne Dokumenty",
    "la": "Documenta Primaria"
  },
  "AI Agent Protocols": {
    "ko": "AI 에이전트 프로토콜",
    "zh": "AI 代理规范",
    "ja": "AIエージェント仕様",
    "ar": "بروتوكولات الذكاء الاصطناعي",
    "fr": "Protocoles Agent IA",
    "de": "KI-Agenten-Protokolle",
    "es": "Protocolos de Agente IA",
    "hi": "AI एजेंट प्रोटोकॉल",
    "ru": "Протоколы ИИ-агентов",
    "vi": "Giao thức AI Agent",
    "pl": "Protokoły Agentów AI",
    "la": "Rationes Agentis AI"
  },
  "AI Agent Protocols & Feeds": {
    "ko": "AI 에이전트 프로토콜 & 피드",
    "zh": "AI 代理规范与订阅",
    "ja": "AIエージェント仕様 & フィード",
    "ar": "بروتوكولات وخلاصات الذكاء الاصطناعي",
    "fr": "Protocoles et flux d'agents IA",
    "de": "KI-Agenten-Protokolle & Feeds",
    "es": "Protocolos y fuentes de agentes IA",
    "hi": "AI एजेंट प्रोटोकॉल और फ़ीड्स",
    "ru": "Протоколы и фиды ИИ-агентов",
    "vi": "Giao thức & Nguồn cấp dữ liệu AI",
    "pl": "Protokoły i kanały agentów AI",
    "la": "Rationes et Flumina Agentis AI"
  }
,
  "Model Hub & GGUF Quantization Presets": {
    "ko": "모델 허브 & GGUF 양자화 프리셋",
    "zh": "模型中心与 GGUF 量化预设",
    "ja": "モデルハブ & GGUF量子化プリセット",
    "ar": "مركز النماذج وإعدادات تكميم GGUF المسبقة",
    "fr": "Hub de modèles et préréglages de quantification GGUF",
    "de": "Modell-Hub & GGUF-Quantisierungs-Presets",
    "es": "Centro de modelos y preajustes de cuantización GGUF",
    "hi": "मॉडल हब और GGUF परिमाणीकरण प्रीसेट",
    "ru": "Центр моделей и пресеты квантования GGUF",
    "vi": "Trung tâm mô hình & Cài đặt lượng tử hóa GGUF",
    "pl": "Centrum modeli i profile kwantyzacji GGUF",
    "la": "Centrum Exemplarium et Praefinitiones Quantizationis GGUF"
  },
  "Specifications for built-in mobile-optimized presets and custom weight resolution.": {
    "ko": "내장된 모바일 최적화 프리셋 및 커스텀 가중치 분석 명세서입니다.",
    "zh": "内置移动端优化预设与自定义权重解析规范。",
    "ja": "組み込みモバイル最適化プリセットおよびカスタム重み解決の仕様。",
    "ar": "مواصفات الإعدادات المسبقة المحسنة للأجهزة المحمولة ودقة الأوزان المخصصة.",
    "fr": "Spécifications pour les préréglages optimisés pour mobiles et la résolution de poids personnalisés.",
    "de": "Spezifikationen für integrierte, mobil-optimierte Voreinstellungen und benutzerdefinierte Gewichtungen.",
    "es": "Especificaciones para preajustes optimizados para móviles y resolución de pesos personalizados.",
    "hi": "अंतर्निहित मोबाइल-अनुकूलित प्रीसेट और कस्टम वेट रिज़ॉल्यूशन के विनिर्देश।",
    "ru": "Спецификации встроенных пресетов для мобильных устройств и пользовательских весов.",
    "vi": "Thông số kỹ thuật cho các cài đặt sẵn tối ưu hóa cho thiết bị di động và trọng số tùy chỉnh.",
    "pl": "Specyfikacje wbudowanych profili mobilnych i własnych wag modeli.",
    "la": "Specificationes praefinitionum mobilium et resolutionis ponderum consuetudinariorum."
  },
  "Preset Name": {
    "ko": "프리셋 명칭",
    "zh": "预设名称",
    "ja": "プリセット名",
    "ar": "اسم الإعداد المسبق",
    "fr": "Nom du préréglage",
    "de": "Preset-Name",
    "es": "Nombre de preset",
    "hi": "प्रीसेट नाम",
    "ru": "Имя пресета",
    "vi": "Tên cài đặt trước",
    "pl": "Nazwa profilu",
    "la": "Nomen Praefiniti"
  },
  "Base Architecture & Quantization": {
    "ko": "기반 아키텍처 및 양자화",
    "zh": "基础架构与量化",
    "ja": "基本アーキテクチャ & 量子化",
    "ar": "البنية الأساسية والكمية",
    "fr": "Architecture de base & Quantification",
    "de": "Basisarchitektur & Quantisierung",
    "es": "Arquitectura base y cuantización",
    "hi": "आधार आर्किटेक्चर और परिमाणीकरण",
    "ru": "Базовая архитектура и квантование",
    "vi": "Kiến trúc cơ sở & Lượng tử hóa",
    "pl": "Architektura bazowa i kwantyzacja",
    "la": "Architectura Fundamentalis et Quantizatio"
  },
  "File Size": {
    "ko": "파일 크기",
    "zh": "文件大小",
    "ja": "ファイルサイズ",
    "ar": "حجم الملف",
    "fr": "Taille du fichier",
    "de": "Dateigröße",
    "es": "Tamaño de archivo",
    "hi": "फ़ाइल का आकार",
    "ru": "Размер файла",
    "vi": "Kích thước tệp",
    "pl": "Rozmiar pliku",
    "la": "Magnitudo Fasciculi"
  },
  "Optimal Steps & CFG": {
    "ko": "최적 스텝 수 & CFG",
    "zh": "最佳步数与 CFG",
    "ja": "最適ステップ数 & CFG",
    "ar": "الخطوات المثلى و CFG",
    "fr": "Étapes optimales & CFG",
    "de": "Optimale Schritte & CFG",
    "es": "Pasos óptimos y CFG",
    "hi": "इष्टतम चरण और CFG",
    "ru": "Оптимальные шаги и CFG",
    "vi": "Số bước tối ưu & CFG",
    "pl": "Optymalne kroki i CFG",
    "la": "Gradus Optimi et CFG"
  },
  "Recommended Sampler": {
    "ko": "권장 샘플러",
    "zh": "推荐采样器",
    "ja": "推奨サンプラー",
    "ar": "المعين الموصى به",
    "fr": "Échantillonneur recommandé",
    "de": "Empfohlener Sampler",
    "es": "Muestreador recomendado",
    "hi": "अनुशंसित सैंपलर",
    "ru": "Рекомендуемый сэмплер",
    "vi": "Bộ lấy mẫu khuyến nghị",
    "pl": "Zalecany sampler",
    "la": "Specimen Commendatum"
  },
  "Key Visual Workload": {
    "ko": "주요 시각 작업 영역",
    "zh": "主要视觉工作负载",
    "ja": "主なビジュアル用途",
    "ar": "عبء العمل البصري الرئيسي",
    "fr": "Charge de travail visuelle principale",
    "de": "Wichtigste visuelle Arbeitslast",
    "es": "Carga de trabajo visual clave",
    "hi": "प्रमुख दृश्य कार्यभार",
    "ru": "Ключевая визуальная нагрузка",
    "vi": "Khối lượng công việc trực quan chính",
    "pl": "Główne obciążenie wizualne",
    "la": "Munus Visus Primarium"
  },
  "Ultra-low latency mobile prototyping (Instant 1-2s, sharp)": {
    "ko": "초저지연 모바일 프로토타이핑 (1~2초 즉시 생성, 선명함)",
    "zh": "超低延迟移动端原型设计（1-2秒即时生成，清晰锐利）",
    "ja": "超低遅延モバイルプロトタイピング（1〜2秒で即時生成、鮮明）",
    "ar": "نمذجة أولية فائقة السرعة للأجهزة المحمولة (توليد فوري خلال 1-2 ثانية)",
    "fr": "Prototypage mobile à très faible latence (instantané 1-2s, net)",
    "de": "Ultra-Low-Latency Mobile Prototyping (Sofort 1-2s, gestochen scharf)",
    "es": "Prototipado móvil de ultra baja latencia (instantáneo 1-2s, nítido)",
    "hi": "अल्ट्रा-लो लेटेंसी मोबाइल प्रोटोटाइपिंग (तुरंत 1-2 सेकंड, स्पष्ट)",
    "ru": "Сверхнизкая задержка для мобильного прототипирования (1-2 сек, четко)",
    "vi": "Tạo mẫu di động độ trễ cực thấp (1-2 giây tức thì, sắc nét)",
    "pl": "Prototypowanie mobilne o ultra niskim opóźnieniu (1-2s natychmiast, ostre)",
    "la": "Prototypatio mobilis celeritatis maximae (1-2s, clara)"
  },
  "2D / 2.5D stylized anime art (Crisp lineart, rich cel-shading)": {
    "ko": "2D / 2.5D 스타일화 애니메이션 아트 (깔끔한 선화, 풍부한 셀 셰이딩)",
    "zh": "2D / 2.5D 风格化动漫艺术（清晰线条，丰富赛璐璐阴影）",
    "ja": "2D / 2.5D スタイライズドアニメアート（鮮明な線画、豊かなセル画シェーディング）",
    "ar": "فن الأنمي ثنائي/ثنائي ونصف الأبعاد (خطوط واضحة وتظليل غني)",
    "fr": "Art anime stylisé 2D / 2.5D (lignes nettes, ombrage riche)",
    "de": "2D / 2.5D stilisierte Anime-Kunst (klare Linienführung, reiches Cel-Shading)",
    "es": "Arte anime estilizado 2D / 2.5D (líneas nítidas, sombreado rico)",
    "hi": "2D / 2.5D शैलीबद्ध एनीमे कला (स्पष्ट रेखाएं, समृद्ध छायांकन)",
    "ru": "Стилизованный аниме-арт 2D / 2.5D (четкие линии, богатое затенение)",
    "vi": "Nghệ thuật anime 2D / 2.5D cách điệu (nét vẽ sắc nét, đổ bóng phong phú)",
    "pl": "Stylizowana grafika anime 2D / 2.5D (ostre linie, bogate cieniowanie)",
    "la": "Ars animata 2D / 2.5D (lineae clarae, umbrae divites)"
  },
  "Ultra-detailed photorealism (Pores, eyes, cinematic lighting)": {
    "ko": "초고화질 실사풍 렌더링 (피부 모공, 눈동자, 시네마틱 조명)",
    "zh": "超逼真写实渲染（毛孔、眼神、电影级光影）",
    "ja": "超詳細フォトリアリズム（毛穴、瞳、映画のようなライティング）",
    "ar": "واقعية سينمائية فائقة التفاصيل (المسام، العيون، الإضاءة السينمائية)",
    "fr": "Photoréalisme ultra-détaillé (pores, yeux, éclairage cinématographique)",
    "de": "Hochdetaillierter Fotorealismus (Poren, Augen, filmische Beleuchtung)",
    "es": "Fotorrealismo ultra detallado (poros, ojos, iluminación cinematográfica)",
    "hi": "अत्यधिक विस्तृत यथार्थवाद (त्वचा के छिद्र, आंखें, सिनेमाई प्रकाश व्यवस्था)",
    "ru": "Ультрадетализированный фотореализм (поры, глаза, кинематографичный свет)",
    "vi": "Chân thực cực kỳ chi tiết (lỗ chân lông, mắt, ánh sáng điện ảnh)",
    "pl": "Niezwykle szczegółowy fotorealizm (pory, oczy, oświetlenie filmowe)",
    "la": "Photorealismus subtilissimus (pori, oculi, lux cinematographica)"
  },
  "General-purpose drafting and balanced composition": {
    "ko": "범용 시안 제작 및 균형 잡힌 구도 생성",
    "zh": "通用草图绘制与平衡构图",
    "ja": "汎用ドラフト作成およびバランスの取れた構図",
    "ar": "صياغة عامة وتكوين متوازن",
    "fr": "Création générale et composition équilibrée",
    "de": "Allgemeine Entwurfserstellung und ausgewogene Komposition",
    "es": "Borradores de uso general y composición equilibrada",
    "hi": "सामान्य प्रयोजन प्रारूपण और संतुलित रचना",
    "ru": "Универсальное черчение и сбалансированная композиция",
    "vi": "Soạn thảo mục đích chung và bố cục cân bằng",
    "pl": "Ogólne szkicowanie i zrównoważona kompozycja",
    "la": "Delineatio generalis et compositio aequilibrata"
  },
  "Lightweight SD1.5 base generation": {
    "ko": "경량화 SD1.5 기본 이미지 생성",
    "zh": "轻量级 SD1.5 基础图像生成",
    "ja": "軽量SD1.5ベース画像生成",
    "ar": "توليد صور خفيف الوزن معتمد على SD1.5",
    "fr": "Génération de base SD1.5 légère",
    "de": "Leichtgewichtige SD1.5-Basisgenerierung",
    "es": "Generación base ligera de SD1.5",
    "hi": "हल्का SD1.5 आधार निर्माण",
    "ru": "Легкая базовая генерация на SD1.5",
    "vi": "Tạo hình ảnh cơ sở SD1.5 nhẹ",
    "pl": "Lekkie generowanie bazowe SD1.5",
    "la": "Generatio levis SD1.5"
  },
  "💡 Denoising Architecture Rules (정석 파라미터 가이드)": {
    "ko": "💡 노이즈 제거 아키텍처 규칙 (정석 파라미터 가이드)",
    "zh": "💡 去噪架构规则（标准参数指南）",
    "ja": "💡 ノイズ除去アーキテクチャ規則（標準パラメータガイド）",
    "ar": "💡 قواعد بنية إزالة الضوضاء (دليل المعلمات القياسي)",
    "fr": "💡 Règles d'architecture de débruitage (Guide des paramètres standard)",
    "de": "💡 Denoising-Architekturregeln (Standard-Parameterleitfaden)",
    "es": "💡 Reglas de arquitectura de reducción de ruido (Guía de parámetros estándar)",
    "hi": "💡 डिनॉइज़िंग आर्किटेक्चर नियम (मानक पैरामीटर गाइड)",
    "ru": "💡 Правила архитектуры шумоподавления (Стандартное руководство по параметрам)",
    "vi": "💡 Quy tắc kiến trúc khử nhiễu (Hướng dẫn tham số chuẩn)",
    "pl": "💡 Zasady architektury odszumiania (Standardowy przewodnik po parametrach)",
    "la": "💡 Regulae Architecturae Denudationis"
  },
  "Custom Model Management API": {
    "ko": "커스텀 모델 관리 API",
    "zh": "自定义模型管理 API",
    "ja": "カスタムモデル管理API",
    "ar": "واجهة برمجة تطبيقات إدارة النماذج المخصصة",
    "fr": "API de gestion des modèles personnalisés",
    "de": "API zur benutzerdefinierten Modellverwaltung",
    "es": "API de gestión de modelos personalizados",
    "hi": "कस्टम मॉडल प्रबंधन API",
    "ru": "API управления пользовательскими моделями",
    "vi": "API Quản lý Mô hình Tùy chỉnh",
    "pl": "API zarządzania własnymi modelami",
    "la": "API Moderandi Exemplaria Consuetudinaria"
  },
  "Benchmarks & Hardware Profiling": {
    "ko": "벤치마크 & 하드웨어 프로파일링",
    "zh": "基准测试与硬件性能分析",
    "ja": "ベンチマーク & ハードウェアプロファイリング",
    "ar": "اختبارات الأداء وتحليل الأجهزة",
    "fr": "Benchmarks & Profilage matériel",
    "de": "Benchmarks & Hardware-Profiling",
    "es": "Benchmarks y perfilado de hardware",
    "hi": "बेंचमार्क और हार्डवेयर प्रोफाइलिंग",
    "ru": "Бенчмарки и профилирование оборудования",
    "vi": "Đo điểm chuẩn & Hồ sơ phần cứng",
    "pl": "Benchmarki i profilowanie sprzętu",
    "la": "Mensurae et Descriptio Instrumentorum"
  },
  "Empirical latency, memory footprint, and big.LITTLE core scaling benchmarks on Exynos and Snapdragon devices.": {
    "ko": "엑시노스 및 스냅드래곤 기기에서의 실제 생성 소요 시간, 메모리 점유율 및 big.LITTLE 코어 스케일링 실측 벤치마크 데이터입니다.",
    "zh": "Exynos 与 Snapdragon 设备上的实测延迟、内存占用及 big.LITTLE 核心扩展基准数据。",
    "ja": "ExynosおよびSnapdragonデバイスにおける実測レイテンシ、メモリフットプリント、big.LITTLEコアスケーリングベンチマーク。",
    "ar": "اختبارات قياسية لزمن الوصول الفعلي وبصمة الذاكرة على أجهزة Exynos و Snapdragon.",
    "fr": "Latence empirique, empreinte mémoire et benchmarks de mise à l'échelle sur Exynos et Snapdragon.",
    "de": "Empirische Latenz, Speicherbedarf und Core-Skalierungs-Benchmarks auf Exynos- und Snapdragon-Geräten.",
    "es": "Latencia empírica, huella de memoria y benchmarks de escalado de núcleos en Exynos y Snapdragon.",
    "hi": "Exynos और Snapdragon उपकरणों पर व्यावहारिक विलंबता, मेमोरी फ़ुटप्रिंट और बेंचमार्क।",
    "ru": "Практические замеры задержки, использования памяти и масштабирования ядер на Exynos и Snapdragon.",
    "vi": "Độ trễ thực tế, dung lượng bộ nhớ và điểm chuẩn mở rộng lõi trên các thiết bị Exynos và Snapdragon.",
    "pl": "Empiryczne pomiary opóźnień, zużycia pamięci i skalowania rdzeni na procesorach Exynos i Snapdragon.",
    "la": "Mensurae latitatis, usus memoriae et gradationis nucleorum in apparatibus Exynos et Snapdragon."
  },
  "Device & Chipset": {
    "ko": "기기 및 칩셋",
    "zh": "设备与芯片组",
    "ja": "デバイス & チップセット",
    "ar": "الجهاز ومجموعة الشرائح",
    "fr": "Appareil & Chipset",
    "de": "Gerät & Chipsatz",
    "es": "Dispositivo y chipset",
    "hi": "डिवाइस और चिपसेट",
    "ru": "Устройство и чипсет",
    "vi": "Thiết bị & Chipset",
    "pl": "Urządzenie i procesor",
    "la": "Apparatus et Microprocessus"
  },
  "Model Preset": {
    "ko": "모델 프리셋",
    "zh": "模型预设",
    "ja": "モデルプリセット",
    "ar": "إعداد النموذج المسبق",
    "fr": "Préréglage de modèle",
    "de": "Modell-Voreinstellung",
    "es": "Preajuste de modelo",
    "hi": "मॉडल प्रीसेट",
    "ru": "Пресет модели",
    "vi": "Cài đặt trước của mô hình",
    "pl": "Profil modelu",
    "la": "Praefinitio Exemplaris"
  },
  "Quantization": {
    "ko": "양자화",
    "zh": "量化方式",
    "ja": "量子化",
    "ar": "التكميم",
    "fr": "Quantification",
    "de": "Quantisierung",
    "es": "Cuantización",
    "hi": "परिमाणीकरण",
    "ru": "Квантование",
    "vi": "Lượng tử hóa",
    "pl": "Kwantyzacja",
    "la": "Quantizatio"
  },
  "Steps": {
    "ko": "스텝 수",
    "zh": "步数",
    "ja": "ステップ数",
    "ar": "الخطوات",
    "fr": "Étapes",
    "de": "Schritte",
    "es": "Pasos",
    "hi": "चरण",
    "ru": "Шаги",
    "vi": "Bước",
    "pl": "Kroki",
    "la": "Gradus"
  },
  "Inference Latency": {
    "ko": "추론 소요 시간",
    "zh": "推理耗时",
    "ja": "推論レイテンシ",
    "ar": "زمن الاستدلال",
    "fr": "Latence d'inférence",
    "de": "Inferenzlatenz",
    "es": "Latencia de inferencia",
    "hi": "अनुमान विलंबता",
    "ru": "Время инференса",
    "vi": "Độ trễ suy luận",
    "pl": "Opóźnienie wnioskowania",
    "la": "Tempus Coniecturae"
  },
  "Peak RAM": {
    "ko": "최대 RAM 점유율",
    "zh": "峰值 RAM",
    "ja": "ピークRAM",
    "ar": "أقصى استهلاك للذاكرة",
    "fr": "RAM maximale",
    "de": "Spitzen-RAM",
    "es": "RAM máxima",
    "hi": "चरम रैम",
    "ru": "Пиковая RAM",
    "vi": "RAM tối đa",
    "pl": "Szczytowe zużycie RAM",
    "la": "RAM Maxima"
  },
  "Quickstart & Integration Recipes": {
    "ko": "퀵스타트 & 연동 레시피",
    "zh": "快速上手与集成代码范式",
    "ja": "クイックスタート & 統合レシピ",
    "ar": "البدء السريع ووصفات التكامل",
    "fr": "Démarrage rapide et recettes d'intégration",
    "de": "Schnellstart & Integrationsrezepte",
    "es": "Inicio rápido y recetas de integración",
    "hi": "त्वरित शुरुआत और एकीकरण रेसिपी",
    "ru": "Быстрый старт и рецепты интеграции",
    "vi": "Bắt đầu nhanh & Công thức tích hợp",
    "pl": "Szybki start i receptury integracji",
    "la": "Initium Rapidum et Formulae"
  },
  "Ready-to-use recipes for programmatic integration across Python and Node.js environments.": {
    "ko": "Python 및 Node.js 환경에서 즉시 활용 가능한 실전 코드 모음입니다.",
    "zh": "适用于 Python 和 Node.js 环境的即开即用程序化集成代码范式。",
    "ja": "PythonおよびNode.js環境でのプログラミング統合用レシピ。",
    "ar": "وصفات جاهزة للاستخدام للتكامل البرمجي عبر بيئات Python و Node.js.",
    "fr": "Recettes prêtes à l'emploi pour l'intégration logicielle sous Python et Node.js.",
    "de": "Gebrauchsfertige Rezepte für die programmatische Integration in Python- und Node.js-Umgebungen.",
    "es": "Recetas listas para usar para la integración programática en entornos Python y Node.js.",
    "hi": "पायथन और Node.js वातावरण में उपयोग के लिए तैयार कोड रेसिपी।",
    "ru": "Готовые рецепты для программной интеграции в средах Python и Node.js.",
    "vi": "Các công thức sẵn sàng sử dụng để tích hợp theo chương trình trên môi trường Python và Node.js.",
    "pl": "Gotowe receptury do integracji programistycznej w środowiskach Python i Node.js.",
    "la": "Formulae paratae ad usum in Python et Node.js."
  },
  "Recipe 1: High-Fidelity Photorealism (Python)": {
    "ko": "레시피 1: 초고화질 실사풍 생성 (Python)",
    "zh": "范式 1：超高清写实人物渲染（Python）",
    "ja": "レシピ 1: 超高画質フォトリアリズム（Python）",
    "ar": "الوصفة 1: واقعية فوتوغرافية عالية الدقة (بايثون)",
    "fr": "Recette 1 : Photoréalisme haute fidélité (Python)",
    "de": "Rezept 1: High-Fidelity-Fotorealismus (Python)",
    "es": "Receta 1: Fotorrealismo de alta fidelidad (Python)",
    "hi": "रेसिपी 1: हाई-फिडेलिटी फोटोरियलिज्म (पायथन)",
    "ru": "Рецепт 1: Высококачественный фотореализм (Python)",
    "vi": "Công thức 1: Chân thực độ trung thực cao (Python)",
    "pl": "Receptura 1: Fotorealizm wysokiej jakości (Python)",
    "la": "Formula I: Photorealismus Subtilissimus (Python)"
  },
  "Visual Showcase & Gallery": {
    "ko": "비주얼 쇼케이스 & 갤러리",
    "zh": "视觉画廊与生成示例展示",
    "ja": "ビジュアルショーケース & ギャラリー",
    "ar": "المعرض البصري وعينات التوليد",
    "fr": "Galerie visuelle & Vitrine de rendu",
    "de": "Visuelle Galerie & Rendering-Showcase",
    "es": "Galería visual y muestra de renderizado",
    "hi": "विजुअल शोकेस और गैलरी",
    "ru": "Визуальная галерея и примеры рендеринга",
    "vi": "Triển lãm trực quan & Thư viện hình ảnh",
    "pl": "Galeria wizualna i prezentacja renderów",
    "la": "Expositio Visus et Pinacotheca"
  },
  "High-resolution on-device output samples generated across 5 built-in presets on Samsung Galaxy hardware.": {
    "ko": "삼성 갤럭시 단말에서 5대 내장 프리셋으로 완전한 온디바이스 (Client-Side Native) 생성된 고해상도 결과물 샘플입니다.",
    "zh": "在三星 Galaxy 硬件上通过 5 大内置预设 100% 本地生成的超高清图像示例。",
    "ja": "Samsung Galaxyハードウェア上の5つの組み込みプリセットで生成された高解像度サンプル。",
    "ar": "عينات إخراج عالية الدقة تم إنشاؤها عبر 5 إعدادات مسبقة مدمجة على أجهزة Samsung Galaxy.",
    "fr": "Échantillons de sortie haute résolution générés sur matériel Samsung Galaxy avec 5 préréglages.",
    "de": "Hochauflösende On-Device-Ausgabebeispiele, generiert auf Samsung Galaxy-Hardware mit 5 Presets.",
    "es": "Muestras de salida de alta resolución generadas en dispositivos Samsung Galaxy con 5 preajustes.",
    "hi": "सैमसंग गैलेक्सी हार्डवेयर पर 5 अंतर्निहित प्रीसेट के माध्यम से उत्पन्न उच्च-रिज़ॉल्यूशन आउटपुट नमूने।",
    "ru": "Примеры выходных изображений высокого разрешения, сгенерированные на устройствах Samsung Galaxy.",
    "vi": "Các mẫu đầu ra độ phân giải cao được tạo trên phần cứng Samsung Galaxy qua 5 cài đặt sẵn.",
    "pl": "Próbki o wysokiej rozdzielczości wygenerowane na urządzeniach Samsung Galaxy z 5 profilami.",
    "la": "Exempla altae resolutionis producta in apparatu Samsung Galaxy per V praefinitiones."
  },
  "Installation Guide & Scenarios": {
    "ko": "설치 가이드 & 시나리오",
    "zh": "安装指南与配置场景",
    "ja": "インストールガイド & シナリオ",
    "ar": "دليل التثبيت والسيناريوهات",
    "fr": "Guide d'installation et scénarios",
    "de": "Installationsanleitung & Szenarien",
    "es": "Guía de instalación y escenarios",
    "hi": "इंस्टॉलेशन गाइड और परिदृश्य",
    "ru": "Руководство по установке и сценарии",
    "vi": "Hướng dẫn cài đặt & Kịch bản",
    "pl": "Instrukcja instalacji i scenariusze",
    "la": "Institutio et Exempla Usus"
  },
  "Step-by-step setup instructions for fresh installs, CLI drafting, and custom models.": {
    "ko": "신규 설치, CLI 도구 연동 및 커스텀 모델 구성을 위한 단계별 안내서입니다.",
    "zh": "适用于全新安装、CLI 工具联动以及自定义模型配置的分步指南。",
    "ja": "新規インストール、CLIドラフト、カスタムモデル向けの詳細セットアップ手順。",
    "ar": "تعليمات الإعداد خطوة بخطوة لعمليات التثبيت الجديدة وتكوين النماذج المخصصة.",
    "fr": "Instructions de configuration étape par étape pour nouvelles installations et modèles personnalisés.",
    "de": "Schritt-für-Schritt-Anleitung für Neuinstallationen, CLI-Workflows und benutzerdefinierte Modelle.",
    "es": "Instrucciones de configuración paso a paso para nuevas instalaciones y modelos personalizados.",
    "hi": "नए इंस्टॉलेशन, CLI ड्राफ्टिंग और कस्टम मॉडल के लिए चरण-दर-चरण निर्देश।",
    "ru": "Пошаговые инструкции по установке, работе с CLI и настройке пользовательских моделей.",
    "vi": "Hướng dẫn thiết lập từng bước cho cài đặt mới, CLI và mô hình tùy chỉnh.",
    "pl": "Instrukcje konfiguracji krok po kroku dla nowych instalacji i własnych modeli.",
    "la": "Institutiones gradatim ad novas institutiones et exemplaria consuetudinaria."
  },
  "System Prerequisites": {
    "ko": "시스템 사전 요구사항",
    "zh": "系统先决条件",
    "ja": "システム前提条件",
    "ar": "متطلبات النظام المسبقة",
    "fr": "Prérequis système",
    "de": "Systemvoraussetzungen",
    "es": "Requisitos previos del sistema",
    "hi": "सिस्टम पूर्वापेक्षाएँ",
    "ru": "Системные требования",
    "vi": "Điều kiện tiên quyết của hệ thống",
    "pl": "Wymagania systemowe",
    "la": "Necessitates Systematis"
  },
  "Installation Verification": {
    "ko": "설치 무결성 검증",
    "zh": "安装完整性验证",
    "ja": "インストール検証",
    "ar": "التحقق من صحة التثبيت",
    "fr": "Vérification de l'installation",
    "de": "Installationsüberprüfung",
    "es": "Verificación de instalación",
    "hi": "इंस्टॉलेशन सत्यापन",
    "ru": "Проверка установки",
    "vi": "Xác minh cài đặt",
    "pl": "Weryfikacja instalacji",
    "la": "Comprobatio Institutionis"
  }
};

  // Cache original English phrases in DOM nodes
  const origTextMap = new WeakMap();

  class I18nManager {
    constructor() {
      this.currentLang = DEFAULT_LANG;
      this.translations = {};
      this.initialized = false;
    }

    init() {
      this.currentLang = this._getSavedLang() || this._detectBrowserLang();
      if (!SUPPORTED_LANGUAGES[this.currentLang]) {
        this.currentLang = DEFAULT_LANG;
      }

      this._setupLanguageSelectors();
      this._setupCodeCopyButtons();
      this._setupTabs();
      this._setupStorageListener();

      if (global.i18nTranslations) {
        this.registerTranslations(global.i18nTranslations);
      } else if (global.AOSF_i18n) {
        this.registerTranslations(global.AOSF_i18n);
      }

      this.applyLanguage(this.currentLang);
      this.initialized = true;
    }

    registerTranslations(dict) {
      this.translations = dict || {};
      if (this.initialized || document.readyState === 'complete' || document.readyState === 'interactive') {
        this.applyLanguage(this.currentLang);
      }
    }

    _getSavedLang() {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const langParam = urlParams.get('lang');
        if (langParam && SUPPORTED_LANGUAGES[langParam]) return langParam;

        for (let i = 0; i < STORAGE_KEYS.length; i++) {
          const val = localStorage.getItem(STORAGE_KEYS[i]);
          if (val && SUPPORTED_LANGUAGES[val]) return val;
        }
      } catch (e) {
        return null;
      }
      return null;
    }

    _saveLang(lang) {
      try {
        for (let i = 0; i < STORAGE_KEYS.length; i++) {
          localStorage.setItem(STORAGE_KEYS[i], lang);
        }
      } catch (e) {}
    }

    _detectBrowserLang() {
      try {
        const nav = navigator.languages || [navigator.language || ''];
        for (let i = 0; i < nav.length; i++) {
          const code = nav[i].toLowerCase().substring(0, 2);
          if (SUPPORTED_LANGUAGES[code]) return code;
        }
      } catch (e) {}
      return DEFAULT_LANG;
    }

    _setupStorageListener() {
      try {
        window.addEventListener('storage', (e) => {
          if (STORAGE_KEYS.includes(e.key) && e.newValue && SUPPORTED_LANGUAGES[e.newValue]) {
            if (e.newValue !== this.currentLang) {
              this.setLanguage(e.newValue);
            }
          }
        });
      } catch (e) {}
    }

    setLanguage(lang) {
      if (!SUPPORTED_LANGUAGES[lang]) return;
      this.currentLang = lang;
      this._saveLang(lang);
      this.applyLanguage(lang);

      document.querySelectorAll('.lang-select').forEach(sel => {
        sel.value = lang;
      });

      document.documentElement.lang = lang;
      document.documentElement.dir = SUPPORTED_LANGUAGES[lang].dir || 'ltr';
    }

    _getCurrentContext() {
      const path = (window.location.pathname || '').toLowerCase();
      if (path.includes('playwright')) return 'playwright';
      if (path.includes('stt')) return 'stt';
      if (path.includes('diffusion')) return 'diffusion';
      if (path.includes('train')) return 'train';
      if (path.includes('forge')) return 'forge';
      if (path.includes('sentinel')) return 'sentinel';
      return 'foundation';
    }

    applyLanguage(lang) {
      const dict = this.translations[lang] || this.translations[DEFAULT_LANG] || this.translations['ko'] || {};
      const ctx = this._getCurrentContext();
      const metaMap = {"playwright": {"brand": "Termux-Playwright", "title": "Termux-Playwright", "subtitles": {"en": "Production On-Device Browser Automation and Scraper Engine for Android Termux", "ko": "안드로이드 Termux를 위한 프로덕션급 온디바이스 브라우저 자동화 & 스크래핑 엔진", "ja": "Android Termux向けオンデバイスブラウザ自動化およびスクレイピングエンジン", "zh": "适用于 Android Termux 的端侧浏览器自动化与网页采集引擎", "ar": "محرك أتمتة المتصفح واستخراج البيانات على الأجهزة المحمولة لنظام Android Termux", "fr": "Moteur d'automatisation et de scraping de navigateur sur appareil pour Android Termux", "de": "On-Device-Browser-Automatisierungs- und Scraping-Engine für Android Termux", "es": "Motor de automatización y extracción de navegadores en el dispositivo para Android Termux", "hi": "Android Termux के लिए ऑन-डिवाइस ब्राउज़र ऑटोमेशन और स्क्रैपर इंजन", "ru": "Автоматизация браузера и сбор данных на устройствах Android Termux", "vi": "Công cụ tự động hóa và trích xuất trình duyệt trên thiết bị Android Termux", "pl": "Silnik automatyzacji i scrapowania przeglądarki na urządzeniach Android Termux", "la": "Machina automatica et extractio navigatoris in apparatu Android Termux"}}, "stt": {"brand": "Termux-STT", "title": "Termux-STT", "subtitles": {"en": "Production On-Device Speech-to-Text & 128d X-Vector Speaker Diarization for Android Termux", "ko": "안드로이드 Termux 전용 프로덕션급 온디바이스 음성인식 & 128차원 X-Vector 화자 분리 프레임워크", "ja": "Android Termux専用オンデバイス音声認識および128次元X-Vector話者分離フレームワーク", "zh": "适用于 Android Termux 的生产级端侧语音识别与 128 维 X-Vector 说话人日志分离框架", "ar": "إطار عمل تحويل الكلام إلى نص والتعرف على المتحدث 128d لنظام Android Termux", "fr": "Framework de reconnaissance vocale et de diarisation des locuteurs 128d sur Android Termux", "de": "On-Device-Sprach-zu-Text- und 128d-X-Vector-Sprechertrennung für Android Termux", "es": "Framework de voz a texto y diarización de hablantes 128d en el dispositivo para Android Termux", "hi": "Android Termux के लिए ऑन-डिवाइस स्पीच-टू-टेक्स्ट और 128d स्पीकर डायराइजेशन", "ru": "Распознавание речи и диаризация дикторов 128d на устройствах Android Termux", "vi": "Nhận dạng giọng nói và phân tách người nói 128d trên thiết bị Android Termux", "pl": "Rozpoznawanie mowy i diaryzacja mówców 128d na urządzeniach Android Termux", "la": "Recongnitio vocis et secretio locutorum 128d in apparatu Android Termux"}}, "diffusion": {"brand": "Termux-Diffusion", "title": "Termux-Diffusion", "subtitles": {"en": "Production On-Device AI Image Generation Framework for Android Termux & Samsung Galaxy", "ko": "안드로이드 Termux 및 삼성 갤럭시를 위한 온디바이스 AI 이미지 생성 프레임워크", "ja": "Android TermuxおよびSamsung Galaxy向けオンデバイスAI画像生成フレームワーク", "zh": "适用于 Android Termux 和三星 Galaxy 的生产级端侧 AI 图像生成框架", "ar": "إطار عمل توليد الصور بالذكاء الاصطناعي على أجهزة Android Termux وSamsung Galaxy", "fr": "Framework de génération d'images IA sur appareil pour Android Termux et Samsung Galaxy", "de": "On-Device-KI-Bilderzeugungs-Framework für Android Termux und Samsung Galaxy", "es": "Framework de generación de imágenes IA en el dispositivo para Android Termux y Samsung Galaxy", "hi": "Android Termux और Samsung Galaxy के लिए ऑन-डिवाइस AI इमेज जेनरेशन फ्रेमवर्क", "ru": "Генерация изображений с помощью ИИ на устройствах Android Termux и Samsung Galaxy", "vi": "Khung tạo hình ảnh AI trên thiết bị cho Android Termux & Samsung Galaxy", "pl": "Generowanie obrazów AI na urządzeniach Android Termux i Samsung Galaxy", "la": "Formatio imaginum per AI in apparatu Android Termux et Samsung Galaxy"}}, "train": {"brand": "Termux-Train", "title": "Termux-Train", "subtitles": {"en": "Ultra-lightweight On-Device Tensor & DAG Autograd Deep Learning Framework for Android ARM64 Termux", "ko": "안드로이드 ARM64 Termux를 위한 초경량 온디바이스 텐서 연산 & DAG 자동미분(Autograd) 딥러닝 프레임워크", "ja": "Android ARM64 Termux向け超軽量オンバイステンソル演算＆DAG自動微分深層学習フレームワーク", "zh": "适用于 Android ARM64 Termux 的超轻量端侧张量运算与有向无环图自动求导深度学习框架", "ar": "إطار عمل للتعلم العميق وحساب المشتقات التلقائية خفيف الوزن لنظام Android ARM64 Termux", "fr": "Framework d'apprentissage profond et d'autodifférenciation DAG ultra-léger pour Android ARM64 Termux", "de": "Ultraleichtes On-Device-Tensor- und DAG-Autograd-Deep-Learning-Framework für Android ARM64 Termux", "es": "Framework de aprendizaje profundo y autograd de tensores ultraligero para Android ARM64 Termux", "hi": "Android ARM64 Termux के लिए अल्ट्रा-लाइटवेट ऑन-डिवाइस टेंसर और DAG ऑटोग्रैड डीप लर्निंग फ्रेमवर्क", "ru": "Сверхлегкий фреймворк глубокого обучения и автографа тензоров для Android ARM64 Termux", "vi": "Khung học sâu Tensor & DAG Autograd siêu nhẹ trên thiết bị cho Android ARM64 Termux", "pl": "Ultralekki framework uczenia głębokiego i autogradu tensorów dla Android ARM64 Termux", "la": "Syntaxis levissima tensurae et autograd pro Android ARM64 Termux"}}, "forge": {"brand": "AMEVA-Forge", "title": "AMEVA-Forge", "subtitles": {"en": "Client-Compute Offloaded Architecture Browser-Native WebGPU Autograd Deep Learning Engine", "ko": "서버 비용 없는 브라우저 네이티브 WebGPU 딥러닝 & 자동미분(Autograd) 엔진", "ja": "サーバー費用ゼロのブラウザネイティブWebGPU深層学習＆自動微分エンジン", "zh": "零服务器成本的浏览器原生 WebGPU 自动求导与深度学习引擎", "ar": "محرك التعلم العميق والمشتقات التلقائية WebGPU الأصلي في المتصفح بدون تكلفة خادم", "fr": "Moteur d'apprentissage profond et d'autodifférenciation WebGPU natif pour navigateur à coût serveur nul", "de": "Serverlose Browser-native WebGPU-Autograd-Deep-Learning-Engine", "es": "Motor de aprendizaje profundo y autograd WebGPU nativo del navegador sin costo de servidor", "hi": "ज़ीरो-सर्वर-लागत ब्राउज़र-मूल WebGPU ऑटोग्रै드 डीप लर्निंग इंजन", "ru": "Браузерный движок глубокого обучения WebGPU без затрат на сервер", "vi": "Công cụ học sâu WebGPU Autograd gốc trên trình duyệt không tốn chi phí máy chủ", "pl": "Natywny silnik uczenia głębokiego WebGPU i autogradu w przeglądarce bez kosztów serwera", "la": "Machina WebGPU nativa in navigatro sine pretio ministri"}}, "sentinel": {"brand": "AMEVA-Sentinel", "title": "AMEVA-Sentinel", "subtitles": {"en": "Privacy-first Security Observability and Deterministic Threat Scoring Layer for Web Applications", "ko": "웹 애플리케이션을 위한 프라이버시 우선 보안 관측성 및 결정론적 0~100 위협 스코어링 엔진", "ja": "Webアプリケーション向けプライバシー優先セキュリティ観測および決定論的脅威スコアリング層", "zh": "适用于 Web 应用的隐私优先安全可观测性与确定性威胁评分层", "ar": "طبقة مراقبة أمنية تعطي الأولوية للخصوصية وتسجيل التهديدات لتطبيقات الويب", "fr": "Couche d'observabilité de la sécurité et d'évaluation des menaces axée sur la confidentialité", "de": "Datenschutzorientierte Sicherheitsbeobachtbarkeit und Bedrohungsbewertung für Webanwendungen", "es": "Capa de observabilidad de seguridad y puntuación de amenazas que prioriza la privacidad", "hi": "वेब अनुप्रयोगों के लिए गोपनीयता-प्रथम सुरक्षा अवलोकन और खतरा स्कोरिंग परत", "ru": "Конфиденциальный уровень наблюдения за безопасностью и оценки угроз для веб-приложений", "vi": "Lớp quan sát bảo mật và chấm điểm mối đe dọa ưu tiên quyền riêng tư cho ứng dụng web", "pl": "Warstwa obserwowalności bezpieczeństwa i oceny zagrożeń zorientowana na prywatność", "la": "Stratum securitatis et computatio periculorum pro applicationibus interretialibus"}}, "foundation": {"brand": "AMEVA Open-Source Foundation", "title": "AMEVA 오픈소스 재단 (AOSF)", "subtitles": {"en": "Democratizing On-Device AI & Autonomous Systems Without Cloud Egress Dependency", "ko": "클라우드 종속성 없는 소버린 온디바이스 AI 및 자율 소프트웨어 생태계의 대중화", "ja": "クラウド依存のないソブリンオンデバイスAIおよび自律ソフトウェアエコシステムの民主化", "zh": "无云端依赖的 端侧自主 AI 与自主软件生态系统普惠化", "ar": "إتاحة الذكاء الاصطناعي على الأجهزة المحمولة والأنظمة المستقلة بدون ضرائب سحابية", "fr": "Démocratiser l'IA sur appareil et les systèmes autonomes sans taxe cloud", "de": "Demokratisierung von On-Device-KI und autonomen Systemen ohne Cloud-Steuer", "es": "Democratización de la IA en el dispositivo y los sistemas autónomos sin impuestos en la nube", "hi": "क्लाउड टैक्स के बिना ऑन-डिवाइस AI और स्वायत्त प्रणालियों का लोकतंत्रीकरण", "ru": "Демократизация локального ИИ и автономных систем без облачных подписок", "vi": "Phổ cập AI trên thiết bị & hệ thống tự trị mà không cần phí đám mây", "pl": "Demokratyzacja lokalnej sztucznej inteligencji i systemów autonomicznych bez opłat chmurowych", "la": "Democratizatio AI in apparatu et systematum autonomorum sine vectigali nubis"}}};
      const meta = metaMap[ctx] || metaMap['foundation'];

      // 1. Explicit [data-i18n] element translation
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');

        // Context-aware Header Brand & Page Title overrides for libraries
        if (ctx !== 'foundation') {
          if (key === 'common.brand' || key === 'common.headerTitle') {
            el.textContent = meta.brand;
            return;
          }
          if (key === 'home.title' || key === 'home.heroTitle') {
            el.textContent = meta.title;
            return;
          }
          if (key === 'home.subtitle' || key === 'home.heroSubtitle') {
            el.textContent = meta.subtitles[lang] || meta.subtitles['en'] || meta.subtitles['ko'];
            return;
          }
        }

        const val = this._lookup(dict, key);
        if (val !== undefined && val !== null && typeof val === 'string') {
          el.textContent = val;
        }
      });

      document.querySelectorAll('[data-i18n-html]').forEach(el => {
        const key = el.getAttribute('data-i18n-html');
        const val = this._lookup(dict, key);
        if (val !== undefined && val !== null && typeof val === 'string') {
          el.innerHTML = val;
        }
      });

      // 2. Intelligent Body, Table Header, Alert & Subtitle Universal Translator
      const targetTags = ['h1', 'h2', 'h3', 'h4', 'th', 'span.alert-title', 'p.subtitle', 'td', 'div.alert > p'];
      document.querySelectorAll(targetTags.join(',')).forEach(el => {
        if (el.querySelector('pre, code, input, select, textarea')) return;
        
        let original = origTextMap.get(el);
        if (!original) {
          original = el.innerText.trim();
          origTextMap.set(el, original);
        }

        if (original && PHRASE_MAP[original]) {
          const transObj = PHRASE_MAP[original];
          const targetTrans = (lang === 'en') ? original : (transObj[lang] || transObj['en'] || original);
          if (targetTrans && el.innerText.trim() !== targetTrans) {
            el.innerText = targetTrans;
          }
        }
      });

      // Update lang dropdowns
      document.querySelectorAll('.lang-select').forEach(sel => {
        sel.value = lang;
      });
    }

    _lookup(dict, keyPath) {
      if (!keyPath || !dict) return undefined;
      const parts = keyPath.split('.');
      let cur = dict;
      for (let i = 0; i < parts.length; i++) {
        if (cur === undefined || cur === null) return undefined;
        cur = cur[parts[i]];
      }
      return cur;
    }

    _setupLanguageSelectors() {
      const optionsHtml = Object.values(SUPPORTED_LANGUAGES).map(l => 
        `<option value="${l.code}">${l.flag} ${l.nativeName}</option>`
      ).join('');

      // Auto-populate empty wrappers
      if (typeof document !== 'undefined') {
        document.querySelectorAll('.lang-selector-wrapper').forEach(wrap => {
          if (!wrap.querySelector('.lang-select')) {
            const sel = document.createElement('select');
            sel.className = 'lang-select';
            sel.setAttribute('aria-label', 'Language Selector');
            sel.innerHTML = optionsHtml;
            wrap.appendChild(sel);
          }
        });

        // Fallback: If no wrapper exists, check header .header-controls
        const existingSelects = document.querySelectorAll('.lang-select');
        if (existingSelects.length === 0) {
          const controls = document.querySelector('header .header-controls');
          if (controls) {
            const wrap = document.createElement('div');
            wrap.className = 'lang-selector-wrapper';
            const sel = document.createElement('select');
            sel.className = 'lang-select';
            sel.setAttribute('aria-label', 'Language Selector');
            sel.innerHTML = optionsHtml;
            wrap.appendChild(sel);
            controls.insertBefore(wrap, controls.firstChild);
          }
        }

        document.querySelectorAll('.lang-select').forEach(sel => {
          if (!sel.children.length || sel.children.length < 10) {
            sel.innerHTML = optionsHtml;
          }
          sel.value = this.currentLang;
          sel.onchange = (e) => {
            this.setLanguage(e.target.value);
          };
        });
      }
    }

    _setupCodeCopyButtons() {
      document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.onclick = function() {
          const block = btn.closest('.code-block');
          const codeEl = block ? block.querySelector('code') : null;
          if (codeEl) {
            navigator.clipboard.writeText(codeEl.innerText).then(() => {
              const orig = btn.innerText;
              btn.innerText = 'Copied!';
              btn.classList.add('copied');
              setTimeout(() => {
                btn.innerText = orig;
                btn.classList.remove('copied');
              }, 2000);
            });
          }
        };
      });
    }

    _setupTabs() {
      document.querySelectorAll('.tab-group').forEach(group => {
        const tabs = group.querySelectorAll('.tab-btn');
        const panels = group.querySelectorAll('.tab-panel');
        tabs.forEach(tab => {
          tab.onclick = function() {
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const target = group.querySelector('#' + tab.getAttribute('data-tab'));
            if (target) target.classList.add('active');
          };
        });
      });
    }
  }

  const instance = new I18nManager();
  global.i18nManager = instance;
  global.I18n = {
    setLanguage: function(l) { instance.setLanguage(l); },
    getLanguage: function() { return instance.currentLang; }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => instance.init());
  } else {
    instance.init();
  }

})(typeof window !== 'undefined' ? window : global);
