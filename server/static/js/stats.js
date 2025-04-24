document.addEventListener('DOMContentLoaded', function() {
    const timeRangeSelect = document.getElementById('timeRange');
    const categorySelect = document.getElementById('category');
    const typeSelect = document.getElementById('type');
    const difficultySelect = document.getElementById('difficulty');
    const updateChartBtn = document.getElementById('updateChart');
    const resetZoomBtn = document.getElementById('resetZoom');
    const noDataMessage = document.getElementById('noDataMessage');
    
    const ctx = document.getElementById('statsChart').getContext('2d');
    let statsChart = new Chart(ctx, {
        type: 'line',
        data: { datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        tooltipFormat: 'dd.MM.yyyy HH:mm',
                        displayFormats: {
                            day: 'dd.MM.yyyy',
                            week: 'dd.MM.yyyy',
                            month: 'MM.yyyy',
                            year: 'yyyy'
                        }
                    },
                    title: { display: true, text: 'Дата' }
                },
                y: {
                    min: 0,
                    max: 100,
                    title: { display: true, text: 'Баллы' }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#FFFFFF' // Белый цвет текста легенды
                    }
                },
                zoom: {
                    zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'xy',
                    },
                    pan: {
                        enabled: true,
                        mode: 'xy',
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} баллов`;
                        }
                    },
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    backgroundColor: '#222',
                    borderColor: '#444',
                    borderWidth: 1
                }
            }
        }
    });

    categorySelect.addEventListener('change', function() {
        const selectedCategory = this.value;
        const typeOptions = typeSelect.querySelectorAll('option');
        
        typeOptions.forEach(option => {
            if (option.value === 'all') {
                option.style.display = 'block';
                return;
            }
            option.style.display = option.dataset.category === selectedCategory || selectedCategory === 'all' ? 'block' : 'none';
        });

        if (typeSelect.value !== 'all' && typeSelect.querySelector(`option[value="${typeSelect.value}"]`).style.display === 'none') {
            typeSelect.value = 'all';
        }
    });

    function getTimeRange(timeRange) {
        const now = new Date();
        switch(timeRange) {
            case 'day': return new Date(now.setDate(now.getDate() - 1)).toISOString();
            case 'week': return new Date(now.setDate(now.getDate() - 7)).toISOString();
            case 'month': return new Date(now.setMonth(now.getMonth() - 1)).toISOString();
            case 'year': return new Date(now.setFullYear(now.getFullYear() - 1)).toISOString();
            case 'all': return new Date(0).toISOString();
            default: return new Date(now.setDate(now.getDate() - 7)).toISOString();
        }
    }

    function toISODate(rawTimestamp) {
        return rawTimestamp ? new Date(rawTimestamp) : null;
    }

    async function loadStatsData() {
        const timeRange = timeRangeSelect.value;
        const category = categorySelect.value;
        const type = typeSelect.value;
        const difficulty = difficultySelect.value;
        const timeAfter = getTimeRange(timeRange);
    
        try {
            const response = await fetch(`/update_stats?time_after=${encodeURIComponent(timeAfter)}`);
            if (!response.ok) throw new Error('Ошибка загрузки данных');
    
            const data = await response.json();
            const tests = data.stats || [];
            let filteredTests = tests;
    
            if (category !== 'all') {
                const categoryTypes = Array.from(typeSelect.querySelectorAll(`option[data-category="${category}"]`)).map(opt => opt.value);
                filteredTests = filteredTests.filter(test => categoryTypes.includes(test.type_id.toString()));
            }
            if (type !== 'all') {
                filteredTests = filteredTests.filter(test => test.type_id.toString() === type);
            }
            if (difficulty !== 'all') {
                filteredTests = filteredTests.filter(test => test.difficulty === difficulty);
            }
    
            const typesMap = window.appData?.typesMap || {};
            const allData = [];
    
            // Собираем все данные в один массив
            filteredTests.forEach(test => {
                const parsedDate = toISODate(test.created_at);
                if (parsedDate) {
                    allData.push({
                        x: parsedDate.toISOString(),
                        y: test.score
                    });
                }
            });
    
            // Группируем и усредняем данные
            let groupedData = groupAndAverageData(allData, timeRange);
    
            // Создаем один график с объединенными данными
            const dataset = {
                label: 'Средний балл',  // Название графика
                data: groupedData,
                borderColor: getRandomColor(),
                backgroundColor: 'rgba(0,0,0,0.1)',
                tension: 0.1,
                pointRadius: 5,
                pointHoverRadius: 7
            };
    
            // Обновляем график
            statsChart.data.datasets = [dataset];
            statsChart.update();
    
            if (filteredTests.length === 0) {
                noDataMessage.style.display = 'block';
                document.querySelector('.chart-container').style.display = 'none';
            } else {
                noDataMessage.style.display = 'none';
                document.querySelector('.chart-container').style.display = 'block';
            }
    
        } catch (error) {
            console.error('Ошибка:', error);
            noDataMessage.textContent = 'Произошла ошибка при загрузке данных';
            noDataMessage.style.display = 'block';
            document.querySelector('.chart-container').style.display = 'none';
        }
    }
    
    function groupAndAverageData(data, timeRange) {
        const grouped = [];
        let currentGroup = [];
        let currentTime = null;
    
        // Устанавливаем нужный интервал для группировки данных
        const intervalMs = getTimeInterval(timeRange);
        let timeThreshold = null;
    
        // Определяем предел времени для группировки
        if (timeRange === 'day') {
            timeThreshold = new Date().setHours(0, 0, 0, 0); // Начало сегодняшнего дня
        } else if (timeRange === 'week') {
            timeThreshold = new Date().setDate(new Date().getDate() - 7); // Начало недели
        } else if (timeRange === 'month') {
            timeThreshold = new Date().setMonth(new Date().getMonth() - 1); // Начало месяца
        } else if (timeRange === 'year') {
            timeThreshold = new Date().setFullYear(new Date().getFullYear() - 1); // Начало года
        }
    
        // Заполняем недостающие интервалы до первого значения
        let firstTimestamp = new Date(data[0].x).getTime();
        while (firstTimestamp > timeThreshold) {
            grouped.push({
                x: new Date(timeThreshold).toISOString(),
                y: 0
            });
            timeThreshold += intervalMs; // Увеличиваем на один интервал
        }
    
        data.forEach((point, index) => {
            const timestamp = new Date(point.x).getTime();
    
            // Если точка данных находится в пределах интервала времени, добавляем её в группу
            if (timestamp >= timeThreshold) {
                currentGroup.push(point.y);
            } else {
                // Если точка данных вне интервала, усредняем текущую группу и начинаем новую
                if (currentGroup.length > 0) {
                    grouped.push({
                        x: new Date(timeThreshold).toISOString(),
                        y: currentGroup.reduce((sum, score) => sum + score, 0) / currentGroup.length
                    });
                }
                currentGroup = [point.y];
                timeThreshold = timestamp;
            }
        });
    
        // Добавляем оставшуюся группу, если есть
        if (currentGroup.length > 0) {
            grouped.push({
                x: new Date(timeThreshold).toISOString(),
                y: currentGroup.reduce((sum, score) => sum + score, 0) / currentGroup.length
            });
        }
    
        // Продлеваем последнее значение до конца временного интервала
        let lastTimestamp = new Date(grouped[grouped.length - 1].x).getTime();
        const endThreshold = new Date().getTime();
        while (lastTimestamp < endThreshold) {
            grouped.push({
                x: new Date(lastTimestamp + intervalMs).toISOString(),
                y: grouped[grouped.length - 1].y
            });
            lastTimestamp += intervalMs;
        }
    
        return grouped;
    }
    
    
    function getTimeInterval(timeRange) {
        switch (timeRange) {
            case 'day': return 24 * 60 * 60 * 1000; // 1 день в миллисекундах
            case 'week': return 7 * 24 * 60 * 60 * 1000; // 1 неделя
            case 'month': return 30 * 24 * 60 * 60 * 1000; // 1 месяц
            case 'year': return 365 * 24 * 60 * 60 * 1000; // 1 год
            default: return 24 * 60 * 60 * 1000; // По умолчанию 1 день
        }
    }
    

    function getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    updateChartBtn.addEventListener('click', loadStatsData);
    resetZoomBtn.addEventListener('click', () => statsChart && statsChart.resetZoom());

    // 🚀 Автозагрузка при изменении фильтров
    [timeRangeSelect, categorySelect, typeSelect, difficultySelect].forEach(select => {
        select.addEventListener('change', loadStatsData);
    });

    loadStatsData();
});
