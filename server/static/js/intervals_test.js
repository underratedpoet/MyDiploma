console.log("Скрипт загружен");
let testData;
let originalAnalyzer, processedAnalyzer;

// Запрашиваем тест
async function fetchTest() {
    console.log("fetchTest");
    const response = await fetch("/generate-test/interval?difficulty=medium");
    testData = await response.json();

    const originalBlob = base64ToBlob(testData.interval_audio);

    document.getElementById("original-audio").src = URL.createObjectURL(originalBlob);
}

// Преобразование Base64 в Blob
function base64ToBlob(base64) {
    return new Blob([new Uint8Array(atob(base64).split("").map(c => c.charCodeAt(0)))], { type: "audio/wav" });
}

// Отправка результата
function submitAnswer(event) {
    console.log("submitAnswer");
    event.preventDefault();
    
    const selectedInterval = document.getElementById("interval-select").value;
    
    fetch("/submit-test/interval", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ "selected_interval": selectedInterval })
    })
    .then(response => response.json())
    .then(data => {
        showResult(`Вы выбрали ${data.selected_interval}. Истинное значение: ${data.real_interval}. Оценка: ${data.score}`);

        // Меняем текст кнопки на "Далее" и перенаправляем
        const button = document.getElementById("submit-button");
        button.innerText = "Далее";
        button.onclick = function() {
            window.location.href = "/profile"; // Перенаправление на /profile
        };

        // Скрываем ползунок, метку и отображаемое значение
        document.getElementById("interval-select").style.display = "none";
        document.querySelector("label[for='interval']").style.display = "none"; // Скрываем label
    })
    .catch(error => console.error("Ошибка отправки:", error));
}



// Отображение результата
function showResult(text) {
    console.log("showResult");
    const resultContainer = document.getElementById("result-container");
    const resultText = document.getElementById("result-text");

    resultText.innerText = text;
    resultContainer.classList.add("visible");
}

// Плавное расширение контейнера и проявление анализаторов
function showAnalyzers() {
    console.log("showAnalyzers");

    // Плавное расширение контейнера для анализаторов
    document.querySelectorAll(".audio-block").forEach(block => {
        block.classList.add("visible");
    });

    // Плавное проявление самих анализаторов
    document.querySelectorAll(".audio-block canvas").forEach(canvas => {
        canvas.classList.add("visible");
    });
}

// Настройка анализаторов
function setupAnalyzers() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();

    originalAnalyzer = createAnalyzer(audioContext, "original-audio", "original-analyzer");
    processedAnalyzer = createAnalyzer(audioContext, "processed-audio", "processed-analyzer");
}

// Создание визуализации
function createAnalyzer(audioContext, audioId, canvasId) {
    const audioElement = document.getElementById(audioId);
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext("2d");

    const source = audioContext.createMediaElementSource(audioElement);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;

    source.connect(analyser);
    analyser.connect(audioContext.destination);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
        requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArray);

        ctx.fillStyle = "#1E1E1E";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        let x = 0;
        const barWidth = (canvas.width / bufferLength) * 2;

        for (let i = 0; i < bufferLength; i++) {
            const barHeight = dataArray[i] * 0.8;
            ctx.fillStyle = `rgb(${barHeight + 100}, 50, 200)`;
            ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            x += barWidth + 1;
        }
    }

    draw();
    return analyser;
}

window.onload = fetchTest;
