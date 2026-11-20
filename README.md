# State of the Art of WebAI

A map of everything between a model and a person when the model runs in a browser, on a phone or on an edge board: choosing and adapting the model, converting and quantizing it, running it, putting it inside an app, and testing it.

It is an awesome list and a landscape in one picture. Every chip is a technology, a technique or a limit, and every chip links to the sources it rests on, with the date they were read.

![The five layers of WebAI](docs/figure-en.png)

**Live page:** `docs/index.html` (static; switch language with the buttons or `?lang=pt`, theme with the sun and moon buttons). [Português](README.pt.md).

## How it works

| File | What it is |
|---|---|
| [SPEC.md](SPEC.md) | The specification (version 0.1): data model, rules, i18n, curation, versioning. |
| `data/layers.yml` | The layers, groups and chips. Each chip has `source` (one link) or `sources` (a tree of links). |
| `i18n/en.yml`, `i18n/pt.yml` | One text per id. English is the reference language. |
| `schema/` | JSON Schemas for the two kinds of file. |
| `assets/` | CSS, the small script, and the icons (SVG). |
| `build.py` | Builds `docs/index.html` and refreshes the list below. |
| `export.py` | Exports a PNG per language with headless Chrome. |
| `scripts/check.py` | Validates the data and the translations against the spec. CI runs it. |

```sh
python3 scripts/check.py   # validate
python3 build.py           # docs/index.html and the list below
python3 export.py          # docs/figure-<lang>.png (needs Chrome or Chromium)
```

Python 3.10+ is enough (PyYAML is used if installed, otherwise a tiny built-in reader handles the files).

## Contributing

Add a chip, fix a source, or translate the whole map. See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: no chip without a source, and every text lives in `i18n/`.

## Open items

Chips from earlier drafts waiting for a good source: base model, narrow task, per-device measurement, regression tests, streaming. Pull requests with a source are welcome.

## License

Code: MIT ([LICENSE-CODE](LICENSE-CODE)). Data and texts: CC BY 4.0 ([LICENSE-DATA](LICENSE-DATA)).

## The list

<!-- awesome:start -->
_79 chips, 107 source links. Last reviewed: 2026-11-19. Generated from `data/layers.yml`: do not edit by hand._

### 1. Choose and adapt
_Which task, which base?_

**Starting point**

- [open weights](https://huggingface.co/HuggingFaceTB/SmolLM3-3B) — Weights published openly, so they can be adapted, converted and shipped; SmolLM3-3B is Apache-2.0.
- [short context](https://huggingface.co/blog/kv-cache-quantization) — A short context keeps the KV cache small; the cache grows with every token kept.

**Adapt**

- [LoRA](https://arxiv.org/abs/2106.09685) — Freezes the base weights and trains small low-rank matrices, with no extra latency at inference.
- [QLoRA](https://arxiv.org/abs/2305.14314) — LoRA on a model frozen in 4 bits; fine-tunes a 65B model on a single 48 GB GPU.
- **distillation** — Squeezes a larger model into a smaller one; DistilBERT is 40% smaller and 60% faster.
  - Papers: [Distilling the knowledge in a neural network](https://arxiv.org/abs/1503.02531), [DistilBERT](https://arxiv.org/abs/1910.01108)

### 2. Convert and quantize
_How low can I go?_

**Format**

- [ONNX](https://onnxruntime.ai/docs/tutorials/web/) — Open graph format that ONNX Runtime executes in the browser and natively.
- [GGUF](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md) — File format for GGML-based runtimes, designed for fast loading with mmap.
- [MLC](https://github.com/mlc-ai/web-llm) — Model packaging used by MLC and WebLLM to run on WebGPU.
- [.tflite](https://ai.google.dev/edge/litert) — Model format of LiteRT, formerly TensorFlow Lite, for on-device inference.
- [Core ML](https://developer.apple.com/documentation/coreml) — Apple's model format for on-device inference; coremltools quantizes weights and activations.

**Precision**

- [fp32](https://cloud.google.com/blog/products/ai-machine-learning/bfloat16-the-secret-to-high-performance-on-cloud-tpus) — 32-bit floating point: 4 bytes per parameter.
- [fp16](https://en.wikipedia.org/wiki/Half-precision_floating-point_format) — 16-bit IEEE float with a 5-bit exponent, range up to ±65,504.
- [bf16](https://cloud.google.com/blog/products/ai-machine-learning/bfloat16-the-secret-to-high-performance-on-cloud-tpus) — 16-bit brain float: fp32's range with 7 mantissa bits, so less precision.
- [int8](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — 8-bit integers with a scale and zero point: value = scale × (quantized − zero point).
- [int4](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — 4-bit weights: a 4× reduction in size compared with BF16.

**Method**

- [RTN](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — Round-to-nearest, the default 4-bit algorithm in ONNX Runtime, applied block by block.
- [GPTQ](https://arxiv.org/abs/2210.17323) — Calibrates 3 to 4 bit weights in one shot with second-order information; handles 175B models.
- [AWQ](https://arxiv.org/abs/2306.00978) — Protects the most important weight channels, chosen by activations.
- [HQQ](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — A weight quantization algorithm ONNX Runtime offers next to RTN and GPTQ.
- [NF4](https://arxiv.org/abs/2305.14314) — 4-bit type for normally distributed weights, used by QLoRA.
- [k-quants](https://github.com/ggml-org/llama.cpp/pull/1684) — GGUF block formats with quantized scales; Q4_K uses 4.5 bits per weight.
- [QAT](https://developers.googleblog.com/en/gemma-3-quantized-aware-trained-state-of-the-art-ai-to-consumer-gpus/) — Trains the model already knowing it will be quantized; Gemma 3 ships QAT versions.

**In ONNX Runtime**

- [MatMulNBits](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — ONNX Runtime rewrites weight MatMul into MatMulNBits, with block-wise quantization.

**KV cache**

- [KIVI (2 bits)](https://arxiv.org/abs/2402.02750) — Quantizes the KV cache to 2 bits: 2.6× less peak memory, including the weights.

### 3. Run
_Which accelerator, which limit?_

**Acceleration**

- **WebGPU** — GPU access for general computation, not only graphics; in the four major browsers, with platform gaps.
  - Docs: [MDN: WebGPU API](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API)
  - Spec: [W3C: WebGPU](https://www.w3.org/TR/webgpu/)
  - Status: [web.dev: browser support](https://web.dev/blog/webgpu-supported-major-browsers)
- [WebAssembly](https://webassembly.org/features/) — SIMD and threads run on the CPU in Chrome, Firefox and Safari; threads need cross-origin isolation.
- **WebNN** · *experimental* — Low-level API for neural-network hardware (CPU, GPU, NPU); a draft that Chrome and Edge are testing.
  - Docs: [ONNX Runtime: WebNN execution provider](https://onnxruntime.ai/docs/tutorials/web/ep-webnn.html)
  - Spec: [W3C: WebNN](https://www.w3.org/TR/webnn/)
  - Status: [Chrome: origin trial](https://developer.chrome.com/blog/chrome-146-beta), [Mozilla: standards position](https://github.com/mozilla/standards-positions/issues/1215), [WebKit: standards position](https://github.com/WebKit/standards-positions/issues/486)
- [NPU](https://www.w3.org/TR/webnn/) — WebNN lets the browser choose among CPU, GPU and NPU devices.

**Execution**

- [Web Worker](https://developer.mozilla.org/en-US/docs/Web/API/Worker) — Runs inference off the main thread so the interface does not freeze.
- [Shared Worker](https://developer.mozilla.org/en-US/docs/Web/API/SharedWorker) — One worker shared by several tabs of the same origin.
- [offscreen doc](https://developer.chrome.com/docs/extensions/reference/api/offscreen) — How a Chrome extension runs work that needs a DOM, since its service worker has none.

**Runtime**

- [ONNX Runtime](https://onnxruntime.ai/) — Runs ONNX models in the browser (WebAssembly, WebGPU, WebNN) and natively.
- [llama.cpp](https://github.com/ggml-org/llama.cpp) — C/C++ inference for GGUF models, with Android and Apple Metal builds.
- [MLC](https://github.com/mlc-ai/web-llm) — The runtime behind WebLLM, running compiled models on WebGPU.
- [LiteRT](https://ai.google.dev/edge/litert) — Google's on-device runtime, formerly TensorFlow Lite; used by 250K+ apps.
- [ExecuTorch](https://github.com/pytorch/executorch) — PyTorch runtime for the edge: Android, iOS, desktop and embedded, with XNNPACK, Core ML and Vulkan backends.
- [Core ML](https://developer.apple.com/documentation/coreml) — Apple's framework for running models on a person's device.

**Cache and size**

- [per-site cache](https://developer.chrome.com/blog/http-cache-partitioning) — The HTTP cache is keyed by site, so two sites cannot reuse one downloaded file.
- **Cache API** — Chrome's recommended store for model files; WebLLM and Transformers.js use it by default.
  - Docs: [Chrome: cache AI models](https://developer.chrome.com/docs/ai/cache-models), [Transformers.js: env](https://huggingface.co/docs/transformers.js/api/env), [ONNX Runtime: large models](https://onnxruntime.ai/docs/tutorials/web/large-models.html)
  - Code: [WebLLM: cacheBackend](https://raw.githubusercontent.com/mlc-ai/web-llm/main/README.md)
- [OPFS](https://developer.mozilla.org/en-US/docs/Web/API/File_System_API/Origin_private_file_system) — Origin private file system: private storage with synchronous access inside workers.
- **shared cache (COS)** · *proposal* — Proposal: ask for a file by its hash and share it across sites. No browser ships it natively yet.
  - Docs: [Chrome: introducing Cross-Origin Storage](https://developer.chrome.com/blog/introducing-cross-origin-storage)
  - Spec: [WICG explainer](https://github.com/WICG/cross-origin-storage)
  - Posts: [Hugging Face: Cross-Origin Storage](https://huggingface.co/blog/cross-origin-storage)
  - Status: [Mozilla: standards position](https://github.com/mozilla/standards-positions/issues/1427), [WebKit: standards position](https://github.com/WebKit/standards-positions/issues/703)
- **split download** — Download a large model in parallel chunks and stitch them together on the client.
  - Docs: [Chrome: cache AI models](https://developer.chrome.com/docs/ai/cache-models), [MDN: range requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests)
- [resume download](https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests) — Range requests let a download pause and resume.
- [size budget](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — Download size is parameters × bytes per parameter: 3.08B parameters is 6.2 GB in bf16 and 1.7 GB in int4.

**Where it runs**

- [Browser](https://web.dev/blog/webgpu-supported-major-browsers) — desktop and mobile, extension, PWA, WebView
- [Desktop](https://www.electronjs.org/) — Electron, Tauri, Node
- [Mobile](https://github.com/pytorch/executorch) — iOS and Android apps
- [Edge](https://www.raspberrypi.com/products/raspberry-pi-5/) — Raspberry Pi, Jetson, Coral, microcontrollers

#### Limits

**Memory**

- **4 GB in wasm** — 32-bit WebAssembly memory tops out at 4 GB.
  - Docs: [V8: 4 GB of Wasm memory](https://v8.dev/blog/4gb-wasm-memory), [WebAssembly 3.0](https://webassembly.org/news/2025-09-17-wasm-3.0/)
- **2 GB file** — Files above 2 GB hit ArrayBuffer and protobuf limits; ONNX uses external data files.
  - Docs: [ONNX Runtime: large models](https://onnxruntime.ai/docs/tutorials/web/large-models.html)
  - Code: [wllama README](https://github.com/ngxson/wllama)
- [256 MB buffer](https://developer.mozilla.org/en-US/docs/Web/API/GPUSupportedLimits) — WebGPU's default maxBufferSize is 256 MB (storage binding 128 MB); more can be requested.
- **KV cache grows** — The KV cache grows with every token: about 72 KiB per token for SmolLM3-3B in fp16.
  - Posts: [Hugging Face: KV cache quantization](https://huggingface.co/blog/kv-cache-quantization), [NVIDIA: LLM inference optimization](https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/)

**GPU**

- [no shader-f16](https://developer.chrome.com/blog/new-in-webgpu-120) — The shader-f16 feature is optional, so half-precision kernels may be unavailable.
- **device lost** — The GPU device can be lost; handle the lost promise and recover.
  - Docs: [MDN: GPUDevice.lost](https://developer.mozilla.org/en-US/docs/Web/API/GPUDevice/lost)
  - Code: [WebLLM issue 517](https://github.com/mlc-ai/web-llm/issues/517)
- [raise limits](https://developer.mozilla.org/en-US/docs/Web/API/GPUAdapter/requestDevice) — Ask for higher limits with requiredLimits when requesting the device.
- [availability](https://web.dev/blog/webgpu-supported-major-browsers) — WebGPU availability varies by browser and platform.

**Disk and network**

- **origin quota** — Browsers manage storage per origin; the quota depends on the engine and the disk.
  - Docs: [MDN: quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), [web.dev: storage for the web](https://web.dev/articles/storage-for-the-web)
- [eviction](https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/persist) — Stored data can be evicted, least recently used first, unless the origin asked for persistence.
- **persist()** — navigator.storage.persist() asks the browser not to evict your origin's data.
  - Docs: [MDN: StorageManager.persist](https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/persist), [MDN: quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria)

**Isolation**

- **COOP and COEP** — Cross-origin isolation is required for WebAssembly threads.
  - Docs: [MDN: crossOriginIsolated](https://developer.mozilla.org/en-US/docs/Web/API/Window/crossOriginIsolated), [ONNX Runtime: env flags](https://onnxruntime.ai/docs/tutorials/web/env-flags-and-session-options.html)

### 4. Integrate in the app
_No GPU, now what?_

**Web library**

- [ONNX Runtime Web](https://onnxruntime.ai/docs/tutorials/web/) — ONNX Runtime for the browser, with WebGPU, WebAssembly and WebNN backends.
- [Transformers.js](https://huggingface.co/docs/transformers.js/index) — Hugging Face's JavaScript library; caches models with the Cache API by default.
- [WebLLM](https://github.com/mlc-ai/web-llm) — In-browser LLM engine on WebGPU, with Chrome extension support and several cache backends.
- [wllama](https://github.com/ngxson/wllama) — WebAssembly bindings for llama.cpp; split models into chunks of up to 512 MB.
- [TensorFlow.js](https://github.com/tensorflow/tfjs) — Machine learning in JavaScript, in the browser and in Node.
- [LiteRT.js](https://ai.google.dev/edge/litert/web) — LiteRT for the web, from Google AI Edge.

**Packaging**

- [extension](https://github.com/mlc-ai/web-llm) — Browser extensions can run models; WebLLM supports Chrome extensions.
- [PWA](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps) — Installable web apps that keep working offline.

**Experience**

- [loading screen](https://developer.chrome.com/docs/ai/built-in) — Tell people the model is downloading; Chrome documents how to inform users.
- **no-GPU fallback** — WebGPU is experimental in some browsers; a WebAssembly path can run where it fails.
  - Docs: [Transformers.js: WebGPU guide](https://huggingface.co/docs/transformers.js/guides/webgpu), [ONNX Runtime Web: tutorials](https://onnxruntime.ai/docs/tutorials/web/)
- **structured output** — Grammar-constrained decoding forces valid JSON or another format.
  - Code: [llama.cpp: grammars](https://github.com/ggml-org/llama.cpp)
  - Papers: [XGrammar paper](https://arxiv.org/abs/2411.15100)

**Browser API**

- **Prompt API (Gemini Nano)** — Prompt a model the browser downloads and manages for you; status varies by context, see the page.
  - Docs: [Chrome: Prompt API](https://developer.chrome.com/docs/ai/prompt-api), [Chrome: built-in model management](https://developer.chrome.com/docs/ai/understand-built-in-model-management), [Chrome: built-in AI APIs](https://developer.chrome.com/docs/ai/built-in-apis)
- [Summarizer](https://developer.chrome.com/docs/ai/built-in-apis) · *stable* — Built-in browser API that summarizes text; the browser manages the model.
- [Translator](https://developer.chrome.com/docs/ai/built-in-apis) · *stable* — Built-in browser API that translates text; the browser manages the model.

**Native SDK**

- [AICore (Gemini Nano)](https://developer.android.com/ai/gemini-nano) — Android system service that runs Gemini Nano and keeps the model up to date.
- [Foundation Models](https://developer.apple.com/documentation/foundationmodels) — Apple's access to on-device and Private Cloud Compute models, with guided generation and tool calling.
- [ML Kit GenAI](https://developer.android.com/ai/gemini-nano) — ML Kit GenAI APIs on Android use AICore and process data locally.
- [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference) — The LLM Inference page now points to LiteRT-LM.
- **LiteRT-LM** — LLMs on Linux, macOS, Windows and Raspberry Pi through a CLI; supports speculative decoding.
  - Docs: [LiteRT-LM overview](https://ai.google.dev/edge/litert-lm/overview)
  - Code: [LiteRT-LM on GitHub](https://github.com/google-ai-edge/LiteRT-LM)

### 5. Evaluate and test
_Same as the original?_

**Quality**

- [fidelity](https://developers.googleblog.com/en/gemma-3-quantized-aware-trained-state-of-the-art-ai-to-consumer-gpus/) — Quantization can degrade performance, so measure the quantized model against the original.
- [operator coverage](https://onnxruntime.ai/docs/tutorials/web/) — WebGPU, WebGL and WebNN support only a subset of ONNX operators; WebAssembly supports all.

**Performance**

- **battery** · *open* — Papers measure phone energy; no comparable, agreed measurement exists yet.
  - Papers: [On-device vs server energy](https://arxiv.org/abs/2609.11940), [Phone battery and launch time](https://arxiv.org/abs/2410.03613)
- [background tab](https://developer.chrome.com/blog/timer-throttling-in-chrome-88) — Background tabs are throttled; timers slow down in Chrome 88 and later.
<!-- awesome:end -->
