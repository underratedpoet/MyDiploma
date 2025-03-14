console.log("Скрипт загружен");

let bpm;
let metronomeInterval;
let audioContext;

// Начало теста
document.getElementById("start-button").addEventListener("click", startTest);

// Отправка ответа
document.getElementById("submit-button").addEventListener("click", submitAnswer);

// Запуск теста
function startTest() {
    // Генерация случайного BPM (от 60 до 250)
    bpm = Math.floor(Math.random() * (250 - 60 + 1)) + 60;

    // Скрываем кнопку "Начать тест" и показываем поле для ввода BPM
    document.getElementById("start-button").style.display = "none";
    document.getElementById("bpm-input-container").style.display = "block";

    // Инициализация AudioContext
    audioContext = new (window.AudioContext || window.webkitAudioContext)();

    // Воспроизведение метронома
    playMetronome();
}

// Воспроизведение метронома
function playMetronome() {
    // Интервал метронома (в миллисекундах)
    const interval = (60 / bpm) * 1000;

    // Запуск метронома
    let count = 0;
    metronomeInterval = setInterval(() => {
        if (count < 10) { // Проигрываем 10 ударов
            playMetronomeSound();
            count++;
        } else {
            // Остановка метронома
            clearInterval(metronomeInterval);
        }
    }, interval);
}

// Воспроизведение одного удара метронома
function playMetronomeSound() {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.frequency.value = 880; // Частота звука (A5)
    oscillator.type = "square";

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Плавное увеличение и уменьшение громкости
    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(1, audioContext.currentTime + 0.01);
    gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.1);

    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.1); // Короткий звук
}

// Отправка ответа
function submitAnswer() {
    const userBpm = parseInt(document.getElementById("bpm-input").value, 10);

    if (isNaN(userBpm) || userBpm < 60 || userBpm > 250) {
        alert("Пожалуйста, введите число от 60 до 250.");
        return;
    }

    // Остановка метронома
    clearInterval(metronomeInterval);
    if (audioContext) {
        audioContext.close();
    }

    // Отправка данных на сервер
    sendResults(userBpm);
}

// Отправка результатов на сервер
async function sendResults(userBpm) {
    try {
        const response = await fetch("/submit-test/bpm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_bpm: userBpm, real_bpm: bpm })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Server response:", data);

        // Отображение результата
        showResult(`Вы ввели: ${userBpm}. Реальный BPM: ${bpm}. Оценка: ${data.score}`);
    } catch (error) {
        console.error("Ошибка отправки:", error);
        showResult("Произошла ошибка при отправке данных. Попробуйте еще раз.");
    }
}

// Отображение результата
function showResult(text) {
    const resultContainer = document.getElementById("result-container");
    const resultText = document.getElementById("result-text");

    resultText.innerText = text;
    resultContainer.classList.add("visible");

    // Меняем текст кнопки на "Далее" и перенаправляем
    const button = document.getElementById("submit-button");
    button.innerText = "Далее";
    button.onclick = function() {
        // Используем fetch для перехода на /next-test
        fetch("/next-test", {
            method: "GET",
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
}