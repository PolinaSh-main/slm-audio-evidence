# Предложение проекта (видение и наука) — Могут ли Speech LLM распознавать недостаточность аудио-доказательств?

**SMILES 2026 · Куратор: Асель Ермекова · Ядро команды — 3 человека (4-й может присоединиться)**
**Дедлайн предзащиты (12 июля, 23:00 UTC+3):** GitHub-репозиторий с текущим кодом + короткая презентация плана.
**Этот документ = наука:** позиционирование, гипотезы, ресурсы, дизайн датасета и экспериментов, что мы утверждаем на каждом уровне объёма.
**Исполнение** (роли, сроки, механика уровней, координация) → [PLAN_RU.md](PLAN.md) · **инструкции по участникам** → [roles/ru/](ROLE_M1.md) · **все термины** → [GLOSSARY_RU.md](../../../ru/GLOSSARY.md) · **карта документов** → [README_RU.md](../../../../README_RU.md) · English version: [PROPOSAL.md](../en/PROPOSAL.md).

---

## 1. Суть проекта (один абзац)

Speech LLM — модели, принимающие аудиозапись и текстовый вопрос и отвечающие текстом (см. [GLOSSARY_RU.md](../../../ru/GLOSSARY.md)) — бегло отвечают на вопросы по аудио даже тогда, когда в аудио **нет никаких доказательств** для ответа — они галлюцинируют вместо того, чтобы сказать *«в аудио нет этой информации»*. Мы строим контролируемый оценочный датасет пар «аудио–вопрос» с тремя эпистемическими уровнями (**сказано / выводимо / отсутствует**), измеряем поведение современных Speech LLM на нём и сравниваем **inference-time стратегии без дообучения** (промпт с учётом неопределённости, явная опция отказа, самопроверка, self-consistency, вербализованная уверенность), которые балансируют галлюцинации против избыточных отказов. Результат: бенчмарк + систематическое сравнение + практические рекомендации для надёжных голосовых ассистентов.

---

## 2. Позиционирование: что уже существует и что добавляем мы

Проверенная литература (все ссылки сверены с arXiv/Crossref — полный список с BibTeX в §9).

### 2.1 Ближайшие работы — читать в первую очередь

| Статья | Что сделали они | Что делаем мы иначе |
|---|---|---|
| **AQUA-Bench** (Kuan & Lee, янв. 2026) — [arXiv:2601.12248](https://arxiv.org/abs/2601.12248) | Бенчмарк неотвечаемости для аудио-QA: отсутствующий правильный вариант, несовместимый набор вариантов, несовместимая пара «аудио–вопрос». **Формат MCQ (вопросы с вариантами ответа)**, общее аудио (звуковые события) | Мы фокусируемся на **речевом содержании** (устные тексты, а не звуковые события), **свободной генерации ответа** (не MCQ), градуированной эпистемической таксономии (сказано/выводимо/отсутствует) и — главное — на **стратегиях митигации**, а не только на измерении |
| **Towards Reliable LALM** (Ma et al., 2025) — [arXiv:2505.19294](https://arxiv.org/abs/2505.19294) | Методы без обучения (мультимодальный chain-of-thought промптинг, MCoT) + дообучение с учителем (SFT), чтобы LALM отказывались отвечать на неизвестное; метрика Reliability Gain Index (RGI); надёжность — переносимая «мета-способность» | Берём их **метрику RGI** и IDK-промпты как бейзлайны; добавляем self-consistency и самопроверку, анализ risk–coverage и градиент «отвечаемо/выводимо/неотвечаемо» на речевом QA |
| **HalluAudio** (Zhao et al., апр. 2026) — [arXiv:2604.19300](https://arxiv.org/abs/2604.19300) | 5K+ верифицированных людьми QA-пар для оценки галлюцинаций LALM по речи/звукам/музыке; меряют hallucination rate, yes/no bias, refusal rate | Только бенчмарк (без митигации); переиспользуем их протокольные идеи (адверсарные промпты, метрика refusal rate) и сравниваем цифры там, где задачи пересекаются |
| **Галлюцинации объектов в LALM** (Kuan et al., 2024) — [arXiv:2406.08402](https://arxiv.org/abs/2406.08402); **«Can LALMs Truly Hear?»** (Kuan & Lee, 2024) — [arXiv:2410.16130](https://arxiv.org/abs/2410.16130) | Пробинг галлюцинаций звуковых объектов; митигация через многошаговый CoT | Звуковые события, а не речевое содержание; заимствуем идею дискриминативных вопросов для дизайна категорий |

**Тезис о новизне для предзащиты:** неотвечаемость в QA по *речевому содержанию* со *свободной формой ответа* + прямое сравнение *inference-time стратегий отказа* через призму *selective prediction* (risk–coverage) — не покрыто ни одной из работ выше. AQUA-Bench доказывает, что тема актуальна (та же лаборатория опубликовала её полгода назад); мы идём туда, где они остановились.

### 2.2 Текстовый фундамент (методы, которые переносим в аудио)

| Кластер | Статьи |
|---|---|
| Дизайн неотвечаемых вопросов | SQuAD 2.0 — [arXiv:1806.03822](https://arxiv.org/abs/1806.03822) (адверсарные неотвечаемые вопросы; наш рецепт для категории C) |
| Знают ли модели, чего не знают | SelfAware — [arXiv:2305.18153](https://arxiv.org/abs/2305.18153); AbstentionBench — [arXiv:2506.09038](https://arxiv.org/abs/2506.09038) (reasoning-дообучение *ухудшает* отказы на ~24% — отличный слайд для мотивации); обзор «Know Your Limits» — [arXiv:2407.18418](https://arxiv.org/abs/2407.18418) / TACL [10.1162/tacl_a_00754](https://doi.org/10.1162/tacl_a_00754) |
| Сигналы неопределённости | Semantic uncertainty — [arXiv:2302.09664](https://arxiv.org/abs/2302.09664); semantic entropy в Nature — [10.1038/s41586-024-07421-0](https://doi.org/10.1038/s41586-024-07421-0); вербализованная уверенность — [arXiv:2306.13063](https://arxiv.org/abs/2306.13063) |
| Inference-time стратегии | Self-consistency — [arXiv:2203.11171](https://arxiv.org/abs/2203.11171); Chain-of-Verification — [arXiv:2309.11495](https://arxiv.org/abs/2309.11495); refusal-aware дообучение R-Tuning — [arXiv:2311.09677](https://arxiv.org/abs/2311.09677) (stretch-цель, если дойдём до обучения) |

### 2.3 Бенчмарки и инфраструктурный контекст

- **MMAU** — [arXiv:2410.19168](https://arxiv.org/abs/2410.19168): 10k аудио-QA с экспертным рассуждением; даже Gemini-1.5-Pro ≈53% — показывает запас сложности.
- **AudioBench** — [arXiv:2406.16020](https://arxiv.org/abs/2406.16020): открытый eval-тулкит для AudioLLM — переиспользуем паттерны харнесса и промпты судьи.
- **SAKURA** — [arXiv:2505.13237](https://arxiv.org/abs/2505.13237): multi-hop рассуждение по речи — релевантно нашей категории B (выводимое).

---

## 3. Исследовательские вопросы и гипотезы

- **RQ1.** Когда Speech LLM отвечают вместо отказа при недостаточных аудио-доказательствах?
  **H1:** модели с дефолтным промптом отвечают на >70% неотвечаемых вопросов (по трендам AQUA-Bench/AbstentionBench).
- **RQ2.** Можно ли обнаружить недостаточность доказательств на инференсе?
  **H2:** несогласованность ответов между сэмплами (self-consistency) и самопроверка обнаруживают неотвечаемые случаи лучше, чем сырая вербализованная уверенность (которая сверхуверенна согласно [arXiv:2306.13063](https://arxiv.org/abs/2306.13063)).
- **RQ3.** Как выражать неопределённость — что максимизирует корректные отказы без избыточных?
  **H3:** промпты с опцией отказа заметно снижают галлюцинации, но повышают избыточные отказы на отвечаемых/выводимых вопросах; компромисс risk–coverage различается между моделями.
- **RQ4 (эпистемический градиент).** Модели трактуют *выводимое* (B) как *сказанное* (A) или как *отсутствующее* (C)?
  **H4:** стратегии отказа непропорционально бьют по категории B — модели не отделяют «требует вывода» от «отсутствует».

---

## 4. Ресурсы

### 4.1 Датасеты (источники для нашего оценочного набора)

| Ресурс | Что это | Как используем | Ссылка |
|---|---|---|---|
| **Spoken-SQuAD** | Озвученные TTS пассажи SQuAD + QA (37k train / 5.3k test) | Основной источник пар (аудио-пассаж, отвечаемый вопрос); добавляем B/C-вопросы к каждому пассажу | [GitHub](https://github.com/Chia-Hsuan-Lee/Spoken-SQuAD) · [HF-зеркало](https://huggingface.co/datasets/AudioLLMs/spoken_squad_test) · [alinet/spoken_squad](https://huggingface.co/datasets/alinet/spoken_squad) |
| **SQuAD 2.0** | 50k+ адверсарных неотвечаемых вопросов (текст) | Рецепт + готовые неотвечаемые вопросы для пассажей, которые озвучим сами | [arXiv:1806.03822](https://arxiv.org/abs/1806.03822) |
| **LibriSpeech** | 1000 ч аудиокниг + транскрипты | Естественное (не-TTS) аудио для среза на устойчивость | [openslr.org/12](https://www.openslr.org/12/) |
| **Свой TTS-пайплайн** | Синтез коротких пассажей → полный контроль содержания | Парные A/B/C-вопросы к одному пассажу; несколько голосов | [edge-tts](https://github.com/rany2/edge-tts) (бесплатно) или [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (локально, Apache-2.0) |
| Контекстные бенчмарки | MMAU / AudioBench / SAKURA / AQUA-Bench / HalluAudio | Референс протоколов и метрик; возможная transfer-оценка позже | ссылки в §2 |

### 4.2 Модели

| Модель | Роль | Примечания | Ссылка |
|---|---|---|---|
| **Qwen2-Audio-7B-Instruct** | Основная открытая Speech LLM | Лучшая интеграция с HF (`transformers`), влезает в 1×A100/Colab | [HF](https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct) · [arXiv:2407.10759](https://arxiv.org/abs/2407.10759) |
| **Qwen2.5-Omni-7B** | Новое поколение | Thinker–Talker; сравнение прогресса поколений | [HF](https://huggingface.co/Qwen/Qwen2.5-Omni-7B) · [arXiv:2503.20215](https://arxiv.org/abs/2503.20215) |
| **SALMONN (13B/7B)** | Другое архитектурное семейство | Энкодеры Whisper+BEATs → Vicuna; более тяжёлая установка | [GitHub](https://github.com/bytedance/SALMONN) · [arXiv:2310.13289](https://arxiv.org/abs/2310.13289) |
| **Каскад: Whisper → текстовая LLM** | Ключевая абляция | whisper-large-v3 + Qwen2.5-7B-Instruct; отделяет «не расслышала» от «не может рассуждать о доказательствах» | [arXiv:2212.04356](https://arxiv.org/abs/2212.04356) |
| *(опционально)* GPT-4o-audio / Gemini 2.x | Закрытый референс | Только если хватит API-бюджета; не на критическом пути | — |

### 4.3 Инструменты

`transformers` + `torch` + `soundfile/librosa`; `edge-tts`/Kokoro для синтеза; `pandas` + `matplotlib` для анализа; LLM-судья через дешёвый API (например, `gpt-4o-mini`/DeepSeek) **или** локальная Qwen2.5-7B-Instruct — выбор судьи задаётся конфигом; W&B или простые JSONL-логи в `results/`.

---

## 5. Дизайн оценочного датасета (спецификация v0.1)

**Единица:** `(аудио, вопрос, категория, эталон)` в JSONL (каноническая схема по полям: [PLAN_RU.md §2](PLAN.md)):

```json
{"id": "sq-0421-C2", "audio_path": "audio/sq-0421.wav", "transcript": "...",
 "question": "What color was the speaker's jacket?", "category": "C",
 "subtype": "absent-attribute", "gold_answer": "UNANSWERABLE",
 "source": "spoken-squad", "generator": "gpt-4o-mini/v2-prompt", "verified_by": "M3"}
```

**Категории и подтипы:**

- **A — Отвечаемый (сказано):** ответ извлекается из аудио дословно. Источник: готовые QA Spoken-SQuAD.
- **B — Требующий рассуждения (выводимо):** нужен 1-шаговый вывод/агрегация по сказанному (отрицание, сравнение, арифметика по названным фактам, опционально паралингвистика). Генерируется LLM по транскрипту, проверяется людьми.
- **C — Неотвечаемый (отсутствует):** правдоподобный, но неподкреплённый вопрос. Подтипы для тонкого анализа:
  - `C1 absent-entity` — про сущность, которая не упоминалась;
  - `C2 absent-attribute` — сущность упомянута, атрибут нет (пример с курткой из брифа);
  - `C3 false-premise` — вопрос предполагает то, что противоречит аудио;
  - `C4 off-topic` — вопрос не связан с доменом аудио.

**Генерация:** категорийные LLM-промпты по **транскриптам** (никогда по аудио), вариация температуры, k кандидатов → фильтры-правила (без да/нет для C, без утечки ответа) → **верификация людьми**: каждый элемент размечает один тиммейт, не участвовавший в генерации; разногласия → совместная адъюдикация. Логируем межразметочное согласие на калибровочном раунде.

**Объёмы:** пилот **90–120 элементов** (30–40 на категорию) к 10 июля → **~600–900 элементов** в основной фазе, сбалансированных по категориям и подтипам, ~50/50 TTS против естественного аудио.

---

## 6. Эксперименты

### E1 — Базовое поведение (RQ1) · *пилот к предзащите*
Сетка: {Qwen2-Audio, каскад} × {обычный промпт} × пилотный набор. Классифицируем каждый ответ как **ответ / отказ / уклонение** (судья + regex по фразам отказа). Главные цифры: доля галлюцинаций на C, точность на A/B.

### E2 — Inference-time митигация (RQ2, RQ3) · *основная фаза, промпты готовим сейчас*
Та же сетка плюс стратегии, каждая против E1:
1. **S1 IDK-промпт:** «Отвечай только если аудио это подтверждает; иначе скажи, что в аудио нет этой информации.»
2. **S2 Явная опция:** добавляем «нельзя определить из аудио» как явный допустимый вариант.
3. **S3 Самопроверка (в духе CoVe):** шаг 1 ответ → шаг 2 «Подтверждён ли этот ответ аудио? Исправь.»
4. **S4 Self-consistency:** k=5 сэмплов при T=0.7; согласие < θ ⇒ отказ (θ перебираем).
5. **S5 Вербализованная уверенность:** уверенность 0–100; перебор порога → кривая risk–coverage.

### E3 — Эпистемический анализ (RQ4)
Разбивки по A/B/C (и подтипам C); таксономия ошибок на C (выдумка vs осторожная догадка vs корректный отказ); избыточные отказы на B как ключевая метрика цены; сравнение каскада с end-to-end; (stretch) сигналы token-logprob, порча аудио (шум/обрезка) как «ручка деградации доказательств».

### Метрики (модуль `src/metrics.py`)
- По категориям: точность (A, B), **доля галлюцинаций** = ответил-и-неверно / всего (C), **доля корректных отказов** (C), **доля избыточных отказов** (A∪B).
- Selective prediction: кривая risk–coverage, **AURC**; F1 отказа по {ответ, отказ}.
- **Reliability Gain Index (RGI)** из [arXiv:2505.19294](https://arxiv.org/abs/2505.19294) для сопоставимости.
- Судья: фиксированная рубрика, версионируемый промпт, ручной аудит.

---

## 7. Уровни объёма — что мы утверждаем на каждом

Механика исполнения (таблицы объёмов, контрольная точка 10 июля, правила переключения, лестница дополнений) — в [PLAN_RU.md §4](PLAN.md). Здесь — наука: каждый уровень содержит предыдущий, и каждый добавляет утверждения.

### Уровень 1 — МИНИМУМ (аварийный)
Наименьший эксперимент, который даёт защитимое научное утверждение: одна модель, plain против S1, 60 элементов, ручная разметка.
**Покрытие RQ:** RQ1 полностью; RQ3 как компромисс из двух точек; RQ2 не покрыт; RQ4 только индикативно (20 элементов на категорию).
**Защитимые утверждения:** «Qwen2-Audio отвечает выдуманным ответом на **X%** неотвечаемых устных вопросов при обычном промпте» и «однострочная IDK-инструкция снижает это до **Y%** ценой **Z%** избыточных отказов» — точные подсчёты с 95%-ными интервалами Уилсона, в формулировке *пилотных свидетельств*.
**Сознательно НЕ утверждаем:** сравнения между моделями, механизмы детекции, калибровку, таксономию подтипов.

### Уровень 2 — СРЕДНИЙ (дефолт = это предложение)
Всё из Уровня 1, расширенное до сравнительного исследования: 3 системы (+ каскад и Qwen2.5-Omni), стратегии S1–S5, LLM-судья с ручным аудитом, 600–900 элементов.
**Покрытие RQ:** все RQ1–RQ4; проверяемы все гипотезы H1–H4 (§3).
**Защитимые утверждения:** первые цифры неотвечаемости в свободной форме (не MCQ) на речевом содержании; рейтинг стратегий с явной ценой на кривых risk–coverage; атрибуция «слух против эпистемического рассуждения» через разрыв каскад–end-to-end; значения RGI, сопоставимые с Ma et al.

### Уровень 3 — МАКСИМУМ (stretch)
Всё из Уровня 2, доведённое до публикуемого исследования. Четыре расширенных вопроса:
**RQ5 (шкала деградации):** растут ли отказы плавно при деградации доказательств (шум/обрезка) или ломаются резко? · **RQ6 (промптинг vs дообучение):** какую долю идеального поведения отказов возвращают inference-time методы против маленького LoRA refusal-tune? · **RQ7 (внутренние vs вербализованные сигналы):** бьют ли детекторы на logprob/semantic entropy заявленную уверенность (AUROC)? · **RQ8 (внешняя валидность):** переносятся ли выводы на речевые подмножества AQUA-Bench / HalluAudio?
**Защитимые утверждения** (каждое соответствует одной ступени лестницы дополнений; отброс ступени убирает ровно одно утверждение): лидерборд на 5 системах · кривые деградации · сравнение детекторов по AUROC · вердикт «промптинг против дообучения» · утверждение о переносе · публичный датасет на HF + черновик workshop-статьи.

---

## 8. Риски

| Риск | Митигация |
|---|---|
| Нет GPU до одобрения | Пилот рассчитан на бесплатный Colab/CPU (Qwen2-Audio-7B int8; ≤120 элементов; каскад дёшев). Всё через конфиги → масштабирование = смена конфига |
| Возражение «AQUA-Bench уже это сделал» | Позиционирование готово (§2.1): речевое содержание + свободная форма + сравнение митигаций + эпистемический градиент. Цитируем и строим поверх, а не соревнуемся в MCQ |
| Сгенерированные C-вопросы втайне отвечаемы | Верификация не-автором 100% пилота; калибровочный раунд со статистикой согласия |
| Трудности установки SALMONN/Omni | Жёсткий приоритет: Qwen2-Audio → каскад → Omni → SALMONN; первых двух достаточно для предзащиты |
| Ненадёжность LLM-судьи | Версионируемая рубрика, ручной аудит, fallback на точное совпадение для span-ответов |
| Избыточные отказы прячутся за хорошими цифрами на C | Всегда отчитываем точность на A/B вместе с risk–coverage |
| Подтверждены только 3 участника (4-й под вопросом) | План полон при 3: гибкое направление отделяемо; правило онбординга и регулятор объёма — в [PLAN_RU.md](PLAN.md) §1, §8 |

---

## 9. Источники (все проверены через arXiv/Crossref)

Библиографические записи оставлены на английском — они используются как есть в BibTeX.

```bibtex
@online{rajpurkar2018know,  author={Pranav Rajpurkar and Robin Jia and Percy Liang},
  title={Know What You Don't Know: Unanswerable Questions for {SQuAD}},
  year={2018}, eprinttype={arXiv}, eprint={1806.03822}, url={https://arxiv.org/abs/1806.03822}}
@online{li2018spoken,       author={Chia-Hsuan Li and Szu-Lin Wu and Chi-Liang Liu and Hung-yi Lee},
  title={Spoken {SQuAD}: A Study of Mitigating the Impact of Speech Recognition Errors on Listening Comprehension},
  year={2018}, eprinttype={arXiv}, eprint={1804.00320}, url={https://arxiv.org/abs/1804.00320}}
@online{yin2023selfaware,   author={Zhangyue Yin and Qiushi Sun and Qipeng Guo and Jiawen Wu and Xipeng Qiu and Xuanjing Huang},
  title={Do Large Language Models Know What They Don't Know?},
  year={2023}, eprinttype={arXiv}, eprint={2305.18153}, url={https://arxiv.org/abs/2305.18153}}
@online{kirichenko2025abstentionbench, author={Polina Kirichenko and Mark Ibrahim and Kamalika Chaudhuri and Samuel J. Bell},
  title={{AbstentionBench}: Reasoning {LLMs} Fail on Unanswerable Questions},
  year={2025}, eprinttype={arXiv}, eprint={2506.09038}, url={https://arxiv.org/abs/2506.09038}}
@article{wen2025know,       author={Bingbing Wen and Jihan Yao and Shangbin Feng and Chenjun Xu and Yulia Tsvetkov and Bill Howe and Lucy Lu Wang},
  title={Know Your Limits: A Survey of Abstention in Large Language Models},
  journal={Transactions of the Association for Computational Linguistics}, year={2025}, doi={10.1162/tacl_a_00754}}
@online{zhang2023rtuning,   author={Hanning Zhang and Shizhe Diao and Yong Lin and Yi R. Fung and Qing Lian and Xingyao Wang and Yangyi Chen and Heng Ji and Tong Zhang},
  title={{R-Tuning}: Instructing Large Language Models to Say `I Don't Know'},
  year={2023}, eprinttype={arXiv}, eprint={2311.09677}, url={https://arxiv.org/abs/2311.09677}}
@online{kuhn2023semantic,   author={Lorenz Kuhn and Yarin Gal and Sebastian Farquhar},
  title={Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation},
  year={2023}, eprinttype={arXiv}, eprint={2302.09664}, url={https://arxiv.org/abs/2302.09664}}
@article{farquhar2024detecting, author={Sebastian Farquhar and Jannik Kossen and Lorenz Kuhn and Yarin Gal},
  title={Detecting hallucinations in large language models using semantic entropy},
  journal={Nature}, year={2024}, doi={10.1038/s41586-024-07421-0}}
@online{xiong2023can,       author={Miao Xiong and Zhiyuan Hu and Xinyang Lu and Yifei Li and Jie Fu and Junxian He and Bryan Hooi},
  title={Can {LLMs} Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in {LLMs}},
  year={2023}, eprinttype={arXiv}, eprint={2306.13063}, url={https://arxiv.org/abs/2306.13063}}
@online{wang2022selfconsistency, author={Xuezhi Wang and Jason Wei and Dale Schuurmans and Quoc Le and Ed Chi and Sharan Narang and Aakanksha Chowdhery and Denny Zhou},
  title={Self-Consistency Improves Chain of Thought Reasoning in Language Models},
  year={2022}, eprinttype={arXiv}, eprint={2203.11171}, url={https://arxiv.org/abs/2203.11171}}
@online{dhuliawala2023cove, author={Shehzaad Dhuliawala and Mojtaba Komeili and Jing Xu and Roberta Raileanu and Xian Li and Asli Celikyilmaz and Jason Weston},
  title={Chain-of-Verification Reduces Hallucination in Large Language Models},
  year={2023}, eprinttype={arXiv}, eprint={2309.11495}, url={https://arxiv.org/abs/2309.11495}}
@online{chu2024qwen2audio,  author={Yunfei Chu and Jin Xu and Qian Yang and Haojie Wei and Xipin Wei and Zhifang Guo and Yichong Leng and Yuanjun Lv and Jinzheng He and Junyang Lin and Chang Zhou and Jingren Zhou},
  title={{Qwen2-Audio} Technical Report},
  year={2024}, eprinttype={arXiv}, eprint={2407.10759}, url={https://arxiv.org/abs/2407.10759}}
@online{xu2025qwen25omni,   author={Jin Xu and Zhifang Guo and Jinzheng He and Hangrui Hu and Ting He and Shuai Bai and Keqin Chen and Jialin Wang and Yang Fan and Kai Dang and Bin Zhang and Xiong Wang and Yunfei Chu and Junyang Lin},
  title={{Qwen2.5-Omni} Technical Report},
  year={2025}, eprinttype={arXiv}, eprint={2503.20215}, url={https://arxiv.org/abs/2503.20215}}
@online{tang2023salmonn,    author={Changli Tang and Wenyi Yu and Guangzhi Sun and Xianzhao Chen and Tian Tan and Wei Li and Lu Lu and Zejun Ma and Chao Zhang},
  title={{SALMONN}: Towards Generic Hearing Abilities for Large Language Models},
  year={2023}, eprinttype={arXiv}, eprint={2310.13289}, url={https://arxiv.org/abs/2310.13289}}
@online{radford2022whisper, author={Alec Radford and Jong Wook Kim and Tao Xu and Greg Brockman and Christine McLeavey and Ilya Sutskever},
  title={Robust Speech Recognition via Large-Scale Weak Supervision},
  year={2022}, eprinttype={arXiv}, eprint={2212.04356}, url={https://arxiv.org/abs/2212.04356}}
@online{sakshi2024mmau,     author={S Sakshi and Utkarsh Tyagi and Sonal Kumar and Ashish Seth and Ramaneswaran Selvakumar and Oriol Nieto and Ramani Duraiswami and Sreyan Ghosh and Dinesh Manocha},
  title={{MMAU}: A Massive Multi-Task Audio Understanding and Reasoning Benchmark},
  year={2024}, eprinttype={arXiv}, eprint={2410.19168}, url={https://arxiv.org/abs/2410.19168}}
@online{wang2024audiobench, author={Bin Wang and Xunlong Zou and Geyu Lin and Shuo Sun and Zhuohan Liu and Wenyu Zhang and Zhengyuan Liu and AiTi Aw and Nancy F. Chen},
  title={{AudioBench}: A Universal Benchmark for Audio Large Language Models},
  year={2024}, eprinttype={arXiv}, eprint={2406.16020}, url={https://arxiv.org/abs/2406.16020}}
@online{yang2025sakura,     author={Chih-Kai Yang and Neo Ho and Yen-Ting Piao and Hung-yi Lee},
  title={{SAKURA}: On the Multi-hop Reasoning of Large Audio-Language Models Based on Speech and Audio Information},
  year={2025}, eprinttype={arXiv}, eprint={2505.13237}, url={https://arxiv.org/abs/2505.13237}}
@online{kuan2024understanding, author={Chun-Yi Kuan and Wei-Ping Huang and Hung-yi Lee},
  title={Understanding Sounds, Missing the Questions: The Challenge of Object Hallucination in Large Audio-Language Models},
  year={2024}, eprinttype={arXiv}, eprint={2406.08402}, url={https://arxiv.org/abs/2406.08402}}
@online{kuan2024trulyhear,  author={Chun-Yi Kuan and Hung-yi Lee},
  title={Can Large Audio-Language Models Truly Hear? Tackling Hallucinations with Multi-Task Assessment and Stepwise Audio Reasoning},
  year={2024}, eprinttype={arXiv}, eprint={2410.16130}, url={https://arxiv.org/abs/2410.16130}}
@online{ma2025reliable,     author={Ziyang Ma and Xiquan Li and Yakun Song and Wenxi Chen and Chenpeng Du and Jian Wu and Yuanzhe Chen and Zhuo Chen and Yuping Wang and Yuxuan Wang and Xie Chen},
  title={Towards Reliable Large Audio Language Model},
  year={2025}, eprinttype={arXiv}, eprint={2505.19294}, url={https://arxiv.org/abs/2505.19294}}
@online{kuan2026aquabench,  author={Chun-Yi Kuan and Hung-yi Lee},
  title={{AQUA-Bench}: Beyond Finding Answers to Knowing When There Are None in Audio Question Answering},
  year={2026}, eprinttype={arXiv}, eprint={2601.12248}, url={https://arxiv.org/abs/2601.12248}}
@online{zhao2026halluaudio, author={Feiyu Zhao and Yiming Chen and Wenhuan Lu and Daipeng Zhang and Xianghu Yue and Jianguo Wei},
  title={{HalluAudio}: A Comprehensive Benchmark for Hallucination Detection in Large Audio-Language Models},
  year={2026}, eprinttype={arXiv}, eprint={2604.19300}, url={https://arxiv.org/abs/2604.19300}}
```
