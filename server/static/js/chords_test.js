console.log("Скрипт загружен");
let testData;

// Запрашиваем тест
async function fetchTest() {
    console.log("fetchTest");
    const response = await fetch("/generate-test/chords?difficulty=medium");
    testData = await response.json();

    // Воспроизведение аудио
    const originalBlob = base64ToBlob(testData.chords_audio);
    document.getElementById("original-audio").src = URL.createObjectURL(originalBlob);

    // Динамическое создание выпадающих списков
    createSelectElements(testData.steps);

    console.log("fetchTest выполнен");
}

// Преобразование Base64 в Blob
function base64ToBlob(base64) {
    return new Blob([new Uint8Array(atob(base64).split("").map(c => c.charCodeAt(0)))], { type: "audio/wav" });
}

// Создание выпадающих списков
function createSelectElements(steps) {
    const container = document.getElementById("steps-container");

    steps.forEach((step, index) => {
        // Создаем контейнер для каждого выпадающего списка
        const div = document.createElement("div");

        // Создаем метку
        const label = document.createElement("label");
        label.setAttribute("for", `step-${index + 1}`);
        label.innerText = `Аккорд ${index + 1}:`;
        div.appendChild(label);

        // Создаем выпадающий список
        const select = document.createElement("select");
        select.setAttribute("id", `step-${index + 1}`);
        select.setAttribute("name", `step-${index + 1}`);

        // Делаем первый и последний выпадающий список неизменяемыми
        if (index === 0 || index === steps.length - 1) {
            select.setAttribute("disabled", "disabled");
        }

        // Добавляем опции (от 1 до 6)
        for (let i = 1; i <= 6; i++) {
            const option = document.createElement("option");
            option.setAttribute("value", i);
            option.innerText = i;
            select.appendChild(option);
        }

        div.appendChild(select);
        container.appendChild(div);
    });
}

// Отправка результата
async function submitAnswer(event) {
    console.log("submitAnswer");
    event.preventDefault();

    // Собираем выбранные значения
    const selectedSteps = [];
    const selects = document.querySelectorAll("#steps-container select");
    selects.forEach(select => {
        selectedSteps.push(parseInt(select.value, 10));
    });

    // Отправляем данные на сервер
    try {
        const response = await fetch("/submit-test/chords", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ selected_steps: selectedSteps })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Server response:", data);

        // Отображение результата
        showResult(`Вы выбрали ${data.selected_steps.join(", ")}. Истинное значение: ${data.real_steps.join(", ")}. Оценка: ${data.score}`);

        // Меняем текст кнопки на "Далее" и перенаправляем
        const button = document.getElementById("submit-button");
        button.innerText = "Далее";
        button.onclick = function() {
            // Используем fetch для перехода на /next-test
            fetch("/next-test", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: new URLSearchParams({ "score": data.score }), 
                credentials: "include"  // Включаем передачу cookies
            })
            .then(response => {
                if (response.redirected) {
                    // Если сервер вернул редирект, переходим по новому URL
                    window.location.href = response.url;
                } else {
                    // Обрабатываем другие ответы (например, JSON)
                    return response.json();
                }
            })
            .then(data => {
                if (data && data.average_score) {
                    // Если тесты завершены, показываем результаты
                    window.location.href = "/test-results";
                }
            })
            .catch(error => console.error("Ошибка перехода:", error));
        };

        // Скрываем выпадающие списки
        document.getElementById("steps-container").style.display = "none";
    } catch (error) {
        console.error("Ошибка отправки:", error);
        showResult("Произошла ошибка при отправке данных. Попробуйте еще раз.");
    }
}

// Отображение результата
function showResult(text) {
    console.log("showResult");
    const resultContainer = document.getElementById("result-container");
    const resultText = document.getElementById("result-text");

    resultText.innerText = text;
    resultContainer.classList.add("visible");
}

window.onload = fetchTest;