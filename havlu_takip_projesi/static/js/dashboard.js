document.addEventListener('DOMContentLoaded', () => {
    
    const updateStats = () => {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                // DOM Elements
                const totalOpsEl = document.getElementById('total_ops');
                const successRateEl = document.getElementById('success_rate');
                const avgTimeEl = document.getElementById('avg_time');
                const totalErrorsEl = document.getElementById('total_errors');
                const lastUpdatedEl = document.getElementById('last_updated');
                const tableBody = document.getElementById('worker_table_body');

                // Update Overview Cards with flash animation if value changed
                updateValueWithAnimation(totalOpsEl, data.toplam_islem.toString());
                updateValueWithAnimation(successRateEl, `%${data.basari_orani}`);
                updateValueWithAnimation(avgTimeEl, `${data.ortalama_sure_saniye}s`);
                updateValueWithAnimation(totalErrorsEl, data.hatali.toString());

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
        if (element.innerText !== newValue) {
            element.innerText = newValue;
            element.classList.remove('value-updated');
            // Trigger reflow to restart animation
            void element.offsetWidth;
            element.classList.add('value-updated');
        }
    }

    // Initial fetch
    updateStats();

    // Fetch every 3 seconds
    setInterval(updateStats, 3000);
});
