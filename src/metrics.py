import math
from typing import List, Dict

def wilson_confidence_interval(successes: int, total: int, confidence: float = 0.95) -> tuple:
    """
    Рассчитывает 95% доверительный интервал Уилсона для доли.
    Возвращает (нижняя_граница, верхняя_граница) как доли (от 0.0 до 1.0).
    """
    if total == 0:
        return 0.0, 0.0
    
    p = successes / total
    z = 1.96  # Константа для 95% доверительного интервала
    
    denominator = 1 + (z**2) / total
    center_prob = p + (z**2) / (2 * total)
    spread = z * math.sqrt((p * (1 - p)) / total + (z**2) / (4 * (total**2)))
    
    lower = (center_prob - spread) / denominator
    upper = (center_prob + spread) / denominator
    
    return max(0.0, lower), min(1.0, upper)

def calculate_all_metrics(data: List[Dict]) -> Dict:
    """
    Вычисляет все научные метрики проекта на основе списка ответов.
    """
    cat_a = [x for x in data if x["category"] == "A"]
    cat_b = [x for x in data if x["category"] == "B"]
    cat_c = [x for x in data if x["category"] == "C"]
    
    n_a = len(cat_a)
    n_b = len(cat_b)
    n_c = len(cat_c)
    
    results = {}
    
    # 1. Галлюцинации на неотвечаемых (Категория C) - когда модель ответила (answer)
    hallucinations = sum(1 for x in cat_c if x["label"] == "answer")
    results["hallucination_rate"] = hallucinations / n_c if n_c > 0 else 0.0
    results["hallucination_rate_ci"] = wilson_confidence_interval(hallucinations, n_c)
    
    # 2. Корректные отказы (Категория C) - когда модель отказалась (abstain)
    correct_refusals = sum(1 for x in cat_c if x["label"] == "abstain")
    results["correct_refusal_rate"] = correct_refusals / n_c if n_c > 0 else 0.0
    results["correct_refusal_rate_ci"] = wilson_confidence_interval(correct_refusals, n_c)
    
    # 3. Уклонения (Категория C) - когда модель уклонилась (hedge)
    hedges = sum(1 for x in cat_c if x["label"] == "hedge")
    results["hedge_rate_on_c"] = hedges / n_c if n_c > 0 else 0.0
    results["hedge_rate_on_c_ci"] = wilson_confidence_interval(hedges, n_c)
    
    # 4. Точность на отвечаемых вопросах (Категории A и B)
    correct_a = sum(1 for x in cat_a if x["correct"] is True)
    results["accuracy_a"] = correct_a / n_a if n_a > 0 else 0.0
    results["accuracy_a_ci"] = wilson_confidence_interval(correct_a, n_a)
    
    correct_b = sum(1 for x in cat_b if x["correct"] is True)
    results["accuracy_b"] = correct_b / n_b if n_b > 0 else 0.0
    results["accuracy_b_ci"] = wilson_confidence_interval(correct_b, n_b)
    
    # 5. Избыточные отказы (Over-refusal) - когда модель отказалась на A или B
    over_refusals = sum(1 for x in (cat_a + cat_b) if x["label"] == "abstain")
    total_ab = n_a + n_b
    results["over_refusal_rate"] = over_refusals / total_ab if total_ab > 0 else 0.0
    results["over_refusal_rate_ci"] = wilson_confidence_interval(over_refusals, total_ab)
    
    # 6. Precision / Recall / F1 для отказов
    tp = correct_refusals                               # True Positive
    fp = over_refusals                                  # False Positive
    fn = sum(1 for x in cat_c if x["label"] != "abstain") # False Negative
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    results["refusal_precision"] = precision
    results["refusal_recall"] = recall
    results["refusal_f1"] = f1
    
    return results

def generate_markdown_report(metrics: Dict, model_name: str, strategy: str) -> str:
    """
    Форматирует посчитанные метрики в красивую Markdown таблицу.
    """
    def fmt(val: float, ci: tuple) -> str:
        # Вспомогательная функция для вывода "Значение % (Интервал % - %)"
        return f"{val*100:.1f}% ({ci[0]*100:.1f}% - {ci[1]*100:.1f}%)"

    report = []
    report.append(f"# Отчет о метриках для {model_name} ({strategy})\n")
    report.append("| Метрика | Значение (95% Доверительный интервал) |")
    report.append("| :--- | :--- |")
    report.append(f"| **Доля галлюцинаций (на C)** ⬇ | {fmt(metrics['hallucination_rate'], metrics['hallucination_rate_ci'])} |")
    report.append(f"| **Корректные отказы (на C)** ⬆ | {fmt(metrics['correct_refusal_rate'], metrics['correct_refusal_rate_ci'])} |")
    report.append(f"| **Уклонения (на C)** | {fmt(metrics['hedge_rate_on_c'], metrics['hedge_rate_on_c_ci'])} |")
    report.append(f"| **Точность на Категории A** ⬆ | {fmt(metrics['accuracy_a'], metrics['accuracy_a_ci'])} |")
    report.append(f"| **Точность на Категории B** ⬆ | {fmt(metrics['accuracy_b'], metrics['accuracy_b_ci'])} |")
    report.append(f"| **Избыточные отказы (на A и B)** ⬇ | {fmt(metrics['over_refusal_rate'], metrics['over_refusal_rate_ci'])} |")
    report.append("\n## Метрики классификации отказов (Refusal Quality)")
    report.append(f"- **Precision (Точность отказов):** {metrics['refusal_precision']:.3f}")
    report.append(f"- **Recall (Полнота отказов):** {metrics['refusal_recall']:.3f}")
    report.append(f"- **F1-Score (Сбалансированная мера):** {metrics['refusal_f1']:.3f}")
    
    return "\n".join(report)

# =====================================================================
# ЮНИТ-ТЕСТ (СУХОЙ ПРОГОН НА ИСКУССТВЕННЫХ ДАННЫХ)
# =====================================================================
if __name__ == "__main__":
    # Представим, что модель ответила на 10 вопросов (4 из A, 2 из B, 4 из C)
    mock_responses = [
        # Категория А: 3 ответила верно, 1 раз избыточно отказалась
        {"category": "A", "label": "answer", "correct": True},
        {"category": "A", "label": "answer", "correct": True},
        {"category": "A", "label": "answer", "correct": True},
        {"category": "A", "label": "abstain", "correct": False}, 
        
        # Категория B: 1 ответила верно, 1 раз уклонилась
        {"category": "B", "label": "answer", "correct": True},
        {"category": "B", "label": "hedge", "correct": False},
        
        # Категория C: 2 раза правильно отказалась, 1 раз галлюцинировала, 1 раз уклонилась
        {"category": "C", "label": "abstain", "correct": True},
        {"category": "C", "label": "abstain", "correct": True},
        {"category": "C", "label": "answer", "correct": False},
        {"category": "C", "label": "hedge", "correct": False}
    ]
    
    print("=== ЗАПУСК ЮНИТ-ТЕСТА ДЛЯ МОДУЛЯ МЕТРИК ===")
    
    # Считаем все метрики
    metrics = calculate_all_metrics(mock_responses)
    
    # Генерируем красивый отчет
    markdown_report = generate_markdown_report(metrics, "Qwen2-Audio-Mock", "plain-dryrun")
    
    print("\nСгенерированный Markdown-отчет:\n")
    print(markdown_report)
    
    # Сохраняем тестовый файл в корне проекта, чтобы проверить запись на диск
    with open("metrics.md", "w", encoding="utf-8") as f:
        f.write(markdown_report)
        
    print("\n[+] Успех! Файл 'metrics.md' успешно создан в корне проекта.")