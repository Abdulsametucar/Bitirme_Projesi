document.addEventListener('DOMContentLoaded', () => {

    let successChart = null;
    let gaugeChart = null;

    function initCharts() {
        // Doughnut Chart (İşlem Başarı Durumu)
        const successCtx = document.getElementById('successChart').getContext('2d');
        successChart = new Chart(successCtx, {
            type: 'doughnut',
            data: {
                labels: ['Başarılı', 'Hatalı'],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: ['#198754', '#dc3545'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#e0e0e0', font: { family: 'Inter' } } }
                },
                cutout: '75%'
            }
        });

        // Gauge Chart (Yarım-Doughnut Ortalama Süre)
        const gaugeCtx = document.getElementById('gaugeChart').getContext('2d');
        gaugeChart = new Chart(gaugeCtx, {
            type: 'doughnut',
            data: {
                labels: ['Ortalama Süre', 'Hedef Süre (Fark)'],
                datasets: [{
                    data: [0, 15], // 15 saniye hedef varsayalım
                    backgroundColor: ['#0dcaf0', 'rgba(255,255,255,0.05)'],
                    borderWidth: 0,
                    circumference: 180,
                    rotation: -90
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: true }
                },
                cutout: '80%'
            }
        });
    }

    const updateStats = () => {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                // DOM Elements
                const chartTotalOpsEl = document.getElementById('chart_total_ops');
                const chartAvgTimeEl = document.getElementById('chart_avg_time');
                const lastUpdatedEl = document.getElementById('last_updated');
                const tableBody = document.getElementById('worker_table_body');

                // Update Overview Values in Chart Headers
                updateValueWithAnimation(chartTotalOpsEl, data.toplam_islem.toString());
                updateValueWithAnimation(chartAvgTimeEl, `${data.ortalama_sure_saniye}s`);

                // Update Charts
                if (successChart) {
                    successChart.data.datasets[0].data = [data.basarili, data.hatali];
                    // Basari oranini ortasina veya tooltip'e ekleyebiliriz. ChartJS update cagrilir
                    successChart.update();
                }

                if (gaugeChart) {
                    let avg = data.ortalama_sure_saniye;
                    let target = 15.0; // optimum 15 sn dedik
                    // Eger ortalama sure hedeften buyukse, kirmizi yapalim, degilse mavi
                    let color = avg > target ? '#dc3545' : '#0dcaf0';
                    let remaining = target - avg;
                    if (remaining < 0) remaining = 0; // Eger target'i gectiysek full dolsun
                    gaugeChart.data.datasets[0].backgroundColor[0] = color;
                    gaugeChart.data.datasets[0].data = [avg, Math.max(target - avg, target * 0.1)]; 
                    // İkinci parametre sadece boslugu gostermek icindir.
                    gaugeChart.update();
                }

                // Update Last Updated Text
                const now = new Date();
                lastUpdatedEl.innerText = `Son Güncelleme: ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

                // Update Worker Table
                tableBody.innerHTML = ''; // Clear current rows

                if (data.son_adimlar && data.son_adimlar.length > 0) {
                    data.son_adimlar.forEach(adim => {
                        const tr = document.createElement('tr');

                        tr.innerHTML = `
                            <td class="ps-3 fw-medium">
                                <div class="d-flex align-items-center">
                                    <div class="bg-secondary rounded-circle d-flex justify-content-center align-items-center me-3" style="width: 32px; height: 32px;">
                                        <i class="fa-solid fa-user text-light small"></i>
                                    </div>
                                    ${adim.isci_ad_soyad}
                                </div>
                            </td>
                            <td>${adim.adim_adi}</td>
                            <td class="text-end pe-3 fw-bold text-info">${adim.gecen_sure_saniye.toFixed(2)}</td>
                        `;
                        tableBody.appendChild(tr);
                    });
                } else {
                    tableBody.innerHTML = `
                        <tr>
                            <td colspan="3" class="text-center text-muted py-4">
                                <i class="fa-solid fa-circle-info me-2"></i> Henüz kayıtlı işlem bulunmuyor.
                            </td>
                        </tr>
                    `;
                }
            })
            .catch(error => {
                console.error("Stats fetching error:", error);
                document.getElementById('last_updated').innerText = 'Bağlantı Hatası!';
                document.getElementById('last_updated').classList.add('text-danger');
            });
    };

    // Helper to animate value changes
    function updateValueWithAnimation(element, newValue) {
        if (element && element.innerText !== newValue) {
            element.innerText = newValue;
            element.classList.remove('value-updated');
            // Trigger reflow to restart animation
            void element.offsetWidth;
            element.classList.add('value-updated');
        }
    }

    // Initial fetch
    initCharts();
    updateStats();

    // Fetch every 3 seconds
    setInterval(updateStats, 3000);
});
