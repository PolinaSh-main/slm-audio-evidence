import argparse
import json
import os

# Работает и как `python src/run_eval.py`, и как `python -m src.run_eval`
try:
    from src.judge import classify_response, check_correctness
    from src.metrics import calculate_all_metrics, generate_markdown_report
except ImportError:
    from judge import classify_response, check_correctness
    from metrics import calculate_all_metrics, generate_markdown_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Оценка одного прогона: манифест + ответы модели -> метрики.")
    parser.add_argument("--manifest", default="data/manifests/pilot.jsonl",
                        help="JSONL манифеста (категории и эталонные ответы).")
    parser.add_argument("--responses", required=True,
                        help="JSONL ответов модели из results/<run_id>/responses.jsonl.")
    parser.add_argument("--out", default=None,
                        help="Куда писать отчёт и разметку; по умолчанию рядом с --responses.")
    return parser.parse_args()


def load_jsonl(file_path: str) -> list:
    """Вспомогательная функция для чтения файлов формата JSONL."""
    if not os.path.exists(file_path):
        print(f"[-] Файл не найден: {file_path}")
        return []
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def run_evaluation(manifest_path: str, responses_path: str, out_dir: str) -> None:
    # 1. Загружаем манифест (там хранятся правильные ответы и категории A/B/C)
    manifest_items = load_jsonl(manifest_path)
    if not manifest_items:
        return
    manifest_dict = {
        item["id"]: {"category": item["category"], "gold_answer": item["gold_answer"]}
        for item in manifest_items
    }

    # 2. Загружаем ответы модели
    responses = load_jsonl(responses_path)
    if not responses:
        print("[-] Нет ответов модели для оценки.")
        return

    evaluated_data = []
    judged_rows = []

    # 3. Сопоставляем каждый ответ с категорией и оцениваем
    for resp in responses:
        item_id = resp["id"]
        if item_id not in manifest_dict:
            print(f"[!] id {item_id} нет в манифесте — пропускаю")
            continue
        category = manifest_dict[item_id]["category"]
        gold_answer = manifest_dict[item_id]["gold_answer"]

        detected_label = classify_response(resp["response"])
        is_correct = check_correctness(category, detected_label, resp["response"], gold_answer)

        evaluated_data.append({"category": category, "label": detected_label, "correct": is_correct})
        judged_rows.append({
            "id": item_id, "category": category, "label": detected_label,
            "correct": is_correct, "gold_answer": gold_answer,
            "response": resp["response"],
            "judge": "pending-manual" if (category == "B" and detected_label == "answer") else "rules",
        })

    # 4. Метрики + отчёт
    metrics = calculate_all_metrics(evaluated_data)
    model_name = responses[0].get("model", "Unknown-Model")
    strategy = responses[0].get("strategy", "unknown")
    report = generate_markdown_report(metrics, model_name, strategy)

    # 5. Сохраняем: поэлементную разметку и отчёт
    os.makedirs(out_dir, exist_ok=True)
    judged_path = os.path.join(out_dir, "responses_judged.jsonl")
    with open(judged_path, "w", encoding="utf-8") as f:
        for row in judged_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    report_path = os.path.join(out_dir, "metrics.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[+] Оценено {len(evaluated_data)} ответов ({model_name} / {strategy})")
    print(f"[+] Разметка: {judged_path}")
    print(f"[+] Отчёт:    {report_path}")


if __name__ == "__main__":
    args = parse_args()
    out = args.out or os.path.dirname(os.path.abspath(args.responses))
    run_evaluation(args.manifest, args.responses, out)
