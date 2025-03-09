console.log("Скрипт загружен");

let bpm;
let metronomeInterval;
let userClicks = [];
let metronomeClicks = [];
let audioContext;
let startTime;

// Начало теста
document.getElementById("start-button").addEventListener("click", startTest);

// Клики пользователя
document.getElementById("click-area").addEventListener("click", registerClick);

// Запуск теста
function startTest() {
    // Генерация случайного BPM (от 60 до 250)
    bpm = Math.floor(Math.random() * (250 - 60 + 1)) + 60;
    document.getElementById("bpm-value").innerText = bpm;

    // Очистка данных
    userClicks = [];
    metronomeClicks = [];
    document.getElementById("chart-container").innerHTML = ""; // Очистка графической визуализации

    // Инициализация AudioContext
    audioContext = new (window.AudioContext || window.webkitAudioContext)();

    // Задержка перед началом метронома (2 секунды)
    setTimeout(() => {
        playMetronome();
    }, 1000);

    // Отключение кнопки "Начать тест"
    document.getElementById("start-button").style.display = "none";
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
            metronomeClicks.push(Date.now());
            count++;
        } else {
            // Остановка метронома
            clearInterval(metronomeInterval);
            fadeOutMetronome();
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

// Постепенное затухание звука
function fadeOutMetronome() {
    const fadeTime = 2; // Время затухания (секунды)
    const gainNode = audioContext.createGain();
    const oscillator = audioContext.createOscillator();

    oscillator.frequency.value = 880; // Частота звука (A5)
    oscillator.type = "square";

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Плавное затухание
    gainNode.gain.setValueAtTime(1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + fadeTime);

    oscillator.start();
    oscillator.stop(audioContext.currentTime + fadeTime);

    // Остановка через 5 секунд после затухания
    setTimeout(stopTest, 5000);
}

// Регистрация кликов пользователя
function registerClick() {
    userClicks.push(Date.now());
}

// Остановка теста и отправка данных
function stopTest() {
    // Остановка метронома
    clearInterval(metronomeInterval);
    if (audioContext) {
        audioContext.close();
    }

    // Расчет разницы между кликами
    const differences = calculateDifferences();
    visualizeDifferences(differences); // Визуализация разницы

    // Отправка данных на сервер
    sendResults(differences);

    // Показываем кнопку "Далее"
    document.getElementById("submit-button").style.display = "block";
}

// Обработчик для кнопки "Далее"
document.getElementById("submit-button").addEventListener("click", () => {
    window.location.href = "/profile"; // Перенаправление на /profile
});

// Расчет разницы между кликами и ударами
function calculateDifferences() {
    const differences = [];

    // Проходим по каждому удару метронома
    for (let i = 0; i < metronomeClicks.length; i++) {
        const metronomeTime = metronomeClicks[i];

        // Находим ближайший клик пользователя к этому удару
        let minDifference = Infinity;
        for (let j = 0; j < userClicks.length; j++) {
            const userTime = userClicks[j];
            const difference = Math.abs(userTime - metronomeTime);

            // Если разница меньше текущей минимальной, обновляем минимальную разницу
            if (difference < minDifference) {
                minDifference = difference;
            }
        }

        // Если найден ближайший клик, добавляем разницу в массив
        if (minDifference !== Infinity) {
            differences.push(minDifference);
        } else {
            // Если клик не найден, пропускаем этот удар
            console.log(`Удар ${i + 1} пропущен: пользователь еще не начал кликать.`);
        }
    }

    return differences;
}

// Визуализация разницы
function visualizeDifferences(differences) {
    const chartContainer = document.getElementById("chart-container");
    chartContainer.innerHTML = ""; // Очистка контейнера

    differences.forEach((diff, index) => {
        // Создаем столбец
        const bar = document.createElement("div");
        bar.classList.add("bar");

        // Высота столбца пропорциональна разнице
        const barHeight = Math.min(diff / 10, 200); // Ограничиваем высоту
        bar.style.height = `${barHeight}px`;

        // Цвет столбца в зависимости от разницы
        if (diff <= 100) {
            bar.classList.add("good"); // Зеленый
        } else if (diff <= 300) {
            bar.classList.add("medium"); // Желтый
        } else {
            bar.classList.add("bad"); // Красный
        }

        // Подсказка при наведении
        bar.title = `Удар ${index + 1}: ${diff} мс`;

        // Добавляем столбец в контейнер
        chartContainer.appendChild(bar);
    });
}

// Отправка результатов на сервер
async function sendResults(differences) {
    try {
        const response = await fetch("/submit-test/rhythm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ differences: differences, bpm: bpm })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Server response:", data);

        // Отображение результата
        showResult(`Ваш результат: ${data.score}. Средняя разница: ${data.average_difference} мс.`);
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

    // Включение кнопки "Начать тест"
    document.getElementById("start-button").disabled = false;
}