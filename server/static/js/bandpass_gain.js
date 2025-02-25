console.log("Скрипт загружен")
let testData;
let originalAnalyzer, processedAnalyzer;

// Запрашиваем тест
async function fetchTest() {
    console.log("fetchTest")
    const response = await fetch("/generate-test/bandpass-gain?difficulty=medium");
    testData = await response.json();

    const originalBlob = base64ToBlob(testData.original_audio);
    const processedBlob = base64ToBlob(testData.processed_audio);

    document.getElementById("original-audio").src = URL.createObjectURL(originalBlob);
    document.getElementById("processed-audio").src = URL.createObjectURL(processedBlob);

    document.getElementById("original-analyzer").parentElement.classList.add("show");
    document.getElementById("processed-analyzer").parentElement.classList.add("show");
}

// Преобразование Base64 в Blob
function base64ToBlob(base64) {
    return new Blob([new Uint8Array(atob(base64).split("").map(c => c.charCodeAt(0)))], { type: "audio/wav" });
}

// Отправка результата
function submitAnswer(event) {
    console.log("submitAnswer")
    event.preventDefault();
    
    const selectedFreq = parseFloat(document.getElementById("frequency").value);
    
    fetch("/submit-test/bandpass-gain", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ "selected_freq": selectedFreq })
    })
    .then(response => response.json())
    .then(data => {
        showResult(`Вы выбрали ${data.selected_freq} Гц. Истинное значение: ${data.real_freq} Гц. Оценка: ${data.score}`);
        showAnalyzers();
        setupAnalyzers();
    })
    .catch(error => console.error("Ошибка отправки:", error));
}

// Отображение результата
function showResult(text) {
    console.log("showResult")
    const resultContainer = document.getElementById("result-container");
    const resultText = document.getElementById("result-text");

    resultText.innerText = text;
    resultContainer.classList.add("visible");
}

// Плавное появление анализаторов
function showAnalyzers() {
    console.log("showAnalyzers");

    document.querySelectorAll(".audio-block canvas").forEach(canvas => {
        canvas.classList.add("visible");  // Отображаем сами канвасы
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
