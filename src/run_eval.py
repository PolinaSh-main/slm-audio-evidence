import json
import os
from judge import classify_response, check_correctness
from metrics import calculate_all_metrics, generate_markdown_report

# Пути к файлам (их можно будет поменять, когда M1 пришлет точные пути)
MANIFEST_PATH = "data/manifests/pilot.jsonl"
RESPONSES_PATH = "results/smoke_run/responses.jsonl"
OUTPUT_REPORT_PATH = "results/smoke_run/metrics.md"

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

def run_dry_evaluation():
    print("=== ЗАПУСК СУХОГО ПРОГОНА НА РЕАЛЬНЫХ ФАЙЛАХ ===")
    
    # 1. Загружаем манифест (там хранятся правильные ответы и категории A/B/C)
    manifest_items = load_jsonl(MANIFEST_PATH)
    if not manifest_items:
        return
    
    # Создаем удобный словарь для быстрого поиска по ID: {id: {"category", "gold_answer"}}
    manifest_dict = {
        item["id"]: {
            "category": item["category"], 
            "gold_answer": item["gold_answer"]
        } for item in manifest_items
    }
    
    # 2. Загружаем ответы модели, которые сгенерировал M1
    responses = load_jsonl(RESPONSES_PATH)
    if not responses:
        print("[-] Нет ответов модели для оценки. Ждем файл от M1.")
        return
        
    evaluated_data = []
    
    # 3. Сопоставляем каждый ответ модели с его категорией из манифеста
    for resp in responses:
        item_id = resp["id"]
        
        # Находим категорию и правильный ответ по ID
        if item_id in manifest_dict:
            category = manifest_dict[item_id]["category"]
            gold_answer = manifest_dict[item_id]["gold_answer"]
            
            # Оцениваем ответ нашей функцией классификации
            detected_label = classify_response(resp["response"])
            
            # Проверяем правильность
            is_correct = check_correctness(category, detected_label, resp["response"], gold_answer)
            
            evaluated_data.append({
                "category": category,
                "label": detected_label,
                "correct": is_correct
            })
            
    # 4. Считаем итоговые метрики по сопоставленным данным
    metrics = calculate_all_metrics(evaluated_data)
    
    # 5. Генерируем красивый Markdown отчет
    model_name = responses[0].get("model", "Unknown-Model")
    strategy = responses[0].get("strategy", "unknown")
    report = generate_markdown_report(metrics, model_name, strategy)
    
    # 6. Сохраняем результат в папку к ответам
    os.makedirs(os.path.dirname(OUTPUT_REPORT_PATH), exist_ok=True)
    with open(OUTPUT_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\n[+] Сухой прогон завершен! Результаты сохранены в {OUTPUT_REPORT_PATH}")
    print(report)

if __name__ == "__main__":
    run_dry_evaluation()