# State of the Art of WebAI

Um mapa de tudo o que existe entre um modelo e uma pessoa quando o modelo roda no navegador, no celular ou numa placa de borda: escolher e adaptar o modelo, converter e quantizar, rodar, integrar no app e testar.

É uma lista "awesome" e uma paisagem (landscape) numa figura só. Cada chip é uma tecnologia, técnica ou limite e leva às fontes em que se apoia, com a data em que foram lidas.

![As cinco camadas do WebAI](docs/figure-pt.png)

**Página:** `docs/index.html` (estática; troque o idioma pelos botões ou `?lang=pt`, e o tema pelos botões de sol e lua). [English](README.md).

## Como funciona

| Arquivo | O que é |
|---|---|
| [SPEC.md](SPEC.md) | A especificação (versão 0.1), em inglês: modelo de dados, regras, i18n, curadoria, versionamento. |
| `data/layers.yml` | As camadas, grupos e chips. Cada chip tem `source` (um link) ou `sources` (uma árvore de links). |
| `i18n/en.yml`, `i18n/pt.yml` | Um texto por id. O inglês é o idioma de referência. |
| `schema/` | JSON Schemas dos dois tipos de arquivo. |
| `build.py` | Gera `docs/index.html` e atualiza a lista abaixo. |
| `export.py` | Exporta um PNG por idioma com Chrome headless. |
| `scripts/check.py` | Valida os dados e as traduções contra a especificação. O CI roda. |

```sh
python3 scripts/check.py   # validar
python3 build.py           # docs/index.html e a lista abaixo
python3 export.py          # docs/figure-<idioma>.png (precisa de Chrome ou Chromium)
```

## Contribuir

Adicione um chip, corrija uma fonte ou traduza o mapa inteiro. Veja o [CONTRIBUTING.md](CONTRIBUTING.md) (em inglês). Em resumo: nenhum chip sem fonte, e todo texto fica em `i18n/`. Para um idioma novo, copie `i18n/en.yml` para `i18n/<idioma>.yml` e traduza os valores; `python3 scripts/check.py` lista o que falta.

## Itens em aberto

Chips de rascunhos anteriores que aguardam uma boa fonte: modelo base, tarefa estreita, medida por aparelho, testes de regressão, streaming. Pull requests com fonte são bem-vindos.

## Licença

Código: MIT ([LICENSE-CODE](LICENSE-CODE)). Dados e textos: CC BY 4.0 ([LICENSE-DATA](LICENSE-DATA)).

## A lista

<!-- awesome:start -->
_79 chips, 107 links de fonte. Última revisão: 2026-11-19. Gerado a partir de `data/layers.yml`: não edite à mão._

### 1. Escolher e adaptar
_Qual tarefa e qual base?_

**Ponto de partida**

- [pesos abertos](https://huggingface.co/HuggingFaceTB/SmolLM3-3B) — Pesos publicados abertamente, que podem ser adaptados, convertidos e distribuídos; o SmolLM3-3B é Apache-2.0.
- [contexto curto](https://huggingface.co/blog/kv-cache-quantization) — Contexto curto mantém o cache KV pequeno; o cache cresce a cada token guardado.

**Adaptar**

- [LoRA](https://arxiv.org/abs/2106.09685) — Congela os pesos base e treina pequenas matrizes de baixo posto, sem latência extra na inferência.
- [QLoRA](https://arxiv.org/abs/2305.14314) — LoRA sobre um modelo congelado em 4 bits; ajusta um modelo de 65B numa única GPU de 48 GB.
- **destilação** — Espreme um modelo maior num menor; o DistilBERT é 40% menor e 60% mais rápido.
  - Artigos: [Distilling the knowledge in a neural network](https://arxiv.org/abs/1503.02531), [DistilBERT](https://arxiv.org/abs/1910.01108)

### 2. Converter e quantizar
_Qual precisão?_

**Formato**

- [ONNX](https://onnxruntime.ai/docs/tutorials/web/) — Formato aberto de grafo que o ONNX Runtime executa no navegador e em plataformas nativas.
- [GGUF](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md) — Formato de arquivo para runtimes baseados em GGML, feito para carregar rápido com mmap.
- [MLC](https://github.com/mlc-ai/web-llm) — Empacotamento de modelo usado pelo MLC e pelo WebLLM para rodar em WebGPU.
- [.tflite](https://ai.google.dev/edge/litert) — Formato de modelo do LiteRT, antigo TensorFlow Lite, para inferência no aparelho.
- [Core ML](https://developer.apple.com/documentation/coreml) — Formato de modelo da Apple para inferência no aparelho; o coremltools quantiza pesos e ativações.

**Precisão**

- [fp32](https://cloud.google.com/blog/products/ai-machine-learning/bfloat16-the-secret-to-high-performance-on-cloud-tpus) — Ponto flutuante de 32 bits: 4 bytes por parâmetro.
- [fp16](https://en.wikipedia.org/wiki/Half-precision_floating-point_format) — Float IEEE de 16 bits com expoente de 5 bits, faixa até ±65.504.
- [bf16](https://cloud.google.com/blog/products/ai-machine-learning/bfloat16-the-secret-to-high-performance-on-cloud-tpus) — Brain float de 16 bits: a faixa do fp32 com 7 bits de mantissa, logo menos precisão.
- [int8](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — Inteiros de 8 bits com escala e ponto zero: valor = escala × (quantizado − ponto zero).
- [int4](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — Pesos de 4 bits: redução de 4× no tamanho em relação ao BF16.

**Método**

- [RTN](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — Arredondamento ao mais próximo, o algoritmo de 4 bits padrão do ONNX Runtime, aplicado por bloco.
- [GPTQ](https://arxiv.org/abs/2210.17323) — Calibra pesos de 3 a 4 bits de uma vez com informação de segunda ordem; aguenta modelos de 175B.
- [AWQ](https://arxiv.org/abs/2306.00978) — Protege os canais de pesos mais importantes, escolhidos pela ativação.
- [HQQ](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — Algoritmo de quantização de pesos que o ONNX Runtime oferece ao lado de RTN e GPTQ.
- [NF4](https://arxiv.org/abs/2305.14314) — Tipo de 4 bits para pesos de distribuição normal, usado pelo QLoRA.
- [k-quants](https://github.com/ggml-org/llama.cpp/pull/1684) — Formatos de bloco do GGUF com escalas quantizadas; o Q4_K usa 4,5 bits por peso.
- [QAT](https://developers.googleblog.com/en/gemma-3-quantized-aware-trained-state-of-the-art-ai-to-consumer-gpus/) — Treina o modelo já sabendo que será quantizado; o Gemma 3 tem versões com QAT.

**No ONNX Runtime**

- [MatMulNBits](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — O ONNX Runtime reescreve o MatMul de pesos em MatMulNBits, com quantização por blocos.

**Cache KV**

- [KIVI (2 bits)](https://arxiv.org/abs/2402.02750) — Quantiza o cache KV em 2 bits: 2,6× menos memória de pico, contando os pesos.

### 3. Rodar
_Qual aceleração, qual limite?_

**Aceleração**

- **WebGPU** — Acesso à GPU para computação geral, não só gráficos; nos quatro navegadores principais, com lacunas por plataforma.
  - Documentação: [MDN: WebGPU API](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API)
  - Especificação: [W3C: WebGPU](https://www.w3.org/TR/webgpu/)
  - Estado: [web.dev: browser support](https://web.dev/blog/webgpu-supported-major-browsers)
- [WebAssembly](https://webassembly.org/features/) — SIMD e threads rodam na CPU no Chrome, Firefox e Safari; threads pedem isolamento de origem cruzada.
- **WebNN** · *experimental* — API de baixo nível para hardware de redes neurais (CPU, GPU, NPU); rascunho que Chrome e Edge testam.
  - Documentação: [ONNX Runtime: WebNN execution provider](https://onnxruntime.ai/docs/tutorials/web/ep-webnn.html)
  - Especificação: [W3C: WebNN](https://www.w3.org/TR/webnn/)
  - Estado: [Chrome: origin trial](https://developer.chrome.com/blog/chrome-146-beta), [Mozilla: standards position](https://github.com/mozilla/standards-positions/issues/1215), [WebKit: standards position](https://github.com/WebKit/standards-positions/issues/486)
- [NPU](https://www.w3.org/TR/webnn/) — O WebNN deixa o navegador escolher entre dispositivos de CPU, GPU e NPU.

**Execução**

- [Web Worker](https://developer.mozilla.org/en-US/docs/Web/API/Worker) — Roda a inferência fora da thread principal, para a interface não travar.
- [Shared Worker](https://developer.mozilla.org/en-US/docs/Web/API/SharedWorker) — Um worker compartilhado por várias abas da mesma origem.
- [doc. offscreen](https://developer.chrome.com/docs/extensions/reference/api/offscreen) — Como uma extensão do Chrome roda trabalho que precisa de DOM, já que o service worker não tem.

**Runtime**

- [ONNX Runtime](https://onnxruntime.ai/) — Roda modelos ONNX no navegador (WebAssembly, WebGPU, WebNN) e em plataformas nativas.
- [llama.cpp](https://github.com/ggml-org/llama.cpp) — Inferência em C/C++ para modelos GGUF, com builds para Android e Metal da Apple.
- [MLC](https://github.com/mlc-ai/web-llm) — O runtime por trás do WebLLM, que roda modelos compilados em WebGPU.
- [LiteRT](https://ai.google.dev/edge/litert) — Runtime do Google para o aparelho, antigo TensorFlow Lite; usado por mais de 250 mil apps.
- [ExecuTorch](https://github.com/pytorch/executorch) — Runtime do PyTorch para a borda: Android, iOS, desktop e embarcados, com backends XNNPACK, Core ML e Vulkan.
- [Core ML](https://developer.apple.com/documentation/coreml) — Framework da Apple para rodar modelos no aparelho da pessoa.

**Cache e tamanho**

- [cache por site](https://developer.chrome.com/blog/http-cache-partitioning) — O cache HTTP é separado por site, então dois sites não reaproveitam o mesmo arquivo baixado.
- **Cache API** — O armazenamento que o Chrome recomenda para arquivos de modelo; WebLLM e Transformers.js o usam por padrão.
  - Documentação: [Chrome: cache AI models](https://developer.chrome.com/docs/ai/cache-models), [Transformers.js: env](https://huggingface.co/docs/transformers.js/api/env), [ONNX Runtime: large models](https://onnxruntime.ai/docs/tutorials/web/large-models.html)
  - Código: [WebLLM: cacheBackend](https://raw.githubusercontent.com/mlc-ai/web-llm/main/README.md)
- [OPFS](https://developer.mozilla.org/en-US/docs/Web/API/File_System_API/Origin_private_file_system) — Sistema de arquivos privado da origem, com acesso síncrono dentro de workers.
- **cache compartilhado (COS)** · *proposta* — Proposta: pedir o arquivo pelo hash e compartilhá-lo entre sites. Nenhum navegador o tem de forma nativa ainda.
  - Documentação: [Chrome: introducing Cross-Origin Storage](https://developer.chrome.com/blog/introducing-cross-origin-storage)
  - Especificação: [WICG explainer](https://github.com/WICG/cross-origin-storage)
  - Posts: [Hugging Face: Cross-Origin Storage](https://huggingface.co/blog/cross-origin-storage)
  - Estado: [Mozilla: standards position](https://github.com/mozilla/standards-positions/issues/1427), [WebKit: standards position](https://github.com/WebKit/standards-positions/issues/703)
- **baixar em partes** — Baixa um modelo grande em partes paralelas e junta tudo no cliente.
  - Documentação: [Chrome: cache AI models](https://developer.chrome.com/docs/ai/cache-models), [MDN: range requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests)
- [retomar download](https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests) — Requisições de faixa (Range) permitem pausar e retomar um download.
- [orçar download](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) — O download é parâmetros × bytes por parâmetro: 3,08 bi de parâmetros são 6,2 GB em bf16 e 1,7 GB em int4.

**Onde roda**

- [Navegador](https://web.dev/blog/webgpu-supported-major-browsers) — desktop e celular, extensão, PWA, WebView
- [Desktop](https://www.electronjs.org/) — Electron, Tauri, Node
- [Celular](https://github.com/pytorch/executorch) — app iOS e Android
- [Borda](https://www.raspberrypi.com/products/raspberry-pi-5/) — Raspberry Pi, Jetson, Coral, microcontroladores

#### Limites

**Memória**

- **4 GB no wasm** — A memória do WebAssembly de 32 bits chega no máximo a 4 GB.
  - Documentação: [V8: 4 GB of Wasm memory](https://v8.dev/blog/4gb-wasm-memory), [WebAssembly 3.0](https://webassembly.org/news/2025-09-17-wasm-3.0/)
- **arquivo de 2 GB** — Arquivos acima de 2 GB esbarram nos limites de ArrayBuffer e protobuf; o ONNX usa arquivos de dados externos.
  - Documentação: [ONNX Runtime: large models](https://onnxruntime.ai/docs/tutorials/web/large-models.html)
  - Código: [wllama README](https://github.com/ngxson/wllama)
- [buffer de 256 MB](https://developer.mozilla.org/en-US/docs/Web/API/GPUSupportedLimits) — O maxBufferSize padrão do WebGPU é 256 MB (binding de armazenamento, 128 MB); dá para pedir mais.
- **cache KV cresce** — O cache KV cresce a cada token: cerca de 72 KiB por token no SmolLM3-3B em fp16.
  - Posts: [Hugging Face: KV cache quantization](https://huggingface.co/blog/kv-cache-quantization), [NVIDIA: LLM inference optimization](https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/)

**GPU**

- [sem shader-f16](https://developer.chrome.com/blog/new-in-webgpu-120) — O recurso shader-f16 é opcional, então kernels de meia precisão podem não estar disponíveis.
- **device lost** — O dispositivo de GPU pode ser perdido; trate a promessa lost e se recupere.
  - Documentação: [MDN: GPUDevice.lost](https://developer.mozilla.org/en-US/docs/Web/API/GPUDevice/lost)
  - Código: [WebLLM issue 517](https://github.com/mlc-ai/web-llm/issues/517)
- [subir limite](https://developer.mozilla.org/en-US/docs/Web/API/GPUAdapter/requestDevice) — Peça limites maiores com requiredLimits ao pedir o dispositivo.
- [disponibilidade](https://web.dev/blog/webgpu-supported-major-browsers) — A disponibilidade do WebGPU varia por navegador e plataforma.

**Disco e rede**

- **cota da origem** — Os navegadores gerenciam o armazenamento por origem; a cota depende do motor e do disco.
  - Documentação: [MDN: quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), [web.dev: storage for the web](https://web.dev/articles/storage-for-the-web)
- [despejo](https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/persist) — Dados guardados podem ser despejados, os menos usados primeiro, a menos que a origem peça persistência.
- **persist()** — navigator.storage.persist() pede ao navegador que não despeje os dados da sua origem.
  - Documentação: [MDN: StorageManager.persist](https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/persist), [MDN: quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria)

**Isolamento**

- **COOP e COEP** — O isolamento de origem cruzada é necessário para threads de WebAssembly.
  - Documentação: [MDN: crossOriginIsolated](https://developer.mozilla.org/en-US/docs/Web/API/Window/crossOriginIsolated), [ONNX Runtime: env flags](https://onnxruntime.ai/docs/tutorials/web/env-flags-and-session-options.html)

### 4. Integrar no app
_E se não houver GPU?_

**Biblioteca web**

- [ONNX Runtime Web](https://onnxruntime.ai/docs/tutorials/web/) — ONNX Runtime para o navegador, com backends WebGPU, WebAssembly e WebNN.
- [Transformers.js](https://huggingface.co/docs/transformers.js/index) — Biblioteca JavaScript da Hugging Face; guarda os modelos na Cache API por padrão.
- [WebLLM](https://github.com/mlc-ai/web-llm) — Motor de LLM no navegador sobre WebGPU, com suporte a extensões do Chrome e vários backends de cache.
- [wllama](https://github.com/ngxson/wllama) — Bindings de WebAssembly para o llama.cpp; divida os modelos em partes de até 512 MB.
- [TensorFlow.js](https://github.com/tensorflow/tfjs) — Aprendizado de máquina em JavaScript, no navegador e no Node.
- [LiteRT.js](https://ai.google.dev/edge/litert/web) — LiteRT para a web, do Google AI Edge.

**Empacotamento**

- [extensão](https://github.com/mlc-ai/web-llm) — Extensões de navegador podem rodar modelos; o WebLLM tem suporte a extensões do Chrome.
- [PWA](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps) — Apps web instaláveis que continuam funcionando offline.

**Experiência**

- [tela de carga](https://developer.chrome.com/docs/ai/built-in) — Avise que o modelo está baixando; o Chrome documenta como informar o usuário.
- **plano B sem GPU** — O WebGPU ainda é experimental em alguns navegadores; um caminho em WebAssembly roda onde ele falha.
  - Documentação: [Transformers.js: WebGPU guide](https://huggingface.co/docs/transformers.js/guides/webgpu), [ONNX Runtime Web: tutorials](https://onnxruntime.ai/docs/tutorials/web/)
- **saída estruturada** — A decodificação restrita por gramática força JSON válido ou outro formato.
  - Código: [llama.cpp: grammars](https://github.com/ggml-org/llama.cpp)
  - Artigos: [XGrammar paper](https://arxiv.org/abs/2411.15100)

**API do navegador**

- **Prompt API (Gemini Nano)** — Use um modelo que o navegador baixa e gerencia por você; o estado varia por contexto, veja a página.
  - Documentação: [Chrome: Prompt API](https://developer.chrome.com/docs/ai/prompt-api), [Chrome: built-in model management](https://developer.chrome.com/docs/ai/understand-built-in-model-management), [Chrome: built-in AI APIs](https://developer.chrome.com/docs/ai/built-in-apis)
- [Summarizer](https://developer.chrome.com/docs/ai/built-in-apis) · *estável* — API embutida do navegador que resume texto; o navegador gerencia o modelo.
- [Translator](https://developer.chrome.com/docs/ai/built-in-apis) · *estável* — API embutida do navegador que traduz texto; o navegador gerencia o modelo.

**SDK nativo**

- [AICore (Gemini Nano)](https://developer.android.com/ai/gemini-nano) — Serviço do sistema Android que roda o Gemini Nano e mantém o modelo atualizado.
- [Foundation Models](https://developer.apple.com/documentation/foundationmodels) — Acesso da Apple aos modelos no aparelho e no Private Cloud Compute, com geração guiada e chamada de ferramentas.
- [ML Kit GenAI](https://developer.android.com/ai/gemini-nano) — As APIs GenAI do ML Kit no Android usam o AICore e processam os dados localmente.
- [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference) — A página de LLM Inference agora aponta para o LiteRT-LM.
- **LiteRT-LM** — LLMs em Linux, macOS, Windows e Raspberry Pi por linha de comando; suporta decodificação especulativa.
  - Documentação: [LiteRT-LM overview](https://ai.google.dev/edge/litert-lm/overview)
  - Código: [LiteRT-LM on GitHub](https://github.com/google-ai-edge/LiteRT-LM)

### 5. Avaliar e testar
_Decide igual ao original?_

**Qualidade**

- [fidelidade](https://developers.googleblog.com/en/gemma-3-quantized-aware-trained-state-of-the-art-ai-to-consumer-gpus/) — A quantização pode degradar o desempenho, então meça o modelo quantizado contra o original.
- [operadores](https://onnxruntime.ai/docs/tutorials/web/) — WebGPU, WebGL e WebNN suportam só parte dos operadores ONNX; o WebAssembly suporta todos.

**Desempenho**

- **bateria** · *aberto* — Artigos medem a energia em celulares; ainda não há uma medida comparável e consolidada.
  - Artigos: [On-device vs server energy](https://arxiv.org/abs/2609.11940), [Phone battery and launch time](https://arxiv.org/abs/2410.03613)
- [segundo plano](https://developer.chrome.com/blog/timer-throttling-in-chrome-88) — Abas em segundo plano são limitadas; os timers ficam mais lentos a partir do Chrome 88.
<!-- awesome:end -->
