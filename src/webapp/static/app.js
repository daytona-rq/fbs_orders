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
            if (!response.ok) throw new Error(`Ошибка загрузки: ${response.status}`);
            
            productsData = await response.json();
            if (productsData.length === 0) renderEmptyMessage();
            else renderProducts(productsData);
        } catch (error) {
            console.error('Ошибка:', error);
            tg.showAlert(error.message);
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
                <td>${product.article_code || 'N/A'}</td>
                <td>
                    <input type="number" 
                           step="0.01" 
                           value="${(product.cost ?? 0).toFixed(2)}" 
                           data-id="${product.id}"
                           onchange="handleCostChange(event)"
                           onblur="handleInputBlur(event)">
                </td>
            </tr>
        `).join('');
    }

    function flashInput(input, className) {
        input.classList.add(className);
        setTimeout(() => input.classList.remove(className), 1500);
    }

    window.handleInputBlur = function(event) {
        const input = event.target;
        let value = parseFloat(input.value.replace(',', '.'));
        
        if (isNaN(value)) {
            value = 0;
        } else if (value < 0) {
            value = 0;
        }
        
        input.value = value.toFixed(2);
    };

    window.handleCostChange = async function(event) {
        const input = event.target;
        const articleId = input.dataset.id;
        let value = parseFloat(input.value.replace(',', '.'));
        
        if (isNaN(value)) {
            value = 0;
        } else if (value < 0) {
            value = 0;
        }
        
        const formattedValue = parseFloat(value.toFixed(2));
        input.value = formattedValue.toFixed(2);

        try {
            const response = await fetch(`/api/articles/${articleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({cost: formattedValue})
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Ошибка сервера");
            }
            
            const updatedProduct = await response.json();
            input.value = updatedProduct.cost.toFixed(2);
            flashInput(input, 'updated');
        } catch (error) {
            console.error('Ошибка обновления:', error);
            const product = productsData.find(p => p.id == articleId);
            input.value = (product?.cost ?? 0).toFixed(2);
            flashInput(input, 'error');
            tg.showAlert(`Ошибка: ${error.message}`);
        }
    };

    window.searchProducts = searchProducts;
});