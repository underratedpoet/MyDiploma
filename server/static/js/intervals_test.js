console.log("Скрипт загружен");
let testData;

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

window.onload = fetchTest;
