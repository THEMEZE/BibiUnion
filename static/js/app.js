/* ============================================
   APPLICATION JS - Mariage
   Gère : upload AJAX, galerie dynamique, lightbox,
   diaporama, administration
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('upload-form')) {
        initUploadPage();
    }
    if (document.getElementById('gallery-grid')) {
        initGalleryPage();
    }
    if (document.querySelector('.admin-container')) {
        initAdminPage();
    }
});

/* ============================================
   PAGE UPLOAD
   ============================================ */
function initUploadPage() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    const submitBtn = document.getElementById('submit-btn');
    const form = document.getElementById('upload-form');
    const summary = document.getElementById('upload-summary');
    const summaryText = document.getElementById('summary-text');
    const addMoreBtn = document.getElementById('add-more-btn');

    let selectedFiles = [];

    // Drag & drop
    ['dragenter', 'dragover'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/') || f.name.toLowerCase().endsWith('.heic'));
        addFiles(files);
    });

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        addFiles(files);
        fileInput.value = ''; // permet de re-sélectionner les mêmes fichiers
    });

    function addFiles(files) {
        files.forEach(file => {
            const id = 'file_' + Math.random().toString(36).substr(2, 9);
            selectedFiles.push({ id, file, status: 'pending' });
            renderPreview(id, file);
        });
        updateSubmitState();
    }

    function renderPreview(id, file) {
        const item = document.createElement('div');
        item.className = 'preview-item';
        item.dataset.id = id;

        const img = document.createElement('img');
        item.appendChild(img);

        // HEIC ne s'affiche pas nativement dans <img> -> icône générique
        if (file.type.startsWith('image/') && !file.name.toLowerCase().endsWith('.heic')) {
            const reader = new FileReader();
            reader.onload = (e) => { img.src = e.target.result; };
            reader.readAsDataURL(file);
        } else {
            img.src = '';
            img.alt = '📷 HEIC';
            item.style.display = 'flex';
            item.style.alignItems = 'center';
            item.style.justifyContent = 'center';
            item.style.fontSize = '2rem';
            item.textContent = '📷';
        }

        const removeBtn = document.createElement('button');
        removeBtn.className = 'preview-remove';
        removeBtn.innerHTML = '&times;';
        removeBtn.type = 'button';
        removeBtn.addEventListener('click', () => removeFile(id));
        item.appendChild(removeBtn);

        const progressWrap = document.createElement('div');
        progressWrap.className = 'preview-progress';
        const progressBar = document.createElement('div');
        progressBar.className = 'preview-progress-bar';
        progressWrap.appendChild(progressBar);
        item.appendChild(progressWrap);

        previewContainer.appendChild(item);
    }

    function removeFile(id) {
        selectedFiles = selectedFiles.filter(f => f.id !== id);
        const el = previewContainer.querySelector(`[data-id="${id}"]`);
        if (el) el.remove();
        updateSubmitState();
    }

    function updateSubmitState() {
        const pendingFiles = selectedFiles.filter(f => f.status === 'pending' || f.status === 'error');
        submitBtn.disabled = pendingFiles.length === 0;
        submitBtn.textContent = pendingFiles.length > 0
            ? `Envoyer ${pendingFiles.length} photo(s)`
            : 'Envoyer les photos';
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const auteur = document.getElementById('auteur').value;
        const table = document.getElementById('table').value;
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

        const filesToUpload = selectedFiles.filter(f => f.status === 'pending' || f.status === 'error');

        if (filesToUpload.length === 0) return;

        submitBtn.disabled = true;
        submitBtn.textContent = 'Envoi en cours...';

        let completed = 0;
        let successCount = 0;

        filesToUpload.forEach(fileObj => {
            uploadFile(fileObj, auteur, table, csrfToken, () => {
                completed++;
                if (fileObj.status === 'success') successCount++;
                if (completed === filesToUpload.length) {
                    onAllUploadsComplete(successCount, filesToUpload.length);
                }
            });
        });
    });

    function uploadFile(fileObj, auteur, table, csrfToken, callback) {
        const formData = new FormData();
        formData.append('image', fileObj.file);
        formData.append('auteur', auteur);
        formData.append('table', table);

        const xhr = new XMLHttpRequest();
        const item = previewContainer.querySelector(`[data-id="${fileObj.id}"]`);
        const progressBar = item ? item.querySelector('.preview-progress-bar') : null;

        xhr.open('POST', window.UPLOAD_URL, true);
        xhr.setRequestHeader('X-CSRFToken', csrfToken);

        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable && progressBar) {
                const percent = (e.loaded / e.total) * 100;
                progressBar.style.width = percent + '%';
            }
        };

        xhr.onload = function () {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.success) {
                    fileObj.status = 'success';
                    markPreviewStatus(item, 'success', '✓');
                } else {
                    fileObj.status = 'error';
                    markPreviewStatus(item, 'error', '✗', response.error);
                }
            } else {
                fileObj.status = 'error';
                let errorMsg = "Erreur d'envoi";
                try {
                    const response = JSON.parse(xhr.responseText);
                    errorMsg = response.error || errorMsg;
                } catch (e) {}
                markPreviewStatus(item, 'error', '✗', errorMsg);
            }
            callback();
        };

        xhr.onerror = function () {
            fileObj.status = 'error';
            markPreviewStatus(item, 'error', '✗', 'Erreur réseau');
            callback();
        };

        xhr.send(formData);
    }

    function markPreviewStatus(item, status, icon, errorMsg) {
        if (!item) return;
        const statusEl = document.createElement('div');
        statusEl.className = `preview-status ${status}`;
        statusEl.textContent = icon;
        if (errorMsg) statusEl.title = errorMsg;
        item.appendChild(statusEl);
    }

    function onAllUploadsComplete(successCount, total) {
        form.style.display = 'none';
        summary.style.display = 'block';
        if (successCount === total) {
            summaryText.textContent = `${successCount} photo(s) envoyée(s) avec succès. Merci ! 💛`;
        } else {
            summaryText.textContent = `${successCount}/${total} photo(s) envoyée(s). Certaines ont échoué.`;
        }
    }

    addMoreBtn.addEventListener('click', () => {
        selectedFiles = [];
        previewContainer.innerHTML = '';
        form.style.display = 'block';
        summary.style.display = 'none';
        submitBtn.disabled = true;
        submitBtn.textContent = 'Envoyer les photos';
    });
}

/* ============================================
   PAGE GALERIE
   ============================================ */
function initGalleryPage() {
    const grid = document.getElementById('gallery-grid');
    const loader = document.getElementById('gallery-loader');
    const empty = document.getElementById('gallery-empty');
    const filterTable = document.getElementById('filter-table');
    const filterDate = document.getElementById('filter-date');
    const resetBtn = document.getElementById('reset-filters');
    const toggleSlideshow = document.getElementById('toggle-slideshow');

    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxCaption = document.getElementById('lightbox-caption');
    const lightboxClose = document.getElementById('lightbox-close');
    const lightboxPrev = document.getElementById('lightbox-prev');
    const lightboxNext = document.getElementById('lightbox-next');

    let currentPage = 1;
    let hasNext = true;
    let loading = false;
    let allPhotos = [];
    let lastPhotoId = 0;
    let currentLightboxIndex = 0;
    let slideshowInterval = null;
    let realtimeInterval = null;

    loadPhotos();

    // Scroll infini
    window.addEventListener('scroll', () => {
        if (loading || !hasNext) return;
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 300) {
            currentPage++;
            loadPhotos();
        }
    });

    filterTable.addEventListener('change', resetAndReload);
    filterDate.addEventListener('change', resetAndReload);
    resetBtn.addEventListener('click', () => {
        filterTable.value = '';
        filterDate.value = '';
        resetAndReload();
    });

    function resetAndReload() {
        currentPage = 1;
        hasNext = true;
        allPhotos = [];
        lastPhotoId = 0;
        grid.innerHTML = '';
        empty.style.display = 'none';
        loadPhotos();
    }

    function loadPhotos() {
        loading = true;
        loader.style.display = 'block';

        const params = new URLSearchParams({
            page: currentPage,
            table: filterTable.value,
            date: filterDate.value,
        });

        fetch(`${window.GALLERY_DATA_URL}?${params}`)
            .then(res => res.json())
            .then(data => {
                loader.style.display = 'none';
                loading = false;
                hasNext = data.has_next;

                if (data.photos.length === 0 && allPhotos.length === 0) {
                    empty.style.display = 'block';
                    return;
                }

                data.photos.forEach(photo => {
                    allPhotos.push(photo);
                    renderPhoto(photo);
                    if (photo.id > lastPhotoId) lastPhotoId = photo.id;
                });
            })
            .catch(() => {
                loader.style.display = 'none';
                loading = false;
            });
    }

    function renderPhoto(photo) {
        const item = document.createElement('div');
        item.className = 'gallery-item';
        item.dataset.id = photo.id;

        const img = document.createElement('img');
        img.src = photo.thumbnail_url;
        img.loading = 'lazy';
        img.alt = `Photo de ${photo.auteur}`;
        item.appendChild(img);

        const caption = document.createElement('div');
        caption.className = 'gallery-item-caption';
        caption.textContent = `${photo.auteur}${photo.table ? ' • ' + photo.table : ''}`;
        item.appendChild(caption);

        item.addEventListener('click', () => openLightbox(photo.id));

        grid.appendChild(item);
    }

    /* ---------- Temps réel : nouvelles photos ---------- */
    realtimeInterval = setInterval(() => {
        if (!lastPhotoId) return;
        const params = new URLSearchParams({
            since_id: lastPhotoId,
            table: filterTable.value,
            date: filterDate.value,
        });
        fetch(`${window.GALLERY_DATA_URL}?${params}`)
            .then(res => res.json())
            .then(data => {
                if (data.photos && data.photos.length > 0) {
                    // Ajoute les nouvelles photos en haut de la grille
                    data.photos.slice().reverse().forEach(photo => {
                        allPhotos.unshift(photo);
                        if (photo.id > lastPhotoId) lastPhotoId = photo.id;

                        const item = document.createElement('div');
                        item.className = 'gallery-item';
                        item.dataset.id = photo.id;

                        const img = document.createElement('img');
                        img.src = photo.thumbnail_url;
                        img.loading = 'lazy';
                        img.alt = `Photo de ${photo.auteur}`;
                        item.appendChild(img);

                        const caption = document.createElement('div');
                        caption.className = 'gallery-item-caption';
                        caption.textContent = `${photo.auteur}${photo.table ? ' • ' + photo.table : ''}`;
                        item.appendChild(caption);

                        item.addEventListener('click', () => openLightbox(photo.id));

                        grid.insertBefore(item, grid.firstChild);
                        empty.style.display = 'none';
                    });
                }
            })
            .catch(() => {});
    }, 15000); // toutes les 15 secondes

    /* ---------- Lightbox plein écran ---------- */
    function openLightbox(photoId) {
        currentLightboxIndex = allPhotos.findIndex(p => p.id === photoId);
        if (currentLightboxIndex === -1) return;
        showLightboxPhoto();
        lightbox.style.display = 'flex';
    }

    function showLightboxPhoto() {
        const photo = allPhotos[currentLightboxIndex];
        lightboxImg.src = photo.full_url;
        lightboxCaption.textContent = `${photo.auteur}${photo.table ? ' • ' + photo.table : ''} - ${photo.date_upload}`;
    }

    lightboxClose.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox();
    });

    function closeLightbox() {
        lightbox.style.display = 'none';
        stopSlideshow();
    }

    lightboxPrev.addEventListener('click', () => {
        currentLightboxIndex = (currentLightboxIndex - 1 + allPhotos.length) % allPhotos.length;
        showLightboxPhoto();
    });

    lightboxNext.addEventListener('click', () => {
        currentLightboxIndex = (currentLightboxIndex + 1) % allPhotos.length;
        showLightboxPhoto();
    });

    document.addEventListener('keydown', (e) => {
        if (lightbox.style.display === 'flex') {
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowLeft') lightboxPrev.click();
            if (e.key === 'ArrowRight') lightboxNext.click();
        }
    });

    /* ---------- Diaporama automatique ---------- */
    toggleSlideshow.addEventListener('change', () => {
        if (toggleSlideshow.checked) {
            startSlideshow();
        } else {
            stopSlideshow();
        }
    });

    function startSlideshow() {
        if (allPhotos.length === 0) return;
        currentLightboxIndex = 0;
        showLightboxPhoto();
        lightbox.style.display = 'flex';
        slideshowInterval = setInterval(() => {
            currentLightboxIndex = (currentLightboxIndex + 1) % allPhotos.length;
            showLightboxPhoto();
        }, 4000);
    }

    function stopSlideshow() {
        if (slideshowInterval) {
            clearInterval(slideshowInterval);
            slideshowInterval = null;
            toggleSlideshow.checked = false;
        }
    }
}

/* ============================================
   PAGE ADMINISTRATION
   ============================================ */
function initAdminPage() {
    const deleteButtons = document.querySelectorAll('.delete-btn');

    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const photoId = this.dataset.id;
            if (!confirm('Supprimer cette photo définitivement ?')) return;

            const url = `/admin-gallery/delete/${photoId}/`;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN,
                },
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        const card = document.querySelector(`.admin-card[data-id="${photoId}"]`);
                        if (card) card.remove();
                    } else {
                        alert('Erreur lors de la suppression.');
                    }
                })
                .catch(() => alert('Erreur réseau.'));
        });
    });
}
