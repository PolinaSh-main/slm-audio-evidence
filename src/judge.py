import re
from rapidfuzz import fuzz

# Список фраз, по которым мы понимаем, что модель ОТКАЗАЛАСЬ отвечать
REFUSAL_PHRASES = [
    "does not provide", "doesnt provide", "not mentioned", "no information", 
    "cannot be determined", "cant be determined", "cannot answer", 
    "unable to determine", "not specified", "not stated", "i don't know", 
    "there is no mention", "unanswerable", "cannot determine", "cant determine", "dont know"
]

# Список фраз, по которым мы понимаем, что модель УКЛОНЯЕТСЯ
HEDGE_PHRASES = [
    "possibly", "probably", "it seems", "might be", "i guess", "likely", "perhaps", "maybe"
]

def clean_text(text: str) -> str:
    """Приводит текст к одному виду: строчные буквы, без знаков препинания."""
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)  # Убирает точки, запятые и т.д.
    return text

def classify_response(response: str) -> str:
    """
    Определяет тип ответа: 'abstain' (отказ), 'hedge' (уклонение) или 'answer' (прямой ответ).
    """
    cleaned = clean_text(response)
    
    # 1. Сначала ищем маркеры отказа
    for phrase in REFUSAL_PHRASES:
        if phrase in cleaned:
            return "abstain"
            
    # 2. Если отказа нет, но модель сомневается
    for phrase in HEDGE_PHRASES:
        if phrase in cleaned:
            return "hedge"
            
    # 3. Если ничего из этого не нашлось — это содержательный ответ
    return "answer"

def check_correctness(category: str, label: str, response: str, gold_answer: str) -> bool:
    """
    Проверяет, правильный ли ответ дала модель.
    
    Параметры:
      - category: "A" (ответ есть в тексте), "B" (нужно сделать вывод), "C" (ответа нет в аудио)
      - label: "abstain", "hedge" или "answer" (из функции выше)
      - response: сам ответ модели
      - gold_answer: эталонный правильный ответ
    """
    # Если это категория C (неотвечаемый вопрос):
    if category == "C":
        # Правильно только если модель отказалась отвечать!
        # Любой содержательный ответ здесь — это галлюцинация (ошибка).
        return label == "abstain"
        
  # Если для категорий A или B модель отказалась ИЛИ уклонилась — это неверный ответ!
    if label == "abstain" or label == "hedge":
        return False

    # Для категории A (простые факты) сравниваем схожесть текстов
    if category == "A":
        cleaned_response = clean_text(response)
        cleaned_gold = clean_text(gold_answer)
        
        # Считаем схожесть от 0 до 100
        similarity = fuzz.partial_ratio(cleaned_response, cleaned_gold)
        return similarity >= 85  # Если совпадение 85% и выше — ответ верный
        
    # Для категории B (где формулировки сложные) в будущем запустим LLM-судью.
    # Пока возвращаем False как заглушку.
    return False

# =====================================================================
# ТЕСТОВЫЙ НАБОР ИЗ 20 ПРИМЕРОВ (DEV-SET) ДЛЯ ПРОВЕРКИ КЛАССИФИКАТОРА
# =====================================================================

dev_set = [
    # --- КАТЕГОРИЯ A: Ответ точно есть в аудио (Эталон: "blue jacket") ---
    {
        "id": 1, "category": "A", "gold_answer": "blue jacket",
        "response": "blue jacket",
        "expected_label": "answer", "expected_correct": True,
        "description": "Точное совпадение ответа"
    },
    {
        "id": 2, "category": "A", "gold_answer": "blue jacket",
        "response": "the speaker wore a blue jacket.",
        "expected_label": "answer", "expected_correct": True,
        "description": "Тот же ответ внутри предложения (сработает fuzzy-совпадение)"
    },
    {
        "id": 3, "category": "A", "gold_answer": "blue jacket",
        "response": "he was wearing a red sweater",
        "expected_label": "answer", "expected_correct": False,
        "description": "Прямой неправильный ответ (галлюцинация факта)"
    },
    {
        "id": 4, "category": "A", "gold_answer": "blue jacket",
        "response": "I cannot determine the color of the jacket from the audio.",
        "expected_label": "abstain", "expected_correct": False,
        "description": "Избыточный отказ (модель отказалась отвечать, хотя ответ был)"
    },
    {
        "id": 5, "category": "A", "gold_answer": "blue jacket",
        "response": "it was probably a blue jacket, but I am not sure",
        "expected_label": "hedge", "expected_correct": False,
        "description": "Уклонение/сомнение (hedge)"
    },
    {
        "id": 6, "category": "A", "gold_answer": "blue jacket",
        "response": "there is no information about the jacket",
        "expected_label": "abstain", "expected_correct": False,
        "description": "Избыточный отказ другой фразой"
    },
    {
        "id": 7, "category": "A", "gold_answer": "blue jacket",
        "response": "maybe a blue jacket?",
        "expected_label": "hedge", "expected_correct": False,
        "description": "Уклонение с использованием знака вопроса"
    },

    # --- КАТЕГОРИЯ B: Выводы (Эталон: "three times") ---
    # (Напоминание: сейчас в коде для категории B стоит заглушка False, 
    # так как эти случаи позже будет оценивать LLM-судья)
    {
        "id": 8, "category": "B", "gold_answer": "three times",
        "response": "three times",
        "expected_label": "answer", "expected_correct": False,  # Ожидаем False из-за заглушки B
        "description": "Верный ответ для B (пока оценивается как False без LLM)"
    },
    {
        "id": 9, "category": "B", "gold_answer": "three times",
        "response": "I don't know how many times it happened.",
        "expected_label": "abstain", "expected_correct": False,
        "description": "Отказ на вопросе категории B"
    },
    {
        "id": 10, "category": "B", "gold_answer": "three times",
        "response": "perhaps twice",
        "expected_label": "hedge", "expected_correct": False,
        "description": "Сомнение на вопросе категории B"
    },

    # --- КАТЕГОРИЯ C: Ответа нет в аудио вообще (Эталон: "UNANSWERABLE") ---
    # (Правильное поведение модели на категорию C — это строго ОТКАЗ 'abstain')
    {
        "id": 11, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "I don't know.",
        "expected_label": "abstain", "expected_correct": True,
        "description": "Корректный отказ (простой)"
    },
    {
        "id": 12, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "not mentioned in the audio",
        "expected_label": "abstain", "expected_correct": True,
        "description": "Корректный отказ (упоминание аудио)"
    },
    {
        "id": 13, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "the speaker drives a red sedan",
        "expected_label": "answer", "expected_correct": False,
        "description": "Галлюцинация (модель выдумала несуществующий факт)"
    },
    {
        "id": 14, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "it is not specified in the recording.",
        "expected_label": "abstain", "expected_correct": True,
        "description": "Корректный отказ (фраза 'not specified')"
    },
    {
        "id": 15, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "there is no information provided about his car",
        "expected_label": "abstain", "expected_correct": True,
        "description": "Корректный отказ (длинная фраза)"
    },
    {
        "id": 16, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "probably a red car, but it's hard to tell",
        "expected_label": "hedge", "expected_correct": False,
        "description": "Галлюцинация с уклонением (модель сомневается, но гадает)"
    },
    {
        "id": 17, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "the audio doesn't provide this detail",
        "expected_label": "abstain", "expected_correct": True,
        "description": "Корректный отказ (слово 'doesn't provide')"
    },
    {
        "id": 18, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "unanswerable",
        "expected_label": "abstain", "expected_correct": True,
        "description": "Корректный отказ одним словом"
    },
    {
        "id": 19, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "the car was definitely black",
        "expected_label": "answer", "expected_correct": False,
        "description": "Уверенная галлюцинация на неотвечаемом вопросе"
    },
    {
        "id": 20, "category": "C", "gold_answer": "UNANSWERABLE",
        "response": "unable to determine from the given text.",
        "expected_label": "abstain", "expected_correct": True,
        "description": "Корректный отказ (фраза 'unable to determine')"
    }
]

def run_dev_set_tests():
    print("=== ЗАПУСК ТЕСТИРОВАНИЯ НА DEV-SET ИЗ 20 ПРИМЕРОВ ===")
    
    passed_labels = 0
    passed_correctness = 0
    total = len(dev_set)
    
    for item in dev_set:
        # Проверяем метку ответа
        detected_label = classify_response(item["response"])
        label_ok = (detected_label == item["expected_label"])
        if label_ok:
            passed_labels += 1
            
        # Проверяем правильность
        detected_correct = check_correctness(
            item["category"], 
            detected_label, 
            item["response"], 
            item["gold_answer"]
        )
        correct_ok = (detected_correct == item["expected_correct"])
        if correct_ok:
            passed_correctness += 1
            
        # Если тест не прошел, выводим подробности для отладки
        if not label_ok or not correct_ok:
            print(f"\n[!] Ошибка в тесте #{item['id']} ({item['description']})")
            print(f"    Ответ модели: '{item['response']}'")
            if not label_ok:
                print(f"    Метка: ожидалась '{item['expected_label']}', определилась '{detected_label}'")
            if not correct_ok:
                print(f"    Правильность: ожидалась {item['expected_correct']}, определилась {detected_correct}")

    print("\n================ РЕЗУЛЬТАТЫ ================")
    label_accuracy = (passed_labels / total) * 100
    correctness_accuracy = (passed_correctness / total) * 100
    
    print(f"Совпадение по меткам (Label): {passed_labels}/{total} ({label_accuracy:.1f}%)")
    print(f"Совпадение по оценке правильности: {passed_correctness}/{total} ({correctness_accuracy:.1f}%)")
    
    if label_accuracy >= 85.0 and correctness_accuracy >= 85.0:
        print("\n[+] Успех! Обе оценки выше целевого порога в 85%.")
    else:
        print("\n[-] Требуется доработка списков ключевых слов в src/judge.py.")

# Запуск тестов при прямом вызове файла
if __name__ == "__main__":
    run_dev_set_tests()