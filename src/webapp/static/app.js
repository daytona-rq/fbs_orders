// app/webapp/static/app.js
document.addEventListener('DOMContentLoaded', function() {
    const tg = window.Telegram?.WebApp;
    if (!tg) {
        console.error('Telegram WebApp не обнаружен! Откройте через бота.');
        return;
    }

    tg.ready();
    tg.expand();

    const chatId = tg.initDataUnsafe?.user?.id || tg.initDataUnsafe?.chat?.id;
    if (!chatId) {
        tg.showAlert('Ошибка: не удалось получить chat_id. Пожалуйста, откройте через бота.');
        console.error('chat_id не найден в:', tg.initDataUnsafe);
        return;
    }

    // Поддержка тёмной темы
    const isDark = tg.colorScheme === 'dark';
    if (isDark) {
        document.documentElement.style.setProperty('--bg-color', '#1e1e1e');
        document.documentElement.style.setProperty('--text-color', '#f0f0f0');
        document.documentElement.style.setProperty('--container-bg', '#2a2a2a');
    }

    let productsData = [];

    fetchProducts();

    function showSpinner() {
        const tbody = document.getElementById('productsBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="2" class="spinner">Загрузка...</td></tr>`;
        }
    }

    function renderEmptyMessage() {
        const tbody = document.getElementById('productsBody');
        tbody.innerHTML = `<tr><td colspan="2" class="spinner">Ничего не найдено</td></tr>`;
    }

    async function fetchProducts(search = '') {
        try {
            showSpinner();
            const url = new URL('/api/articles', window.location.origin);
            url.searchParams.set('chat_id', chatId);
            if (search) url.searchParams.set('search', search);

            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            productsData = await response.json();
            if (productsData.length === 0) renderEmptyMessage();
            else renderProducts(productsData);
        } catch (error) {
            console.error('Ошибка при загрузке данных:', error);
            tg.showAlert(`Ошибка загрузки: ${error.message}`);
        }
    }

    let searchTimeout;
    function searchProducts() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const searchTerm = document.getElementById('searchInput').value;
            fetchProducts(searchTerm);
        }, 300);
    }

    function renderProducts(products) {
        const tbody = document.getElementById('productsBody');
        if (!tbody) return;

        tbody.innerHTML = products.map(product => `
            <tr>
                <td>${product.article_code || product.article || 'N/A'}</td>
                <td>
                    <input type="number" 
                           step="0.01" 
                           value="${product.cost ?? ''}" 
                           data-id="${product.id}"
                           onchange="handleCostChange(event)">
                </td>
            </tr>
        `).join('');
    }

    function flashInput(input, className) {
        input.classList.add(className);
        setTimeout(() => input.classList.remove(className), 1500);
    }

    window.handleCostChange = async function(event) {
        const input = event.target;
        const articleId = input.dataset.id;
        const newCost = input.value ? parseFloat(input.value) : null;
        
        try {
            const response = await fetch(`/api/articles/${articleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ cost: newCost })
            });
            
            if (!response.ok) {
                throw new Error(await response.text());
            }
            
            const updatedProduct = await response.json();
            input.value = updatedProduct.cost ?? '';
            
            const productIndex = productsData.findIndex(p => p.id == articleId);
            if (productIndex !== -1) {
                productsData[productIndex].cost = updatedProduct.cost;
            }

            flashInput(input, 'updated');

        } catch (error) {
            console.error('Ошибка при обновлении:', error);
            const product = productsData.find(p => p.id == articleId);
            input.value = product?.cost ?? '';
            flashInput(input, 'error');
            tg.showAlert('Ошибка сохранения: ' + error.message);
        }
    };

    window.searchProducts = searchProducts;

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', searchProducts);
    }

    // Сортировка по клику на заголовки
    let sortAsc = true;
    document.querySelectorAll('th').forEach((th, index) => {
        th.addEventListener('click', () => {
            if (index === 0) {
                productsData.sort((a, b) => {
                    const valA = a.article_code || a.article || '';
                    const valB = b.article_code || b.article || '';
                    return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
                });
            } else if (index === 1) {
                productsData.sort((a, b) => {
                    const valA = a.cost ?? 0;
                    const valB = b.cost ?? 0;
                    return sortAsc ? valA - valB : valB - valA;
                });
            }
            sortAsc = !sortAsc;
            renderProducts(productsData);
        });
    });
});
