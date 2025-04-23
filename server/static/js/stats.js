document.addEventListener('DOMContentLoaded', function() {
    // Элементы управления
    const timeRangeSelect = document.getElementById('timeRange');
    const categorySelect = document.getElementById('category');
    const typeSelect = document.getElementById('type');
    const difficultySelect = document.getElementById('difficulty');
    const updateChartBtn = document.getElementById('updateChart');
    const resetZoomBtn = document.getElementById('resetZoom');
    const noDataMessage = document.getElementById('noDataMessage');
    
    // Инициализация графика
    const ctx = document.getElementById('statsChart').getContext('2d');
    let statsChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: []
        },
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
                    title: {
                        display: true,
                        text: 'Дата'
                    }
                },
                y: {
                    min: 0,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Баллы'
                    }
                }
            },
            plugins: {
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true
                        },
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
                    }
                }
            }
        }
    });
    
    // Фильтрация типов тестов по категории
    categorySelect.addEventListener('change', function() {
        const selectedCategory = this.value;
        const typeOptions = typeSelect.querySelectorAll('option');
        
        typeOptions.forEach(option => {
            if (option.value === 'all') {
                option.style.display = 'block';
                return;
            }
            
            if (selectedCategory === 'all' || option.dataset.category === selectedCategory) {
                option.style.display = 'block';
            } else {
                option.style.display = 'none';
            }
        });
        
        // Сброс выбора типа, если он стал невидимым
        if (typeSelect.value !== 'all' && typeSelect.querySelector(`option[value="${typeSelect.value}"]`).style.display === 'none') {
            typeSelect.value = 'all';
        }
    });
    
    // Функция для получения временного диапазона
    function getTimeRange(timeRange) {
        const now = new Date();
        
        switch(timeRange) {
            case 'day':
                return new Date(now.setDate(now.getDate() - 1)).toISOString();
            case 'week':
                return new Date(now.setDate(now.getDate() - 7)).toISOString();
            case 'month':
                return new Date(now.setMonth(now.getMonth() - 1)).toISOString();
            case 'year':
                return new Date(now.setFullYear(now.getFullYear() - 1)).toISOString();
            case 'all':
                return new Date(0).toISOString();
            default:
                return new Date(now.setDate(now.getDate() - 7)).toISOString();
        }
    }
    
    // Функция для загрузки данных
    async function loadStatsData() {
        const timeRange = timeRangeSelect.value;
        const category = categorySelect.value;
        const type = typeSelect.value;
        const difficulty = difficultySelect.value;
        
        const timeAfter = getTimeRange(timeRange);
        
        try {
            const response = await fetch(`/update_stats?time_after=${encodeURIComponent(timeAfter)}`);
            if (!response.ok) {
                throw new Error('Ошибка загрузки данных');
            }
            
            const data = await response.json();
            const tests = data.stats || [];
            
            // Фильтрация данных
            let filteredTests = tests;
            
            if (category !== 'all') {
                const categoryTypes = Array.from(typeSelect.querySelectorAll(`option[data-category="${category}"]`))
                    .map(opt => opt.value);
                filteredTests = filteredTests.filter(test => categoryTypes.includes(test.type_id.toString()));
            }
            
            if (type !== 'all') {
                filteredTests = filteredTests.filter(test => test.type_id.toString() === type);
            }
            
            if (difficulty !== 'all') {
                filteredTests = filteredTests.filter(test => test.difficulty === difficulty);
            }
            
            // Группировка по типу теста
            const typesMap = window.appData?.typesMap || {};
            
            const groupedData = {};
            filteredTests.forEach(test => {
                if (!groupedData[test.type_id]) {
                    groupedData[test.type_id] = {
                        label: typesMap[test.type_id] || `Тип ${test.type_id}`,
                        data: [],
                        borderColor: getRandomColor(),
                        backgroundColor: 'rgba(0, 0, 0, 0.1)',
                        tension: 0.1,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    };
                }
                
                groupedData[test.type_id].data.push({
                    x: new Date(test.timestamp || new Date()).toISOString(),
                    y: test.score
                });
            });
            
            // Обновление графика
            statsChart.data.datasets = Object.values(groupedData);
            statsChart.update();
            
            // Показываем сообщение, если нет данных
            if (filteredTests.length === 0) {
                noDataMessage.style.display = 'block';
                document.querySelector('.chart-container').style.display = 'none';
            } else {
                noDataMessage.style.display = 'none';
                document.querySelector('.chart-container').style.display = 'block';
            }
            
        } 
        catch (error) {
            console.error('Ошибка:', error);
            noDataMessage.textContent = 'Произошла ошибка при загрузке данных';
            noDataMessage.style.display = 'block';
            document.querySelector('.chart-container').style.display = 'none';
        }
    }
    
    // Генерация случайного цвета
    function getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }
    
    // Обработчики событий
    updateChartBtn.addEventListener('click', loadStatsData);
    
    resetZoomBtn.addEventListener('click', function() {
        if (statsChart) {
            statsChart.resetZoom();
        }
    });
    
    // Первоначальная загрузка данных
    loadStatsData();
});