/**
 * DOM and UI utilities
 */

/**
 * Show status message with auto-clear on success
 */
function showStatus(element, message, isError = false) {
    element.innerText = message;
    element.className = isError ? 'status error' : 'status success';
    
    if (!isError) {
        setTimeout(() => {
            element.className = 'status';
        }, 3000);
    }
}

/**
 * Set loading state on button
 */
function setButtonLoading(button, isLoading = true) {
    button.disabled = isLoading;
    if (isLoading) {
        button.classList.add('loading');
    } else {
        button.classList.remove('loading');
    }
}

/**
 * Show user info in metadata element
 */
function displayUserInfo(element, userProfile, telegramUser = null) {
    if (!element) return;
    
    let userInfo = userProfile || telegramUser;
    
    if (userInfo) {
        if (userInfo.username && userInfo.role) {
            element.innerText = `👤 ${userInfo.username} (${userInfo.role})`;
        } else if (userInfo.loginParam && userInfo.value) {
            element.innerText = `👤 ${userInfo.loginParam}: ${userInfo.value}`;
        } else {
            element.innerText = `👤 ${userInfo.first_name || ''} ${userInfo.last_name || ''} (@${userInfo.username || ''})`;
        }
    } else {
        element.innerText = "Not logged in";
    }
}

/**
 * Convert data URL to Blob
 */
function dataURLToBlob(dataUrl) {
    const arr = dataUrl.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new Blob([u8arr], { type: mime });
}

/**
 * Create preview item wrapper with image, remove button, and label
 */
function createPreviewItem(dataUrl, name, index, size, onRemove) {
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    wrapper.style.display = 'inline-block';
    wrapper.style.marginRight = '8px';

    const img = document.createElement('img');
    img.src = dataUrl;
    img.alt = name || 'file';
    img.style.width = '80px';
    img.style.height = '80px';
    img.style.objectFit = 'cover';
    img.style.borderRadius = '8px';
    img.style.border = '1px solid #e2e8f0';
    wrapper.appendChild(img);

    const removeBtn = document.createElement('button');
    removeBtn.innerText = '✖';
    removeBtn.title = 'Remove file';
    removeBtn.style.position = 'absolute';
    removeBtn.style.top = '4px';
    removeBtn.style.right = '4px';
    removeBtn.style.background = 'rgba(0,0,0,0.6)';
    removeBtn.style.color = 'white';
    removeBtn.style.border = 'none';
    removeBtn.style.borderRadius = '50%';
    removeBtn.style.width = '22px';
    removeBtn.style.height = '22px';
    removeBtn.style.cursor = 'pointer';
    removeBtn.style.fontSize = '14px';
    removeBtn.style.padding = '0';
    removeBtn.addEventListener('click', () => onRemove(index));
    wrapper.appendChild(removeBtn);

    const label = document.createElement('div');
    label.style.fontSize = '11px';
    label.style.color = '#444';
    label.style.textAlign = 'center';
    label.style.marginTop = '4px';
    label.style.maxWidth = '80px';
    label.style.overflow = 'hidden';
    label.style.textOverflow = 'ellipsis';
    label.style.whiteSpace = 'nowrap';
    label.innerText = name + (size ? ` (${Math.round(size / 1024)} KB)` : '');
    wrapper.appendChild(label);

    return wrapper;
}

/**
 * Clear all children from an element
 */
function clearElement(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

/**
 * Reset form to initial state
 */
function resetForm(titleInput, quillEditor, fileInput, previewElement) {
    if (titleInput) titleInput.value = '';
    if (quillEditor) quillEditor.setContents([]);
    if (fileInput) fileInput.value = '';
    if (previewElement) clearElement(previewElement);
}

/**
 * Format date string (DD-MM-YYYY to readable format)
 */
function formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    const [day, month, year] = parts;
    const date = new Date(`${year}-${month}-${day}`);
    return date.toLocaleDateString('en-US', { 
        weekday: 'short', 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

/**
 * Sort dates in descending order (newest first)
 */
function sortDatesByRecent(dateStrings) {
    return dateStrings.sort((a, b) => {
        const dateA = new Date(a.split('-').reverse().join('-'));
        const dateB = new Date(b.split('-').reverse().join('-'));
        return dateB - dateA;
    });
}

/**
 * Truncate HTML text to specified length
 */
function truncateText(htmlText, maxLength = 100) {
    const plainText = htmlText.replace(/<[^>]*>/g, '');
    if (plainText.length > maxLength) {
        return plainText.substring(0, maxLength) + '...';
    }
    return plainText;
}
