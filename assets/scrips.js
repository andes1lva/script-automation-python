document.addEventListener('DOMContentLoaded', () => {
    console.log('Scraper Pro v8.0 carregado com sucesso!');

    const textarea = document.getElementById('urls');
    const status = document.getElementById('status');
    const loading = document.getElementById('loading');
    const btnDownload = document.getElementById('download');

    // Garante que o botão existe
    if (!btnDownload) {
        console.error('Botão #download não encontrado!');
        return;
    }

    btnDownload.addEventListener('click', () => {
        console.log('Botão DOWNLOAD clicado!');

        const urls = textarea.value.trim();
        if (!urls) {
            showStatus('Adicione pelo menos uma URL!', 'error');
            console.warn('Campo de URLs vazio.');
            return;
        }

        loading.style.display = 'block';
        showStatus('Gerando urls.txt...', 'success');

        // DOWNLOAD GARANTIDO
        setTimeout(() => {
            const blob = new Blob([urls], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'urls.txt';
            a.style.display = 'none';
            document.body.appendChild(a);

            // Força o clique
            a.click();

            // Limpeza
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                console.log('urls.txt baixado com sucesso!');
            }, 100);

            // ABRE A PASTA
            setTimeout(() => {
                loading.style.display = 'none';
                showStatus('urls.txt baixado! Pasta aberta.', 'success');
                const folderPath = location.pathname.replace(/[^/]+$/, '');
                window.open('file:///' + folderPath, '_blank');
            }, 800);
        }, 600);
    });

    function showStatus(msg, type) {
        status.textContent = msg;
        status.className = `status-neon ${type}`;
        status.style.display = 'block';
        setTimeout(() => status.style.display = 'none', 5000);
        console.log('Status:', msg);
    }

    console.log('Botão DOWNLOAD pronto!');
});