document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://127.0.0.1:8000';
    const userToken = localStorage.getItem('userToken');

    const isDashboardPage = window.location.pathname.includes('dashboard.html');
    const isReportsPage = window.location.pathname.includes('reports.html');
    const isAdminPage = window.location.pathname.includes('admin.html');
    const isIndexPage = !isDashboardPage && !isReportsPage && !isAdminPage;

    if ((isDashboardPage || isReportsPage || isAdminPage) && !userToken) {
        window.location.href = 'index.html';
        return;
    }
    if (isIndexPage && userToken) {
        window.location.href = 'dashboard.html';
        return;
    }

    function handleLogout() {
        localStorage.removeItem('userToken');
        localStorage.removeItem('userEmail');
        window.location.href = 'index.html';
    }
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);

    const homeBtn = document.getElementById('home-btn');
    if (homeBtn) homeBtn.addEventListener('click', () => window.location.href = 'dashboard.html');

    const prevPageBtn = document.getElementById('prev-page-btn');
    if (prevPageBtn) prevPageBtn.addEventListener('click', () => window.history.back());


    // --- LOGIC FOR INDEX.HTML(Landing Page) ---
    if (isIndexPage) {
        const loginHeroBtn = document.getElementById('login-hero-btn');
        const registerNavBtn = document.getElementById('register-nav-btn');
        const adminNavBtn = document.getElementById('admin-nav-btn');
        const loginModalOverlay = document.getElementById('login-modal-overlay');
        const registerModalOverlay = document.getElementById('register-modal-overlay');
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');

        function hideAllModals() {
            if (loginModalOverlay) loginModalOverlay.classList.add('hidden');
            if (registerModalOverlay) registerModalOverlay.classList.add('hidden');
        }

        function showModal(modalOverlay) {
            hideAllModals();
            if (modalOverlay) modalOverlay.classList.remove('hidden');
        }

        if (loginHeroBtn) loginHeroBtn.addEventListener('click', () => showModal(loginModalOverlay));
        if (registerNavBtn) registerNavBtn.addEventListener('click', () => showModal(registerModalOverlay));
        if (adminNavBtn) adminNavBtn.addEventListener('click', () => {
             alert("管理者ダッシュボードにアクセスするには、管理者アカウントでログインしてください。");
             showModal(document.getElementById('login-modal-overlay'));
        });

        if (loginModalOverlay) loginModalOverlay.addEventListener('click', (e) => { if (e.target === loginModalOverlay) hideAllModals(); });
        if (registerModalOverlay) registerModalOverlay.addEventListener('click', (e) => { if (e.target === registerModalOverlay) hideAllModals(); });

        if (loginForm) loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);
            try {
                const response = await fetch(`${API_URL}/token`, { method: 'POST', body: formData });
                if (!response.ok) throw new Error('ログインに失敗しました。');
                const data = await response.json();
                localStorage.setItem('userToken', data.access_token);
                localStorage.setItem('userEmail', data.user_email);
                if (data.is_admin) {
                    window.location.href = 'admin.html';
                } else {
                    window.location.href = 'dashboard.html';
                }
            } catch (error) {
                alert(error.message);
            }
        });

        if (registerForm) registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const rePassword = document.getElementById('register-re-password').value;
            if (password !== rePassword) {
                alert("パスワードが一致しません！");
                return;
            }
            try {
                const response = await fetch(`${API_URL}/users/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                if (!response.ok) throw new Error('登録に失敗しました。');
                alert('登録に成功しました！ログインしてください。');
                hideAllModals();
                showModal(loginModalOverlay);
            } catch (error) {
                alert(error.message);
            }
        });
    }

    // --- LOGIC FOR DASHBOARD.HTML ---
    if (isDashboardPage) {
        const viewAllBtn = document.getElementById('view-all-btn');
        if (viewAllBtn) viewAllBtn.addEventListener('click', () => window.location.href = 'reports.html');
        
        // --- FULLSCREEN LOGIC ---
        const spendingCard = document.getElementById("spending-dashboard-card");
        const fullscreenBtn = document.getElementById("fullscreen-btn");
        if (fullscreenBtn && spendingCard) {
            fullscreenBtn.addEventListener("click", () => {
                if (!document.fullscreenElement) {
                    spendingCard.requestFullscreen().catch(err => {
                        alert(`フルスクリーンにしようとしてエラーが発生しました ${err.message} (${err.name})`);
                    });
                } else {
                    document.exitFullscreen();
                }
            });
        }

        const uploadForm = document.getElementById('dashboard-upload-form');
        const uploadResult = document.getElementById('dashboard-upload-result');
        const uploadButton = document.getElementById('dashboard-upload-btn');
        const recentActivityList = document.getElementById('recent-activity-list');
        const startDateInput = document.getElementById('start-date');
        const endDateInput = document.getElementById('end-date');

        // --- FILE INPUT NAME DISPLAY ---
        const fileInput = document.getElementById('dashboard-receipt-file');
        const fileNameSpan = document.getElementById('file-name');

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                fileNameSpan.textContent = fileInput.files[0].name;
            } else {
                fileNameSpan.textContent = "ファイルが選択されていません";
            }
        });

        let categoryChart = null;
        let timeSeriesChart = null;

        async function fetchDashboardData() {
            const startDate = startDateInput.value;
            const endDate = endDateInput.value;
            let queryParams = '';
            if (startDate && endDate) {
                queryParams = `?start_date=${startDate}&end_date=${endDate}`;
            }

            try {
                const [kpiRes, categoryRes, timeRes, topItemsRes] = await Promise.all([
                    fetch(`${API_URL}/api/dashboard/kpis${queryParams}`, { headers: { 'Authorization': `Bearer ${userToken}` }}),
                    fetch(`${API_URL}/api/dashboard/chart-data${queryParams}`, { headers: { 'Authorization': `Bearer ${userToken}` }}),
                    fetch(`${API_URL}/api/dashboard/time-series${queryParams}`, { headers: { 'Authorization': `Bearer ${userToken}` }}),
                    fetch(`${API_URL}/api/dashboard/top-items${queryParams}`, { headers: { 'Authorization': `Bearer ${userToken}` }})
                ]);

                const kpis = await kpiRes.json();
                document.getElementById('total-spend-kpi').textContent = `¥${kpis.total_spend.toFixed(2)}`;
                document.getElementById('total-tax-kpi').textContent = `¥${kpis.total_tax.toFixed(2)}`;
                document.getElementById('total-bills-kpi').textContent = kpis.total_bills;

                const categoryData = await categoryRes.json();
                renderCategoryChart(categoryData);

                const timeData = await timeRes.json();
                renderTimeSeriesChart(timeData);
                
                const topItemsData = await topItemsRes.json();
                renderTopItems(topItemsData);

            } catch (error) {
                console.error("ダッシュボード取得エラー:", error);
            }
        }
        // Function to draw the "Spending by Category" pie chart
        function renderCategoryChart(chartData) {
            const categoryTranslations = {
                "Groceries": "食料品",
                "Dining Out": "外食",
                "Shopping": "ショッピング",
                "Fuel": "燃料",
                "Entertainment": "エンターテイメント",
                "Travel": "旅行",
                "Utilities": "光熱費",
                "Online Shopping" : "オンラインショッピング",
                "Other": "その他"
            };
            const labels = chartData.map(item => categoryTranslations[item.label] || item.label);
            const values = chartData.map(item => item.value);
            const ctx = document.getElementById('categoryChart').getContext('2d');
            if (categoryChart) categoryChart.destroy();
            categoryChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'カテゴリ別支出',
                        data: values,
                        backgroundColor: ['rgba(13, 14, 14,1)', 'rgba(68, 66, 66, 1)', 'rgba(93, 89, 89, 1)','rgba(171,163,167,1)',],
                    }]
                }
            });
        }

        function renderTimeSeriesChart(timeData) {
            const labels = timeData.map(item => item.label);
            const values = timeData.map(item => item.value);
            const ctx = document.getElementById('timeSeriesChart').getContext('2d');
            if (timeSeriesChart) timeSeriesChart.destroy();
            timeSeriesChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '月別支出',
                        data: values,
                        backgroundColor: 'rgba(44, 41, 41, 1)',
                    }]
                },
                options: {
                    responsive: false,
                    maintainAspectRatio: false
                }
            });
        }

        function renderTopItems(items) {
            const list = document.getElementById('top-items-list');
            if (items.length === 0) {
                list.innerHTML = '<p>の期間に表示する項目はありません。</p>';
                return;
            }
            let html = '<ul>';
            items.forEach(item => {
                html += `<li><span>${item.label}</span> <strong>¥${item.value.toFixed(2)}</strong></li>`;
            });
            html += '</ul>';
            list.innerHTML = html;
        }

        async function fetchAndDisplayReceipts() {
            recentActivityList.innerHTML = '<p>最近のアクティビティを読み込んでいます…</p>';
            try {
                const response = await fetch(`${API_URL}/api/receipts/`, { headers: { 'Authorization': `Bearer ${userToken}` } });
                if (!response.ok) throw new Error('レシートを取得できませんでした。');
                const receipts = await response.json();
                if (receipts.length === 0) {
                    recentActivityList.innerHTML = '<p>表示する最近のアクティビティはありません。</p>';
                    return;
                }
                let html = '<ul>';
                receipts.forEach(receipt => {
                    const uploadDate = new Date(receipt.upload_date).toLocaleDateString();
                    html += `<li><strong>${receipt.seller_name}</strong> (アップロード済み: ${uploadDate}) - ¥${receipt.total_amount.toFixed(2)}</li>`;
                });
                html += '</ul>';
                recentActivityList.innerHTML = html;
            } catch (error) {
                recentActivityList.innerHTML = `<p class="error-message">${error.message}</p>`;
            }
        }

        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            uploadResult.innerHTML = '';
            uploadButton.disabled = true;
            uploadButton.textContent = '処理中…';
            const fileInput = document.getElementById('dashboard-receipt-file');
            const file = fileInput.files[0];
            if (!file) {
                uploadResult.textContent = 'ファイルを選択してください。';
                uploadButton.disabled = false;
                uploadButton.textContent = 'アップロードして処理';
                return;
            }
            const formData = new FormData();
            formData.append('file', file);
            try {
                const response = await fetch(`${API_URL}/api/receipts/`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${userToken}` },
                    body: formData
                });
                if (!response.ok) throw new Error('アップロードに失敗しました。');
                uploadResult.innerHTML = `<p style="color: green;">アップロード成功！</p>`;
                fetchAndDisplayReceipts();
                fetchDashboardData();
            } catch (error) {
                uploadResult.innerHTML = `<p class="error-message">${error.message}</p>`;
            } finally {
                uploadButton.disabled = false;
                uploadButton.textContent = 'アップロードして処理';
            }
        });

        startDateInput.addEventListener('change', fetchDashboardData);
        endDateInput.addEventListener('change', fetchDashboardData);

        fetchAndDisplayReceipts();
        fetchDashboardData();
    }

    // --- LOGIC FOR REPORTS.HTML ---
    if (isReportsPage) {
        const tableBody = document.getElementById('receipts-table-body');
        const searchBar = document.getElementById('search-bar');
        const downloadBtn = document.getElementById('download-csv-btn');
        let allReceipts = [];

        async function fetchAllReceipts() {
            tableBody.innerHTML = '<tr><td colspan="6">レシートを読み込み中…</td></tr>';
            try {
                const response = await fetch(`${API_URL}/api/receipts/all`, {
                    headers: { 'Authorization': `Bearer ${userToken}` }
                });
                if (!response.ok) throw new Error('レシートを取得できませんでした。');
                allReceipts = await response.json();
                renderTable(allReceipts);
            } catch (error) {
                tableBody.innerHTML = `<tr><td colspan="6" class="error-message">${error.message}</td></tr>`;
            }
        }

        function renderTable(receipts) {
            if (receipts.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="6">レシートが見つかりません。</td></tr>';
                return;
            }
            tableBody.innerHTML = receipts.map(receipt => `
                <tr data-receipt-id="${receipt.id}">
                    <td>${receipt.seller_name}</td>
                    <td>${receipt.category}</td>
                    <td>${new Date(receipt.receipt_date).toLocaleDateString()}</td>
                    <td>${new Date(receipt.upload_date).toLocaleDateString()}</td>
                    <td>${receipt.total_amount.toFixed(2)}</td>
                    <td>
                        <button class="delete-btn" data-id="${receipt.id}">削除</button>
                    </td>
                </tr>
            `).join('');
        }
        
        async function handleDelete(receiptId) {
            if (!confirm("この領収書を削除してもよろしいですか？この操作は元に戻せません。")) {
                return;
            }
            try {
                const response = await fetch(`${API_URL}/api/receipts/${receiptId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${userToken}` }
                });
                if (!response.ok) throw new Error('領収書を削除できませんでした。');
                
                const rowToDelete = tableBody.querySelector(`tr[data-receipt-id="${receiptId}"]`);
                if (rowToDelete) rowToDelete.remove();

            } catch (error) {
                alert(error.message);
            }
        }

        tableBody.addEventListener('click', (event) => {
            if (event.target && event.target.classList.contains('delete-btn')) {
                const receiptId = event.target.getAttribute('data-id');
                handleDelete(receiptId);
            }
        });

        function filterTable() {
            const searchTerm = searchBar.value.toLowerCase();
            const filteredReceipts = allReceipts.filter(receipt =>
                receipt.seller_name.toLowerCase().includes(searchTerm)
            );
            renderTable(filteredReceipts);
        }

        function downloadCSV() {
            const rows = Array.from(tableBody.querySelectorAll('tr'));
            if (rows.length === 0 || rows[0].children.length <= 1) {
                alert("ダウンロードするデータがありません。");
                return;
            }
            const headers = ['Seller Name', 'Category', 'Receipt Date', 'Upload Date', 'Total Amount'];
            let csvContent = "data:text/csv;charset=utf-8," + headers.join(',') + '\n';
            rows.forEach(row => {
                const rowData = Array.from(row.children).map(cell => `"${cell.textContent.trim()}"`).slice(0, 5);
                csvContent += rowData.join(',') + '\n';
            });
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "receipts_report.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        searchBar.addEventListener('keyup', filterTable);
        downloadBtn.addEventListener('click', downloadCSV);
        fetchAllReceipts();
    }
    
    // --- LOGIC FOR ADMIN.HTML ---
    if (isAdminPage) {
        const usersTableBody = document.getElementById('users-table-body');
        const receiptsTableBody = document.getElementById('all-receipts-table-body');
        const userSearchBar = document.getElementById('user-search-bar');
        const receiptSearchBar = document.getElementById('receipt-search-bar');

        let allUsers = [];
        let allReceipts = [];

        async function fetchAdminData() {
            try {
                const usersResponse = await fetch(`${API_URL}/api/admin/users`, {
                    headers: { 'Authorization': `Bearer ${userToken}` }
                });
                if (!usersResponse.ok) {
                    if (usersResponse.status === 403) throw new Error('このページを表示する権限がありません。');
                    throw new Error('ユーザーを取得できませんでした。');
                }
                allUsers = await usersResponse.json();
                renderUsersTable(allUsers);
            } catch (error) {
                document.querySelector('main').innerHTML = `<h1 style="color: red; text-align: center;">${error.message}</h1>`;
                return;
            }

            try {
                const receiptsResponse = await fetch(`${API_URL}/api/admin/receipts`, {
                    headers: { 'Authorization': `Bearer ${userToken}` }
                });
                if (!receiptsResponse.ok) throw new Error('レシートを取得できませんでした。');
                allReceipts = await receiptsResponse.json();
                renderReceiptsTable(allReceipts);
            } catch (error) {
                receiptsTableBody.innerHTML = `<tr><td colspan="6" class="error-message">${error.message}</td></tr>`;
            }
        }

        function renderUsersTable(users) {
            usersTableBody.innerHTML = users.map(user => `
                <tr data-user-id="${user.id}">
                    <td>${user.id}</td>
                    <td>${user.email}</td>
                    <td>${user.is_admin ? 'Yes' : 'No'}</td>
                    <td>
                        <button class="delete-btn" data-id="${user.id}" ${user.is_admin ? 'disabled' : ''}>削除</button>
                    </td>
                </tr>
            `).join('');
        }
        
        function renderReceiptsTable(receipts) {
            if (!receipts || receipts.length === 0) {
                receiptsTableBody.innerHTML = '<tr><td colspan="6">No receipts found for any user.</td></tr>';
                return;
            }
            receiptsTableBody.innerHTML = receipts.map(receipt => `
                <tr>
                    <td>${receipt.id}</td>
                    <td>${receipt.owner ? receipt.owner.email : `User ID: ${receipt.owner_id}`}</td>
                    <td>${receipt.seller_name}</td>
                    <td>${receipt.category}</td>
                    <td>${new Date(receipt.upload_date).toLocaleDateString()}</td>
                </tr>
            `).join('');
        }

        async function handleDeleteUser(userId) {
            if (!confirm("このユーザーとそのすべてのデータを削除してもよろしいですか？この操作は元に戻せません。")) return;
            try {
                const response = await fetch(`${API_URL}/api/admin/users/${userId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${userToken}` }
                });
                if (!response.ok) {
                     const errorData = await response.json();
                     throw new Error(errorData.detail || 'ユーザーの削除に失敗しました。');
                }
                const rowToDelete = usersTableBody.querySelector(`tr[data-user-id="${userId}"]`);
                if (rowToDelete) rowToDelete.remove();
            } catch (error) {
                alert(error.message);
            }
        }

        usersTableBody.addEventListener('click', (event) => {
            if (event.target && event.target.classList.contains('delete-btn')) {
                const userId = event.target.getAttribute('data-id');
                handleDeleteUser(userId);
            }
        });

        userSearchBar.addEventListener('keyup', () => {
            const searchTerm = userSearchBar.value.toLowerCase();
            const filteredUsers = allUsers.filter(user => 
                user.email.toLowerCase().includes(searchTerm)
            );
            renderUsersTable(filteredUsers);
        });
        
        receiptSearchBar.addEventListener('keyup', () => {
            const searchTerm = receiptSearchBar.value.toLowerCase();
            const filteredReceipts = allReceipts.filter(receipt => 
                receipt.seller_name.toLowerCase().includes(searchTerm)
            );
            renderReceiptsTable(filteredReceipts);
        });

        fetchAdminData();
    }
});